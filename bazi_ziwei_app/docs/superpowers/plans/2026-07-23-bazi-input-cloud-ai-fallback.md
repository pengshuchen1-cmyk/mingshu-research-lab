# Bazi Input, Cloud AI, and Full Local Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make lunar birth input unambiguous and previewable, keep local “四柱八字分析规则” as the only source of chart facts, use cloud AI for detailed six-section conversations when available, and return a visibly degraded but complete local six-section answer when the cloud is unavailable.

**Architecture:** Add a pure birth-input preview module between the Streamlit form and `build_bazi_chart`, then make the page use a preview/confirm state machine whose chart fingerprint must remain stable. Keep `ChartFacts` as the normative AI boundary. Replace category-only question canonicalization with PII-redacted semantic context, require six structured answer sections from the cloud, validate them locally, and reuse the same answer contract for deterministic local fallback. Preserve the existing U01–U05 fixture and add a separate 1999 lunar regression fixture so the prior five-case acceptance chain remains intact.

**Tech Stack:** Python 3, Streamlit, Pydantic, `lunar_python`, OpenAI Responses API, pytest.

**Global Constraints:**

- Local `calculate_four_pillars` / `build_bazi_chart` remains the only authority for conversion, pillars, strength, pattern, wealth, relationship, and luck facts.
- Cloud AI never receives raw name, profile ID, exact birth date/time, birth place, longitude, API key, logs, or database IDs.
- Cloud AI may explain only supplied `ChartFacts` and rule evidence; one corrective retry is allowed.
- Automated tests never call the live OpenAI API; use fake clients and synthetic SDK-like exceptions.
- The 1999 acceptance value is `农历1999-07-01 10:00 → 公历1999-08-11 10:00 → 己卯/壬申/乙未/辛巳`.
- Keep the current public summary fields exactly: 时间模式、四柱计算依据、起运方向、起运时间、强弱证据、格局、财运、姻缘.

---

## Task 1: Add a pure birth-input preview contract

**Files:**

- Create: `core/birth_input_preview.py`
- Create: `tests/test_birth_input_preview.py`
- Modify: `utils/validators.py`

- [ ] **Step 1: Write failing tests for lunar conversion, receipt text, and fingerprint**

```python
# tests/test_birth_input_preview.py
from core.birth_input_preview import BirthFormInput, build_birth_preview


def test_1999_lunar_input_builds_expected_receipt_and_pillars():
    preview = build_birth_preview(
        BirthFormInput(
            name="访客",
            gender="男",
            calendar="lunar",
            year=1999,
            month=7,
            day=1,
            is_leap_month=False,
            hour=10,
            minute=0,
            time_label="巳时",
        )
    )

    assert preview.solar_datetime == "1999-08-11 10:00"
    assert preview.pillars == ("己卯", "壬申", "乙未", "辛巳")
    assert "农历1999年七月初一" in preview.input_text
    assert "非闰月" in preview.input_text
    assert preview.chart_fingerprint == preview.chart["chart_fingerprint_v2"]


def test_same_numeric_solar_date_is_explicitly_different():
    preview = build_birth_preview(
        BirthFormInput(
            name="访客",
            gender="男",
            calendar="solar",
            year=1999,
            month=7,
            day=1,
            hour=10,
            minute=0,
            time_label="精确时间",
        )
    )

    assert preview.input_text.startswith("公历1999年7月1日")
    assert preview.pillars != ("己卯", "壬申", "乙未", "辛巳")


def test_invalid_lunar_date_does_not_produce_a_preview():
    import pytest

    with pytest.raises(ValueError, match="农历日期"):
        build_birth_preview(
            BirthFormInput(
                name="访客",
                gender="女",
                calendar="lunar",
                year=1999,
                month=2,
                day=31,
                hour=10,
                minute=0,
            )
        )
```

- [ ] **Step 2: Run the new test and confirm it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_input_preview.py -q
```

Expected: FAIL because `core.birth_input_preview` does not exist.

- [ ] **Step 3: Implement immutable form and preview models**

```python
# core/birth_input_preview.py
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from core.bazi_engine import build_bazi_chart
from utils.validators import validate_profile


CHINESE_MONTHS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二")
CHINESE_DAYS = (
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
)


@dataclass(frozen=True)
class BirthFormInput:
    name: str
    gender: str
    calendar: Literal["solar", "lunar"]
    year: int
    month: int
    day: int
    hour: int | None
    minute: int | None
    is_leap_month: bool = False
    birth_place: str = ""
    time_label: str = "精确时间"

    def to_profile(self) -> dict:
        source_date = f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        profile = {
            "name": self.name.strip() or "访客",
            "gender": self.gender,
            "calendar_type": self.calendar,
            "birth_date": source_date,
            "birth_hour": self.hour,
            "birth_minute": self.minute,
            "birth_place": self.birth_place.strip(),
            "is_leap_month": bool(self.is_leap_month and self.calendar == "lunar"),
            "use_solar_time": False,
            "use_true_solar_time": False,
            "birth_longitude": None,
            "time_mode": "china_standard",
        }
        if self.calendar == "lunar":
            profile["lunar_birth_date"] = source_date
        return profile

    def fingerprint(self) -> str:
        payload = json.dumps(self.to_profile(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BirthPreview:
    profile: dict
    chart: dict
    input_text: str
    solar_datetime: str
    pillars: tuple[str, str, str, str]
    calculation_basis: str
    input_fingerprint: str
    chart_fingerprint: str


def _input_text(value: BirthFormInput) -> str:
    if value.calendar == "solar":
        prefix = f"公历{value.year}年{value.month}月{value.day}日"
    else:
        leap = "闰" if value.is_leap_month else ""
        prefix = (
            f"农历{value.year}年{leap}{CHINESE_MONTHS[value.month - 1]}月"
            f"{CHINESE_DAYS[value.day - 1]}"
        )
        prefix += "，闰月" if value.is_leap_month else "，非闰月"
    return f"{prefix}，{value.gender}，{value.time_label}"


def build_birth_preview(value: BirthFormInput) -> BirthPreview:
    profile = value.to_profile()
    ok, message = validate_profile(profile)
    if not ok:
        raise ValueError(message)
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        label = "农历日期" if value.calendar == "lunar" else "出生日期"
        raise ValueError(f"{label}无法转换：{chart['error']}")
    pillars = tuple(
        chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
    )
    time_text = (
        f"{value.hour:02d}:{value.minute:02d}"
        if value.hour is not None and value.minute is not None
        else "时辰不详"
    )
    return BirthPreview(
        profile=profile,
        chart=chart,
        input_text=_input_text(value),
        solar_datetime=f"{chart['profile']['birth_date']} {time_text}",
        pillars=pillars,
        calculation_basis=chart["pillar_evidence"]["public_text"],
        input_fingerprint=value.fingerprint(),
        chart_fingerprint=chart["chart_fingerprint_v2"],
    )
```

- [ ] **Step 4: Permit only paired unknown hour/minute values in validation**

Update `validate_profile` so `(None, None)` is valid, one missing component is invalid, and known values retain the 0–23 / 0–59 checks.

```python
hour_raw = profile.get("birth_hour")
minute_raw = profile.get("birth_minute")
if hour_raw is None and minute_raw is None:
    pass
elif hour_raw is None or minute_raw is None:
    return False, "出生小时和分钟需要同时填写。"
else:
    try:
        birth_hour = int(hour_raw)
        birth_minute = int(minute_raw)
    except (TypeError, ValueError):
        return False, "出生时间格式不正确。"
    if not 0 <= birth_hour <= 23:
        return False, "出生小时必须在 0-23 之间。"
    if not 0 <= birth_minute <= 59:
        return False, "出生分钟必须在 0-59 之间。"
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_input_preview.py tests/test_profile_form_calendar_type.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/birth_input_preview.py utils/validators.py tests/test_birth_input_preview.py
git commit -m "feat: add deterministic birth input preview"
```

---

## Task 2: Add traditional-hour mapping and boundary tests

**Files:**

- Modify: `core/birth_input_preview.py`
- Modify: `tests/test_birth_input_preview.py`

- [ ] **Step 1: Add failing tests for every traditional hour and split 子时**

```python
from core.birth_input_preview import traditional_time


def test_traditional_hour_uses_stable_representative_times():
    assert traditional_time("巳时") == (10, 0, "巳时")
    assert traditional_time("未时") == (14, 0, "未时")
    assert traditional_time("子时（23:00–23:59）") == (23, 30, "子时（23:00–23:59）")
    assert traditional_time("子时（00:00–00:59）") == (0, 30, "子时（00:00–00:59）")


def test_split_zi_hour_can_change_the_day_pillar():
    late = build_birth_preview(
        BirthFormInput("访客", "女", "solar", 1996, 9, 4, 23, 30, time_label="子时（23:00–23:59）")
    )
    early = build_birth_preview(
        BirthFormInput("访客", "女", "solar", 1996, 9, 4, 0, 30, time_label="子时（00:00–00:59）")
    )
    assert late.pillars[2] != early.pillars[2]
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_input_preview.py -q
```

Expected: FAIL because `traditional_time` is missing.

- [ ] **Step 3: Implement the explicit mapping**

```python
TRADITIONAL_TIMES = {
    "子时（23:00–23:59）": (23, 30),
    "子时（00:00–00:59）": (0, 30),
    "丑时": (2, 0),
    "寅时": (4, 0),
    "卯时": (6, 0),
    "辰时": (8, 0),
    "巳时": (10, 0),
    "午时": (12, 0),
    "未时": (14, 0),
    "申时": (16, 0),
    "酉时": (18, 0),
    "戌时": (20, 0),
    "亥时": (22, 0),
}


def traditional_time(label: str) -> tuple[int, int, str]:
    try:
        hour, minute = TRADITIONAL_TIMES[label]
    except KeyError as exc:
        raise ValueError("请选择有效的传统时辰。") from exc
    return hour, minute, label
```

- [ ] **Step 4: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_input_preview.py -q
```

Expected: PASS.

```bash
git add core/birth_input_preview.py tests/test_birth_input_preview.py
git commit -m "feat: support explicit traditional birth hours"
```

---

## Task 3: Replace ambiguous lunar date input with preview/confirm UI

**Files:**

- Modify: `ui/profile_form.py`
- Rewrite: `tests/test_profile_form_calendar_type.py`
- Modify: `tests/test_profile_form_steps.py`

- [ ] **Step 1: Write failing source and state-machine tests**

Tests must assert:

- calendar mode control is rendered outside `st.form`;
- solar mode uses a control labeled `公历出生日期`;
- lunar mode renders `农历年份`, `农历月份`, `农历日期`, `是否闰月`;
- lunar mode does not call `date_input` for the lunar date;
- time precision has `精确时间`, `传统时辰`, `时辰不详`;
- first submit is `校验并预览`;
- preview displays `原始输入`, `标准时间`, `四柱预览`, `计算依据`;
- second action is `确认生成命盘`;
- changing any birth field invalidates the saved preview;
- confirmation rebuilds the chart and rejects a changed chart fingerprint.

Use a fake Streamlit implementation rather than a browser for these unit tests. Patch `build_birth_preview` to return a deterministic preview.

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_profile_form_calendar_type.py tests/test_profile_form_steps.py -q
```

Expected: FAIL against the current one-submit date-picker form.

- [ ] **Step 3: Add preview state keys and input conversion helpers**

```python
PROFILE_PREVIEW_KEY = "profile_birth_preview"
PROFILE_PREVIEW_INPUT_KEY = "profile_birth_preview_input"


def _clear_birth_preview(state) -> None:
    state.pop(PROFILE_PREVIEW_KEY, None)
    state.pop(PROFILE_PREVIEW_INPUT_KEY, None)
```

Keep `_build_profile_payload` as a compatibility wrapper for existing callers, but route all new UI submissions through `BirthFormInput`.

- [ ] **Step 4: Move calendar mode outside the form**

Render:

```python
calendar_label = st.radio(
    "出生日期类型",
    ["公历", "农历"],
    key="profile_calendar_label",
    horizontal=True,
)
```

Then render mode-specific controls inside the single data-entry form:

```python
if calendar_label == "公历":
    solar_date = st.date_input(
        "公历出生日期",
        value=draft.get("birth_date", date(1990, 1, 1)),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
    )
else:
    lunar_year = st.selectbox(
        "农历年份",
        list(range(1900, date.today().year + 1)),
        index=int(draft.get("lunar_year", 1990)) - 1900,
    )
    lunar_month = st.selectbox(
        "农历月份",
        list(range(1, 13)),
        index=int(draft.get("lunar_month", 1)) - 1,
        format_func=lambda value: f"{CHINESE_MONTHS[value - 1]}月",
    )
    lunar_day = st.selectbox(
        "农历日期",
        list(range(1, 31)),
        index=int(draft.get("lunar_day", 1)) - 1,
        format_func=lambda value: CHINESE_DAYS[value - 1],
    )
    is_leap_month = st.checkbox(
        "是否闰月",
        value=bool(draft.get("is_leap_month", False)),
    )
```

Render time precision and map traditional times with `traditional_time`. For unknown time pass `(None, None)` and visibly state that the hour pillar and time-specific conclusions will be limited.

- [ ] **Step 5: Implement two-step generation**

On `校验并预览`:

1. construct `BirthFormInput`;
2. call `build_birth_preview`;
3. store only the preview profile, input fingerprint, chart fingerprint, and display fields in session state;
4. show no confirmation button when conversion fails.

On `确认生成命盘`:

1. reconstruct the current `BirthFormInput`;
2. require its fingerprint to equal the preview input fingerprint;
3. call `build_birth_preview` again;
4. require the rebuilt chart fingerprint to equal the preview chart fingerprint;
5. only then store `current_profile`, `current_chart`, and `current_report`.

Render the receipt exactly as:

```text
原始输入：农历1999年七月初一，非闰月，男，巳时
标准时间：中国标准时间 1999-08-11 10:00
四柱预览：己卯 / 壬申 / 乙未 / 辛巳
计算依据：<本地规则证据>
```

- [ ] **Step 6: Update public privacy consent**

Keep consent required before preview. Replace the old local-only wording with:

```text
出生资料只用于本地排盘，不上传云端。进入 AI 问答后，去身份化命盘事实、问题和近期对话会发送给已配置的云端 AI 服务；30 分钟无操作后清除本次会话。
```

- [ ] **Step 7: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_birth_input_preview.py tests/test_profile_form_calendar_type.py tests/test_profile_form_steps.py -q
```

Expected: PASS.

```bash
git add ui/profile_form.py tests/test_profile_form_calendar_type.py tests/test_profile_form_steps.py
git commit -m "feat: add unambiguous lunar preview flow"
```

---

## Task 4: Define one six-section answer contract for cloud and local output

**Files:**

- Modify: `core/ai_models.py`
- Create: `core/ai_answer_format.py`
- Create: `tests/test_ai_answer_format.py`
- Modify: `tests/test_ai_answer_guard.py`

- [ ] **Step 1: Write failing schema and formatter tests**

```python
from core.ai_answer_format import render_structured_answer
from core.ai_models import BaziAIAnswer


def test_structured_answer_always_renders_six_sections():
    answer = BaziAIAnswer(
        analysis_conclusion="财务发展应先看承载能力。",
        chart_evidence=["日主为乙，强弱结论为身弱。"],
        rule_evidence=["承财能力需结合日主强弱。"],
        timing_conditions=["遇到支持日主的阶段再观察机会。"],
        practical_advice=["先验证现金流，避免高杠杆。"],
        uncertainty_limitations=["命理趋势不能保证现实收益。"],
    )

    rendered = render_structured_answer(answer)

    assert list(rendered) == [
        "分析结论",
        "命盘依据",
        "规则依据",
        "阶段与触发条件",
        "现实建议",
        "不确定性与限制",
    ]
    assert all(rendered.values())
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_answer_format.py tests/test_ai_answer_guard.py -q
```

Expected: FAIL because the six-section schema does not exist.

- [ ] **Step 3: Replace the cloud response model**

```python
class BaziAIAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    analysis_conclusion: str = Field(min_length=1, max_length=3000)
    chart_evidence: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1, max_length=12)
    rule_evidence: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1, max_length=12)
    timing_conditions: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1, max_length=12)
    practical_advice: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1, max_length=12)
    uncertainty_limitations: list[Annotated[str, Field(min_length=1)]] = Field(min_length=1, max_length=8)
```

Extend `AnswerResult`:

```python
DegradationReason = Literal[
    "missing_api_key",
    "insufficient_quota",
    "invalid_credentials",
    "rate_limited",
    "network_error",
    "timeout",
    "service_unavailable",
    "unparseable_response",
    "local_validation_failed",
]


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sections: dict[str, str]
    chart_evidence: tuple[str, ...]
    rule_evidence: tuple[str, ...]
    timing_conditions: tuple[str, ...]
    practical_advice: tuple[str, ...]
    uncertainty: tuple[str, ...]
    source: Literal["cloud_validated", "local_rules"]
    degraded_reason: DegradationReason | None = None
```

- [ ] **Step 4: Add one deterministic formatter**

`render_structured_answer()` returns the six Chinese keys and `render_structured_markdown()` joins them with `###` headings. The guard must inspect all six fields, not only the old `answer`, `uncertainty`, and `cautions` fields.

- [ ] **Step 5: Update answer-guard fixtures and run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_answer_format.py tests/test_ai_answer_guard.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/ai_models.py core/ai_answer_format.py tests/test_ai_answer_format.py tests/test_ai_answer_guard.py
git commit -m "refactor: require six-section bazi answers"
```

---

## Task 5: Preserve specific semantics while redacting PII

**Files:**

- Modify: `core/ai_context.py`
- Modify: `tests/test_ai_context.py`
- Modify: `tests/test_ai_context_privacy.py`

- [ ] **Step 1: Write failing tests for useful detail and real follow-up context**

```python
def test_specific_question_survives_privacy_redaction():
    context = build_ai_context(
        facts,
        "姓名：金丝雀，生日1996-09-04 23:45，我想在2026年抵押房子做AI创业，现金流要注意什么？",
        [],
    )
    assert "金丝雀" not in context.question
    assert "1996-09-04" not in context.question
    assert "23:45" not in context.question
    for useful in ("2026年", "抵押房子", "AI创业", "现金流"):
        assert useful in context.question


def test_recent_follow_up_keeps_deidentified_semantics():
    context = build_ai_context(
        facts,
        "那姻缘方面呢？",
        [
            {"role": "user", "content": "我更关心2027年的事业转换"},
            {"role": "assistant", "content": "前一轮讨论了事业转换的条件和现金流。"},
        ],
    )
    assert "2027年的事业转换" in context.history[0].content
    assert "现金流" in context.history[1].content
```

- [ ] **Step 2: Run and confirm current canonicalization loses detail**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_context.py tests/test_ai_context_privacy.py -q
```

Expected: FAIL on preserved semantics.

- [ ] **Step 3: Implement bounded PII redaction**

Add `redact_customer_text(text: str) -> str` that:

- removes labeled names, phone numbers, emails, profile IDs, exact `YYYY-MM-DD`, Chinese birth dates, exact clock times, birth/residence cities, and longitude;
- removes birth-year shorthand before retaining forecast years;
- replaces removed spans with a neutral marker rather than exposing raw values;
- keeps industry, financial action, relationship topic, month/year target, and causal wording;
- truncates each message to 4,000 characters and total history to 6,000 characters;
- caps history at six messages.

Set:

```python
question=redact_customer_text(question)
```

and build history from actual redacted content rather than category labels.

- [ ] **Step 4: Keep full normative facts relevant to the question**

Always include pillars, gender, day master, hidden stems, ten gods, element counts, strength, pattern, wealth, relationship, and dayun. Include current context and explicit target-year pillars for timing questions. Continue selecting relevant local rules and never include `internal_rule_version`.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_context.py tests/test_ai_context_privacy.py -q
```

Expected: PASS.

```bash
git add core/ai_context.py tests/test_ai_context.py tests/test_ai_context_privacy.py
git commit -m "feat: preserve deidentified ai conversation detail"
```

---

## Task 6: Classify cloud errors and require the six-section prompt

**Files:**

- Modify: `services/openai_bazi_client.py`
- Modify: `tests/test_openai_bazi_client.py`

- [ ] **Step 1: Write failing error-classification tests**

Create lightweight exceptions with `status_code`, `code`, and message attributes. Assert:

| Simulated condition | Expected code |
|---|---|
| 401 / 403 | `invalid_credentials` |
| 429 plus `insufficient_quota` or billing marker | `insufficient_quota` |
| other 429 | `rate_limited` |
| `TimeoutError` | `timeout` |
| connection exception | `network_error` |
| 500 / 502 / 503 | `service_unavailable` |
| invalid parsed object | `unparseable_response` |

Also assert the system prompt includes all six section names, says not to recalculate pillars, and requests only supplied evidence.

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_openai_bazi_client.py -q
```

Expected: FAIL because most exceptions are currently collapsed to `service_error`.

- [ ] **Step 3: Implement deterministic classification**

```python
def classify_service_error(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    status = getattr(exc, "status_code", None)
    code = str(getattr(exc, "code", "") or "").lower()
    text = f"{code} {exc}".lower()
    if status in {401, 403}:
        return "invalid_credentials"
    if status == 429 and any(token in text for token in ("insufficient_quota", "billing", "quota")):
        return "insufficient_quota"
    if status == 429:
        return "rate_limited"
    if status in {500, 502, 503, 504}:
        return "service_unavailable"
    if isinstance(exc, (ConnectionError, OSError)) or "connection" in type(exc).__name__.lower():
        return "network_error"
    return "service_unavailable"
```

Keep `ValidationError` and missing `output_parsed` mapped to `unparseable_response`.

- [ ] **Step 4: Update the cloud instruction**

Require the six fields, specific chart citations, timing conditions, realistic suggestions, explicit limitations, no raw birth-data inference, and no recalculation. Keep `store=False`.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_openai_bazi_client.py -q
```

Expected: PASS.

```bash
git add services/openai_bazi_client.py tests/test_openai_bazi_client.py
git commit -m "feat: classify bazi ai service failures"
```

---

## Task 7: Build complete local answers and wire degradation reasons

**Files:**

- Create: `core/local_bazi_answer.py`
- Modify: `core/ai_orchestrator.py`
- Modify: `tests/test_ai_orchestrator.py`
- Create: `tests/test_local_bazi_answer.py`

- [ ] **Step 1: Write failing local-answer tests**

For overview, wealth, career, relationship, family, and timing questions assert:

- all six sections are non-empty;
- answer cites current pillars/day master/strength/pattern where relevant;
- wealth uses `facts.wealth` and wealth evidence;
- relationship current-status question says it cannot confirm whether the person is married;
- mortgage/borrowing question does not guarantee results and gives cash-flow/downside advice;
- timing answers use supplied dayun/current/target-year facts only.

- [ ] **Step 2: Write failing orchestration reason tests**

Assert:

```python
result = answer_question(chart, "财运如何？", [], config=AIConfig("", False))
assert result.source == "local_rules"
assert result.degraded_reason == "missing_api_key"
assert list(result.sections) == SIX_SECTION_TITLES
```

Parametrize fake service errors for every code. Assert a malformed response retries once, then returns `unparseable_response`; two guard failures return `local_validation_failed`.

- [ ] **Step 3: Run and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_local_bazi_answer.py tests/test_ai_orchestrator.py -q
```

Expected: FAIL because local fallback is currently one paragraph and has no reason.

- [ ] **Step 4: Implement the local builder using the same model**

`build_local_answer(context: AIRequestContext) -> BaziAIAnswer` must combine:

- category-specific conclusion from `ChartFacts`;
- concrete evidence already present in `context.chart_facts`;
- mapped rule statements from `context.rule_evidence`;
- dayun/current/target-year facts when supplied;
- category-specific realistic suggestions;
- explicit limitations.

Do not create a second set of astrological calculations.

- [ ] **Step 5: Update orchestration**

Use:

```python
if not config.enabled:
    return _local_result(context, "missing_api_key")
```

For cloud:

- retry once only for `unparseable_response` or local guard violations;
- return immediate local fallback for quota/auth/rate/network/timeout/service failures;
- after the second malformed output use `unparseable_response`;
- after the second guard rejection use `local_validation_failed`;
- preserve the exact `AIServiceError.code`;
- convert accepted cloud output with the shared formatter and `degraded_reason=None`.

- [ ] **Step 6: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_local_bazi_answer.py tests/test_ai_orchestrator.py tests/test_ai_answer_guard.py -q
```

Expected: PASS.

```bash
git add core/local_bazi_answer.py core/ai_orchestrator.py tests/test_local_bazi_answer.py tests/test_ai_orchestrator.py
git commit -m "feat: add complete local bazi answer fallback"
```

---

## Task 8: Render six sections, source labels, and visible service warnings

**Files:**

- Modify: `ui/inquiry_page.py`
- Modify: `core/ai_session.py`
- Modify: `ui/privacy_center_page.py`
- Modify: `tests/test_inquiry_chat_page.py`
- Modify: `tests/test_inquiry_chat_source_contract.py`

- [ ] **Step 1: Write failing source-label and warning tests**

Expected labels:

```python
assert answer_source_label("cloud_validated", None) == "云端 AI 分析 · 本地规则校验"
assert answer_source_label("local_rules", "missing_api_key") == "本地完整分析 · 云端服务未配置"
assert answer_source_label("local_rules", "insufficient_quota") == "本地完整分析 · 云端额度不足"
assert answer_source_label("local_rules", "network_error") == "本地完整分析 · 网络或服务异常"
assert answer_source_label("local_rules", "local_validation_failed") == "本地完整分析 · 云端回答校验未通过"
```

Assert the visible warnings contain:

- no key: `未配置 AI 服务`;
- quota: `余额或额度不足`;
- auth: `API Key 无效或无权限`;
- rate/network/timeout/service: `网络或 AI 服务出现短暂异常`;
- local validation: `未通过本地四柱规则校验`;
- every warning: `当前已切换为本地四柱规则完整分析`.

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_inquiry_chat_page.py tests/test_inquiry_chat_source_contract.py -q
```

Expected: FAIL against the current two generic labels.

- [ ] **Step 3: Persist structured details and degradation reason**

Extend `DETAIL_KEYS` with:

```python
("sections", "timing_conditions", "practical_advice", "degraded_reason")
```

Handle `sections` as a fixed allowlisted dictionary and `degraded_reason` as a fixed allowlisted string. Never store arbitrary exception text.

- [ ] **Step 4: Render visible degradation banners**

When a local result has `degraded_reason`, show the matching `st.warning` above its answer. Render the six sections directly in the chat response and keep the evidence expander only for any additional machine-verification details.

Log `reason_code=result.degraded_reason`, never the question, answer, raw exception, birth data, or API key.

- [ ] **Step 5: Update privacy-center wording**

State:

```text
出生资料和排盘计算保留在本次会话；AI 问答会把去身份化命盘事实、问题和近期对话发送给已配置的云端 AI 服务。不会发送姓名、精确出生日期、出生地点或 API Key。
```

- [ ] **Step 6: Run tests and commit**

Run:

```bash
.venv/bin/python -m pytest tests/test_inquiry_chat_page.py tests/test_inquiry_chat_source_contract.py tests/test_ai_session.py tests/test_ai_logging.py -q
```

Expected: PASS.

```bash
git add ui/inquiry_page.py core/ai_session.py ui/privacy_center_page.py tests/test_inquiry_chat_page.py tests/test_inquiry_chat_source_contract.py
git commit -m "feat: show structured ai answers and fallback status"
```

---

## Task 9: Add the 1999 case without rewriting the existing five-case chain

**Files:**

- Create: `tests/fixtures/lunar_1999_bazi_case.json`
- Create: `tests/test_lunar_1999_acceptance.py`
- Create: `scripts/render_lunar_1999_acceptance.py`
- Create: `acceptance_samples/lunar_1999_input_ai_acceptance.md`
- Modify: `scripts/run_user_five_ai_acceptance.py`
- Modify: `tests/test_user_five_ai_acceptance.py`

- [ ] **Step 1: Add the independent regression fixture**

```json
{
  "id": "L1999",
  "calendar": "lunar",
  "date": "1999-07-01",
  "time": "10:00",
  "time_label": "巳时",
  "is_leap_month": false,
  "gender": "male",
  "expected_solar_date": "1999-08-11",
  "expected_pillars": ["己卯", "壬申", "乙未", "辛巳"]
}
```

- [ ] **Step 2: Write failing end-to-end acceptance tests**

Test the fixture through:

1. `BirthFormInput`;
2. `build_birth_preview`;
3. formal `build_bazi_chart`;
4. chart fingerprint equality;
5. cloud request context;
6. accepted fake cloud six-section answer;
7. no-key local six-section answer;
8. privacy serialization.

Also assert original `user_five_bazi_cases.json` still contains exactly U01–U05 and all five continue to pass.

- [ ] **Step 3: Update deterministic acceptance client**

Make `DeterministicAcceptanceClient` return the new `BaziAIAnswer` six-section schema. Keep live mode explicit and keep automated runs offline.

- [ ] **Step 4: Create a human-readable 1999 receipt**

`render_lunar_1999_acceptance.py` must emit:

```text
# 1999 农历命例·输入与问答验收

原始输入：农历1999年七月初一，非闰月，男，巳时
标准时间：中国标准时间 1999-08-11 10:00
四柱预览：己卯 / 壬申 / 乙未 / 辛巳
预览与正式命盘：一致
云端结构化模拟：通过
本地完整降级：通过
隐私边界：通过
```

- [ ] **Step 5: Run six-case acceptance**

Run:

```bash
.venv/bin/python -m pytest tests/test_user_five_bazi_acceptance.py tests/test_user_five_ai_acceptance.py tests/test_lunar_1999_acceptance.py -q
.venv/bin/python scripts/render_user_five_bazi_acceptance.py
.venv/bin/python scripts/run_user_five_ai_acceptance.py
.venv/bin/python scripts/render_lunar_1999_acceptance.py
```

Expected: all tests PASS and all three acceptance samples regenerate deterministically.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/lunar_1999_bazi_case.json tests/test_lunar_1999_acceptance.py scripts/render_lunar_1999_acceptance.py acceptance_samples/lunar_1999_input_ai_acceptance.md scripts/run_user_five_ai_acceptance.py tests/test_user_five_ai_acceptance.py acceptance_samples/user_five_ai_acceptance.md
git commit -m "test: add 1999 lunar input and ai acceptance"
```

---

## Task 10: Run complete regression and live browser verification

**Files:**

- Modify only if a failing test exposes an in-scope defect.

- [ ] **Step 1: Run all targeted contracts**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_birth_input_preview.py \
  tests/test_profile_form_calendar_type.py \
  tests/test_profile_form_steps.py \
  tests/test_ai_context.py \
  tests/test_ai_context_privacy.py \
  tests/test_openai_bazi_client.py \
  tests/test_ai_answer_guard.py \
  tests/test_ai_answer_format.py \
  tests/test_local_bazi_answer.py \
  tests/test_ai_orchestrator.py \
  tests/test_inquiry_chat_page.py \
  tests/test_inquiry_chat_source_contract.py \
  tests/test_lunar_1999_acceptance.py \
  tests/test_user_five_bazi_acceptance.py \
  tests/test_user_five_ai_acceptance.py -q
```

Expected: PASS.

- [ ] **Step 2: Run the full suite**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: all tests PASS; no existing U01–U05, privacy, source-contract, report, or navigation regression.

- [ ] **Step 3: Start the app without an API key and verify fallback**

Run:

```bash
env -u OPENAI_API_KEY .venv/bin/python -m streamlit run app.py --server.port 8502
```

In the browser:

1. choose 农历;
2. enter 1999 / 七月 / 初一 / 非闰月 / 男 / 传统时辰 / 巳时;
3. click 校验并预览;
4. verify receipt is `1999-08-11 10:00` and `己卯 / 壬申 / 乙未 / 辛巳`;
5. confirm generation and verify the same pillars;
6. ask a wealth/career question and a follow-up;
7. verify six sections and the visible “未配置 AI 服务” fallback warning;
8. verify browser console and Streamlit logs have no errors or PII.

- [ ] **Step 4: Verify cloud mode with a fake service in tests**

Do not spend user API balance as part of automated verification. Confirm fake cloud tests cover:

- specific question and follow-up preservation;
- six structured sections;
- local fact guard;
- quota/auth/rate/network/timeout/service classifications;
- one malformed/guard corrective retry;
- correct source and degradation labels.

If the user later explicitly requests a live paid call, run the acceptance script with `--live` and inspect the generated timestamped artifact.

- [ ] **Step 5: Check working tree and commit any final in-scope fixes**

Run:

```bash
git status --short
git diff --check
git log --oneline -12
```

Expected: no unintended files, no whitespace errors, and task commits in dependency order.
