# Rule-Driven Bazi Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Check off each step only after its stated test passes.

**Goal:** Make the project-local 四柱八字 rule engine the single normative source for chart calculation and interpretation, keep `lunar_python` only as a calendar/solar-term adapter, replace saved chart data, and validate the result with the five user-supplied charts.

**Architecture:** Input normalization feeds an explicit four-pillar engine, which produces one immutable `ChartFacts` contract. Dayun, strength, pattern, wealth, relationship, reports, and later AI context consume that contract only. Rule provenance lives in versioned project JSON; the internal version remains machine-visible but is never shown in customer-facing summaries.

**Tech Stack:** Python 3, Streamlit, SQLite, JSON, `lunar_python`, pytest-compatible unittest tests.

**Global constraints:**

- `lunar_python` may provide Gregorian/lunar conversion, exact Jie timestamps, and the day-pillar seed. It must not decide strength, pattern, wealth, relationship, favorable elements, luck meaning, or narrative text.
- Civil time is China Standard Time unless a future profile explicitly supplies a supported location/time mode. Do not silently apply true-solar-time correction.
- Year changes at 立春; month changes at the 12 节; 23:00 starts the next bazi day; hour stem uses 五鼠遁.
- Customer summaries show only 时间模式、四柱计算依据、起运方向、起运时间、强弱证据、格局、财运、姻缘. They do not show 算法版本 or 调候依据.
- Delete incompatible saved profiles/charts after one recoverable database-file backup. Do not reinterpret old rows.
- The five supplied charts are release acceptance samples; existing algorithm boundary tests remain required engineering safeguards.

---

## Task 1: Install the project-local rulebook contract

**Files:**

- Create: `rules/bazi_skill/manifest.json`
- Create: `rules/bazi_skill/foundations.json`
- Create: `rules/bazi_skill/classical_rules.json`
- Create: `core/bazi_rulebook.py`
- Create: `tests/test_bazi_rulebook.py`

### Step 1: Write the failing contract tests

Test that `load_rulebook()` returns a frozen object containing all required sections, rejects duplicate rule IDs, rejects an unknown citation key, and exposes an internal semantic version without putting that version in `public_basis()`.

```python
from core.bazi_rulebook import load_rulebook


def test_rulebook_has_single_normative_sections():
    book = load_rulebook()
    assert set(book.sections) == {
        "calendar", "pillars", "dayun", "strength", "pattern",
        "wealth", "relationship", "safety",
    }
    assert book.version
    assert "version" not in book.public_basis()
```

Run: `.venv/bin/python -m pytest tests/test_bazi_rulebook.py -q`

Expected: FAIL because `core.bazi_rulebook` does not exist.

### Step 2: Add deterministic rule files

Use stable IDs such as `CAL-YEAR-LICHUN`, `CAL-MONTH-JIE`, `CAL-DAY-ZI23`, `PILLAR-HOUR-FIVERAT`, `DAYUN-DIRECTION`, `DAYUN-START-DIV3`, `STRENGTH-SEASON`, `PATTERN-MONTH-QI`, `WEALTH-REVENUE-RETENTION`, and `REL-STAGES`.

Every rule record must contain:

```json
{
  "id": "CAL-DAY-ZI23",
  "section": "calendar",
  "statement": "北京时间23:00起按次日命理日期计算日柱",
  "citations": ["bazi-skill:time-boundary"],
  "priority": 100
}
```

The manifest must list the exact files and SHA-256 digest of their canonical UTF-8 bytes. Tests should rebuild the digest rather than trusting it.

### Step 3: Implement the loader

Expose:

```python
@dataclass(frozen=True)
class Rule:
    id: str
    section: str
    statement: str
    citations: tuple[str, ...]
    priority: int

@dataclass(frozen=True)
class RuleBook:
    version: str
    rules: tuple[Rule, ...]
    sections: Mapping[str, tuple[Rule, ...]]
```

Required callable interfaces are `RuleBook.public_basis() -> dict[str, str]` and cached `load_rulebook() -> RuleBook`.

Fail closed with `RuleBookError` on a bad digest, duplicate ID, missing section, invalid citation, or invalid priority.

### Step 4: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_bazi_rulebook.py -q`

Expected: PASS.

Commit: `git add rules/bazi_skill core/bazi_rulebook.py tests/test_bazi_rulebook.py && git commit -m "feat: add normative bazi rulebook"`

---

## Task 2: Normalize birth input and calendar evidence

**Files:**

- Create: `core/bazi_calendar_adapter.py`
- Modify: `ui/profile_form.py`
- Create: `tests/test_bazi_calendar_adapter.py`
- Modify: `tests/test_lunar_leap_month.py`

### Step 1: Specify the normalized input

Write failing tests for lunar conversion, explicit leap-month selection, unknown-time handling, CST mode, and preservation of the original calendar label.

```python
@dataclass(frozen=True)
class BirthInput:
    calendar: Literal["solar", "lunar"]
    year: int
    month: int
    day: int
    hour: int | None
    minute: int | None
    gender: Literal["male", "female"]
    is_leap_month: bool = False
    time_mode: Literal["china_standard"] = "china_standard"

@dataclass(frozen=True)
class CalendarEvidence:
    civil_datetime: datetime
    converted_solar_date: date
    source_calendar: str
    is_leap_month: bool
    time_mode_label: str
```

Run: `.venv/bin/python -m pytest tests/test_bazi_calendar_adapter.py tests/test_lunar_leap_month.py -q`

Expected: FAIL on missing adapter and leap-month form contract.

### Step 2: Implement a narrow `lunar_python` adapter

Only these functions may import `lunar_python`:

The adapter must expose `normalize_birth_input(value: BirthInput) -> CalendarEvidence`, `day_pillar_seed(day: date) -> tuple[str, str]`, and `jie_boundaries(year: int) -> tuple[JieBoundary, ...]`.

Assert exactly 12 month-changing Jie entries ordered by timestamp. Do not expose library-generated year, month, or hour pillars to production consumers.

### Step 3: Update the form

Show a leap-month checkbox only for lunar input. Allow “时辰不详”; when selected, store `hour=None` and `minute=None` and report that the hour pillar cannot be asserted.

### Step 4: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_bazi_calendar_adapter.py tests/test_lunar_leap_month.py -q`

Expected: PASS.

Commit: `git add core/bazi_calendar_adapter.py ui/profile_form.py tests/test_bazi_calendar_adapter.py tests/test_lunar_leap_month.py && git commit -m "feat: normalize bazi birth input"`

---

## Task 3: Compute all four pillars explicitly

**Files:**

- Create: `core/four_pillars_engine.py`
- Modify: `core/bazi_engine.py`
- Create: `tests/test_four_pillars_engine.py`
- Modify: `tests/test_algorithm_boundaries.py`
- Modify: `tests/test_jieqi_boundary_month_pillar.py`
- Modify: `tests/test_true_solar_time_integration.py`

### Step 1: Write boundary-first tests

Cover one second before/at 立春, one second before/at every monthly Jie, 22:59 versus 23:00, all five day-stem groups for 子时, unknown hour, and CST labels. Include this mandatory regression:

```python
def test_1996_09_04_2345_uses_next_bazi_day():
    chart = calculate_four_pillars(BirthInput(
        calendar="solar", year=1996, month=9, day=4,
        hour=23, minute=45, gender="female",
    ))
    assert chart.day.text == "乙巳"
    assert chart.hour.text == "丙子"
    assert "23:00" in chart.evidence.day_basis
```

Run: `.venv/bin/python -m pytest tests/test_four_pillars_engine.py tests/test_algorithm_boundaries.py tests/test_jieqi_boundary_month_pillar.py -q`

Expected: FAIL because production still delegates pillar decisions.

### Step 2: Implement explicit rules

Expose `calculate_four_pillars(birth: BirthInput) -> FourPillarsResult`.

- Year: compare civil timestamp with exact 立春; derive stem/branch cyclically from the effective year.
- Month branch: choose 寅 through 丑 using the most recent of the 12 Jie.
- Month stem: use 五虎遁 from the year stem.
- Day: if time is at or after 23:00, request the next civil date from `day_pillar_seed`.
- Hour branch: `((hour + 1) // 2) % 12`; 23:00–00:59 is 子.
- Hour stem: use 五鼠遁 from the effective day stem.
- Unknown hour: return `hour=None`, never guess.

Record the exact rule IDs and boundary timestamps in `PillarEvidence`.

### Step 3: Replace the production path

Make `build_bazi_chart()` call `calculate_four_pillars()` and remove any production read of `lunar.getEightChar()` or library-computed year/month/hour pillars. Keep a temporary comparison helper test-only if needed; do not expose it to reports.

### Step 4: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_four_pillars_engine.py tests/test_algorithm_boundaries.py tests/test_jieqi_boundary_month_pillar.py tests/test_true_solar_time_integration.py -q`

Expected: PASS.

Commit: `git add core/four_pillars_engine.py core/bazi_engine.py tests/test_four_pillars_engine.py tests/test_algorithm_boundaries.py tests/test_jieqi_boundary_month_pillar.py tests/test_true_solar_time_integration.py && git commit -m "feat: compute four pillars from explicit rules"`

---

## Task 4: Establish the single `ChartFacts` contract

**Files:**

- Create: `core/chart_facts.py`
- Modify: `core/bazi_engine.py`
- Modify: `core/chart_fingerprint.py`
- Create: `tests/test_chart_facts.py`

### Step 1: Write serialization and immutability tests

Define exact required keys and prove that a report cannot mutate facts. The contract must include normalized input evidence, four pillars, hidden stems, ten gods, element counts, dayun basis, strength evidence, pattern, wealth, relationship, current luck context, internal rule version, and rule IDs.

### Step 2: Implement typed frozen facts

Use frozen dataclasses for in-process use and one `to_dict()` canonical serializer. `chart_fingerprint` must hash canonical facts excluding transient current-date context but including calendar mode and pillar boundary policy.

Public projection:

```python
def public_summary(facts: ChartFacts) -> dict[str, object]:
    return {
        "时间模式": facts.calendar.time_mode_label,
        "四柱计算依据": facts.pillars.evidence.public_text(),
        "起运方向": facts.dayun.direction_label,
        "起运时间": facts.dayun.start_text,
        "强弱证据": facts.strength.public_evidence,
        "格局": facts.pattern.public_text,
        "财运": facts.wealth.public_text,
        "姻缘": facts.relationship.public_text,
    }
```

Assert that neither `算法版本` nor `调候依据` appears in this projection.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_chart_facts.py -q`

Expected: PASS.

Commit: `git add core/chart_facts.py core/bazi_engine.py core/chart_fingerprint.py tests/test_chart_facts.py && git commit -m "refactor: add unified chart facts contract"`

---

## Task 5: Replace dayun direction and start calculation

**Files:**

- Create: `core/dayun_rule_engine.py`
- Modify: `core/luck_engine.py`
- Create: `tests/test_dayun_rule_engine.py`

### Step 1: Write failing direction and interval tests

Test all four combinations of gender and yin/yang year stem. Test forward interval to the next Jie, reverse interval to the previous Jie, exact-boundary zero interval, and conversion of three days to one year with residual days converted consistently to months/days.

### Step 2: Implement the explicit engine

Expose:

```python
@dataclass(frozen=True)
class DayunBasis:
    direction: Literal["forward", "reverse"]
    direction_label: str
    boundary_name: str
    boundary_datetime: datetime
    interval_seconds: int
    start_age_years: int
    start_age_months: int
    start_age_days: int
    start_datetime: datetime
    rule_ids: tuple[str, ...]
```

The engine entry point is `calculate_dayun(facts: PillarCoreFacts) -> DayunBasis`.

Make `core/luck_engine.py` a compatibility adapter that reads `DayunBasis`; it must not recalculate direction or start age.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_dayun_rule_engine.py tests/test_luck_engine.py -q`

Expected: PASS; if `tests/test_luck_engine.py` is absent, run the existing luck test file reported by `rg -l "get_luck_cycles" tests`.

Commit: `git add core/dayun_rule_engine.py core/luck_engine.py tests/test_dayun_rule_engine.py && git commit -m "feat: make dayun calculation rule driven"`

---

## Task 6: Produce auditable strength and pattern evidence

**Files:**

- Modify: `core/strength_engine.py`
- Modify: `core/pattern_engine.py`
- Create: `tests/test_strength_rule_evidence.py`
- Create: `tests/test_pattern_rule_evidence.py`

### Step 1: Lock the evidence schema with failing tests

Strength must report separate evidence for 得令、得地、得助、泄耗克制、合冲造成的有效性变化 and uncertainty. Pattern must identify the month-command source,透干/藏干 basis,成立条件,破格因素, and whether a special pattern was considered then rejected.

### Step 2: Replace opaque totals with evidence aggregation

Scores may remain internal ordering aids, but classification cannot depend on a single unexplained threshold. Each evidence item must contain `rule_id`, `polarity`, `weight`, `fact`, and `explanation`. `public_evidence` must be generated from those items, not a second narrative path.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_strength_rule_evidence.py tests/test_pattern_rule_evidence.py tests/test_strength_engine.py tests/test_pattern_engine.py -q`

Expected: PASS for all files that exist; do not omit existing strength/pattern suites.

Commit: `git add core/strength_engine.py core/pattern_engine.py tests/test_strength_rule_evidence.py tests/test_pattern_rule_evidence.py && git commit -m "refactor: explain strength and pattern decisions"`

---

## Task 7: Add explicit wealth and relationship analyzers

**Files:**

- Create: `core/wealth_analysis.py`
- Create: `core/relationship_analysis.py`
- Create: `tests/test_wealth_analysis.py`
- Create: `tests/test_relationship_analysis.py`

### Step 1: Write domain tests before implementation

Wealth tests must distinguish earning opportunity from retention capacity, inspect direct/indirect wealth visibility and roots, and account for day-master capacity. Relationship tests must distinguish attraction/appearance, relationship formation, and stability; use gender-specific spouse-star convention without claiming current marital status from the natal chart alone.

### Step 2: Implement structured results

```python
@dataclass(frozen=True)
class WealthAnalysis:
    earning_channels: tuple[Evidence, ...]
    retention_factors: tuple[Evidence, ...]
    risk_factors: tuple[Evidence, ...]
    public_text: str

@dataclass(frozen=True)
class RelationshipAnalysis:
    attraction_signals: tuple[Evidence, ...]
    formation_signals: tuple[Evidence, ...]
    stability_signals: tuple[Evidence, ...]
    uncertainty: tuple[str, ...]
    public_text: str
```

Ban deterministic assertions such as “一定结婚/离婚/发财”. Advice must be phrased as tendencies and decision support.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_wealth_analysis.py tests/test_relationship_analysis.py -q`

Expected: PASS.

Commit: `git add core/wealth_analysis.py core/relationship_analysis.py tests/test_wealth_analysis.py tests/test_relationship_analysis.py && git commit -m "feat: add rule-driven wealth and relationship analysis"`

---

## Task 8: Make every report and page consume `ChartFacts`

**Files:**

- Modify: `report/bazi_report.py`
- Modify: `report/wealth_report.py`
- Modify: `report/love_report.py`
- Modify: `report/career_report.py`
- Modify: `core/life_overview_engine.py`
- Modify: `core/yearly_engine.py`
- Modify: `core/monthly_engine.py`
- Modify: `ui/bazi_page.py`
- Modify: `ui/life_overview_page.py`
- Modify: `ui/luck_page.py`
- Modify: `ui/yearly_page.py`
- Modify: `ui/report_page.py`
- Create: `tests/test_chart_facts_consumers.py`
- Create: `tests/test_public_bazi_summary.py`

### Step 1: Add source-contract tests

Patch legacy helpers to raise and prove pages/reports still render from a prepared `ChartFacts`. Scan rendered strings to assert the eight allowed summary labels exist and `算法版本`, `调候依据` do not.

### Step 2: Convert consumers one at a time

Remove local recomputation of ten gods, element strength, pattern, wealth, relationship, and dayun. Yearly/monthly engines may combine current stems/branches with stored facts, but all interpretation must cite project rule IDs.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_chart_facts_consumers.py tests/test_public_bazi_summary.py tests/test_bazi_report.py tests/test_wealth_report.py tests/test_love_report.py -q`

Expected: PASS for all existing named files; use `rg --files tests | rg '(report|page|yearly|monthly)'` to include the rest before commit.

Commit: `git add report core/life_overview_engine.py core/yearly_engine.py core/monthly_engine.py ui/bazi_page.py ui/life_overview_page.py ui/luck_page.py ui/yearly_page.py ui/report_page.py tests/test_chart_facts_consumers.py tests/test_public_bazi_summary.py && git commit -m "refactor: unify bazi report consumers"`

---

## Task 9: Perform the one-time overwrite migration safely

**Files:**

- Modify: `utils/database.py`
- Create: `tests/test_rule_engine_v2_migration.py`

### Step 1: Write migration tests against a temporary SQLite file

Prove the migration:

1. makes exactly one sibling backup before deletion;
2. deletes `bazi_charts` before `profiles` inside one transaction;
3. records `schema_meta.rule_engine_schema = 2`;
4. is idempotent and does not delete new v2 rows on later startups;
5. rolls back if backup creation fails.

### Step 2: Implement the startup migration

Create `schema_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)`. Before opening the destructive transaction, copy the closed database to `<database>.pre-rule-v2-YYYYMMDDHHMMSS.bak` with `shutil.copy2`. Then use `BEGIN IMMEDIATE`, delete child then parent rows, set metadata, and commit. Remove `_ensure_chart_fields`; v2 rows must already match the current schema.

Do not delete logs, exports, or files outside the selected database. Log counts and backup path but never profile contents.

### Step 3: Verify and commit

Run: `.venv/bin/python -m pytest tests/test_rule_engine_v2_migration.py tests/test_database.py -q`

Expected: PASS for files that exist.

Commit: `git add utils/database.py tests/test_rule_engine_v2_migration.py && git commit -m "feat: replace legacy charts for rule engine v2"`

---

## Task 10: Gate release on the five supplied charts

**Files:**

- Create: `tests/fixtures/user_five_bazi_cases.json`
- Create: `tests/test_user_five_bazi_acceptance.py`
- Create: `scripts/render_user_five_bazi_acceptance.py`
- Create: `acceptance_samples/user_five_bazi_acceptance.md`

### Step 1: Encode the confirmed input assumptions

The fixture must contain exactly:

| ID | Input | Calendar | Time handling | Expected four pillars |
|---|---|---|---|---|
| U01 | 1986-07-10 10:00 female | lunar | CST 巳时 | 丙寅/丙申/辛卯/癸巳 |
| U02 | 1977-09-29 19:30 male | lunar | CST 戌时 | 丁巳/辛亥/辛未/戊戌 |
| U03 | 1974-06-17 14:00 male | lunar | 13:00–15:00 treated as 未时 | 甲寅/辛未/丁丑/丁未 |
| U04 | 1994-09-23 18:00 male | solar | CST 酉时 | 甲戌/癸酉/壬子/己酉 |
| U05 | 1996-09-04 23:45 female | solar | 23:00 next bazi day | 丙子/丙申/乙巳/丙子 |

These pillar expectations are the accepted release baseline only after Tasks 2–3 boundary tests pass. If an exact Jie timestamp or calendar conversion contradicts U01–U04, stop and document the concrete evidence instead of silently rewriting the fixture. U05 must never retain the legacy 甲辰 day result.

### Step 2: Test the entire contract

For every case assert conversion, pillars, time mode, direction, non-empty start time, auditable strength evidence, pattern, wealth, relationship, and the eight-field public projection. For U03 preserve the range note. For U05 assert `CAL-DAY-ZI23` in evidence.

### Step 3: Generate a human-readable acceptance record

`scripts/render_user_five_bazi_acceptance.py` must load the same fixture and production engine, then write the eight visible fields for all five cases. The checked-in Markdown is a review artifact, never a second source of truth.

### Step 4: Run focused and full verification

Run:

```bash
.venv/bin/python -m pytest tests/test_user_five_bazi_acceptance.py -q
.venv/bin/python scripts/render_user_five_bazi_acceptance.py
git diff --exit-code acceptance_samples/user_five_bazi_acceptance.md
.venv/bin/python -m pytest tests -q
```

Expected: all tests PASS and generation produces no diff.

### Step 5: Commit the release gate

Commit: `git add tests/fixtures/user_five_bazi_cases.json tests/test_user_five_bazi_acceptance.py scripts/render_user_five_bazi_acceptance.py acceptance_samples/user_five_bazi_acceptance.md && git commit -m "test: gate rule engine on five user charts"`

---

## Final verification checklist

- Run `rg -n "getEightChar|算法版本|调候依据" core report ui` and inspect every match; no production pillar decision may use `getEightChar`, and the two hidden labels may not appear in customer rendering.
- Run `rg -n "lunar_python" core` and confirm imports are confined to `core/bazi_calendar_adapter.py` or a clearly test-only compatibility module.
- Run `.venv/bin/python -m pytest tests -q` and record the pass count.
- Run the app with `.venv/bin/python -m streamlit run app.py --server.port 8501`, create one chart, and verify the eight-field summary visually.
- Restart the app against a temporary legacy database and verify one backup, zero old profiles/charts, and no repeat wipe.
- Do not begin the AI Q&A plan until this plan's full suite and five-case gate pass.
