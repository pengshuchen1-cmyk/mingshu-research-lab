# Kimi 段落映射与局部修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 Kimi 返回 `CLOUD_STRUCTURE_INVALID` 后整篇退回本地模板的问题，使云端只能引用合法 `claim_id`，并在单段失败时保留其他合格云端段落。

**Architecture:** 本地 `AnalysisPlan` 仍是唯一事实与结论来源。Kimi 请求的 JSON Schema 和提示词都携带当前请求允许的 `claim_id`；响应进入本地段落守卫后，未知编号、事实冲突、漏答和重复引用均按段处理。只有没有任何合格云端段落时才整体显示本地答案，同时记录不含客户隐私的精确失败代码。

**Tech Stack:** Python 3、Pydantic、Streamlit、OpenAI Python SDK（Kimi OpenAI-compatible Chat Completions）、pytest。

## Global Constraints

- 四柱、强弱、格局、十神、大运、流年、流月及领域结论继续只来自本地规则。
- Kimi 每个客户问题最多自动调用一次；修复过程不得增加第二次自动云端请求。
- 未知 `claim_id` 的云端正文不得进入最终回答。
- 单个段落失败时只替换该段所覆盖的本地 claim；其他通过校验的云端段落必须保留。
- 如果所有云端段落均不可用，返回本地完整答案，不向客户展示空白或半截回答。
- 失败代码、日志和页面状态不得包含问题正文、命盘、出生资料、联系方式、API Key 或云端原文。
- 继续使用 `kimi-k3`、`low` 推理和最长 90 秒配置，不通过放宽事实校验换取通过率。
- 1999 命例及原有 5 个真实命例只用于验收，不进入规则、提示词示例、缓存样本或训练材料。
- 所有代码修改采用 TDD：先写失败测试并观察预期失败，再写最小实现并运行完整回归。

---

## File Map

### 修改文件

- `services/kimi_bazi_client.py`：根据当前 `AnalysisPlan` 生成带 `claim_id` 枚举的动态 JSON Schema。
- `services/bazi_ai_prompt.py`：显式发送允许的 `claim_id` 清单并要求原样复制。
- `core/ai_segment_guard.py`：未知编号、冲突段落、漏答和重复引用的局部替换。
- `core/ai_orchestrator.py`：区分局部修复、全量本地回退、守卫异常和答案超长。
- `core/ai_session.py`：在会话消息中保留安全的结构校验代码。
- `ui/inquiry_page.py`：显示可读的局部修复或全量回退原因。
- `README.md`：说明云端段落局部修复及匿名诊断代码。

### 测试文件

- `tests/test_kimi_bazi_client.py`
- `tests/test_bazi_ai_prompt.py`
- `tests/test_ai_segment_guard.py`
- `tests/test_ai_orchestrator.py`
- `tests/test_ai_session.py`
- `tests/test_inquiry_chat_page.py`
- `tests/test_ai_logging_privacy.py`
- `tests/test_lunar_1999_acceptance.py`

---

### Task 1: 将 Kimi 输出 Schema 绑定到当前合法 claim

**Files:**
- Modify: `services/kimi_bazi_client.py`
- Modify: `services/bazi_ai_prompt.py`
- Test: `tests/test_kimi_bazi_client.py`
- Test: `tests/test_bazi_ai_prompt.py`

**Interfaces:**
- Consumes: `AIRequestContext.analysis_plan.claims[].id`
- Produces: `_response_format(allowed_claim_ids: tuple[str, ...]) -> dict[str, object]`
- Produces: 云端消息中的 `allowed_claim_ids: list[str]`

- [ ] **Step 1: 写入动态枚举失败测试**

```python
def test_kimi_schema_only_allows_current_plan_claim_ids():
    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    completions = _Completions(_Response(_payload()))
    KimiBaziClient(
        AIConfig("moonshot-secret", True),
        client=_Client(completions),
    ).answer(_context())

    schema = completions.calls[0]["response_format"]["json_schema"]["schema"]
    claim_items = (
        schema["$defs"]["CloudSegment"]["properties"]["claim_ids"]["items"]
    )
    assert claim_items["enum"] == ["wealth.core"]
```

```python
def test_prompt_contains_exact_allowed_claim_catalog():
    from services.bazi_ai_prompt import build_messages

    serialized = json.dumps(build_messages(_context()), ensure_ascii=False)

    assert '"allowed_claim_ids": ["wealth.core"]' in serialized
    assert "必须原样复制 allowed_claim_ids" in serialized
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_kimi_bazi_client.py::test_kimi_schema_only_allows_current_plan_claim_ids \
  tests/test_bazi_ai_prompt.py::test_prompt_contains_exact_allowed_claim_catalog -v
```

Expected: FAIL；当前静态 Schema 没有 `enum`，提示词载荷也没有 `allowed_claim_ids`。

- [ ] **Step 3: 实现请求级动态 Schema**

在 `services/kimi_bazi_client.py` 中从 Pydantic Schema 创建独立副本，禁止修改全局模型 Schema：

```python
from copy import deepcopy


def _response_format(
    allowed_claim_ids: tuple[str, ...],
) -> dict[str, object]:
    schema = deepcopy(CloudBaziAnalysis.model_json_schema())
    claim_items = (
        schema["$defs"]["CloudSegment"]["properties"]["claim_ids"]["items"]
    )
    claim_items["enum"] = list(allowed_claim_ids)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "bazi_cloud_analysis",
            "strict": True,
            "schema": schema,
        },
    }
```

在 `KimiBaziClient.answer()` 中使用当前计划：

```python
plan = context.analysis_plan
if plan is None:
    raise AIServiceError("unparseable_response")
allowed_claim_ids = tuple(claim.id for claim in plan.claims)

response = self._client.chat.completions.create(
    # 保留现有 model/messages/stream/token/reasoning/timeout 参数
    response_format=_response_format(allowed_claim_ids),
)
```

- [ ] **Step 4: 强化提示词但不增加命理事实**

在 `services/bazi_ai_prompt.py` 的用户载荷中加入：

```python
payload = {
    "allowed_claim_ids": [
        claim.id for claim in context.analysis_plan.claims
    ],
    "fact_packet": context.fact_packet.model_dump(mode="json"),
    "analysis_plan": context.analysis_plan.model_dump(mode="json"),
}
```

在系统指令中加入：

```text
每个 claim_id 必须从 allowed_claim_ids 中原样复制；不得翻译、缩写、拼接、
改写或创造新编号。无法展开某个 claim 时省略该段，由本地规则补齐。
```

- [ ] **Step 5: 运行客户端和提示词测试**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_kimi_bazi_client.py \
  tests/test_bazi_ai_prompt.py -q
```

Expected: PASS；Key 不出现在序列化消息中，动态枚举仅包含当前计划编号。

- [ ] **Step 6: 提交**

```bash
git add services/kimi_bazi_client.py services/bazi_ai_prompt.py \
  tests/test_kimi_bazi_client.py tests/test_bazi_ai_prompt.py
git commit -m "fix: constrain kimi claim identifiers"
```

---

### Task 2: 将未知编号和坏段落改为局部替换

**Files:**
- Modify: `core/ai_segment_guard.py`
- Test: `tests/test_ai_segment_guard.py`

**Interfaces:**
- Consumes: `CloudGeneration`, `AnalysisPlan`, `AIRequestContext`
- Produces: `SegmentGuardResult`
- Stable codes: `CLOUD_UNKNOWN_CLAIM_ID`, `GUARD_*`

- [ ] **Step 1: 将“未知编号整篇失败”测试改为局部替换测试**

```python
def test_unknown_claim_id_replaces_only_its_segment():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core", "wealth.timing"))
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[0].id],
                "text": "云端核心段保留。",
            },
            {
                "claim_ids": [plan.claims[1].id, "unknown.claim"],
                "text": "混入未知编号的段落不得保留。",
            },
        ]
    )

    result = validate_and_repair_segments(generation, plan, _context())

    assert result.full_fallback is False
    assert "云端核心段保留。" in result.answer_text
    assert "混入未知编号" not in result.answer_text
    assert plan.claims[1].local_text in result.answer_text
    assert result.violation_codes == ("CLOUD_UNKNOWN_CLAIM_ID",)
    assert result.replaced_claim_ids == (plan.claims[1].id,)
    assert result.retained_cloud_segments == 1
```

再增加全无效场景：

```python
def test_all_unknown_segments_return_complete_local_text():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core", "wealth.timing"))
    result = validate_and_repair_segments(
        _generation(
            [{"claim_ids": ["unknown.claim"], "text": "不得保留。"}]
        ),
        plan,
        _context(),
    )

    assert result.full_fallback is True
    assert result.retained_cloud_segments == 0
    assert result.answer_text.split("\n\n") == [
        plan.claims[0].local_text,
        plan.claims[1].local_text,
    ]
    assert result.violation_codes == ("CLOUD_UNKNOWN_CLAIM_ID",)
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_segment_guard.py::test_unknown_claim_id_replaces_only_its_segment \
  tests/test_ai_segment_guard.py::test_all_unknown_segments_return_complete_local_text -v
```

Expected: FAIL；当前实现发现任意未知编号便立即返回空文本和整篇回退。

- [ ] **Step 3: 扩展结果契约并实现局部处理**

将 `SegmentGuardResult` 扩展为：

```python
@dataclass(frozen=True)
class SegmentGuardResult:
    answer_text: str
    violation_codes: tuple[str, ...]
    replaced_claim_ids: tuple[str, ...]
    retained_cloud_segments: int
    full_fallback: bool
```

每个段落先拆分已知与未知编号：

```python
known_ids = [
    claim_id for claim_id in segment.claim_ids if claim_id in claims
]
unknown_ids = [
    claim_id for claim_id in segment.claim_ids if claim_id not in claims
]
fresh_claim_ids = [
    claim_id for claim_id in known_ids if claim_id not in covered
]

if unknown_ids:
    codes.append("CLOUD_UNKNOWN_CLAIM_ID")
    replaced.update(fresh_claim_ids)
    covered.update(fresh_claim_ids)
    continue
```

随后沿用现有事实冲突校验。最终始终用计划顺序装配：

```python
replaced.update(claim_id for claim_id in claims if claim_id not in covered)
paragraphs: list[str] = []
for claim in plan.claims:
    if claim.id in replaced:
        paragraphs.append(claim.local_text)
    elif claim.id in cloud_paragraphs:
        paragraphs.append(cloud_paragraphs[claim.id])
retained_cloud_segments = len(cloud_paragraphs)
```

`full_fallback` 只表示没有任何云端段落被保留：

```python
full_fallback = retained_cloud_segments == 0
```

- [ ] **Step 4: 补齐边界测试**

增加并验证重复、漏答和全部冲突场景：

```python
def test_duplicate_and_omitted_claims_stay_in_plan_order():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core", "wealth.timing", "wealth.action"))
    result = validate_and_repair_segments(
        _generation(
            [
                {
                    "claim_ids": [plan.claims[1].id],
                    "text": "唯一保留的时间段。",
                },
                {
                    "claim_ids": [plan.claims[1].id],
                    "text": "重复段落不得出现。",
                },
            ]
        ),
        plan,
        _context(),
    )

    assert result.answer_text.split("\n\n") == [
        plan.claims[0].local_text,
        "唯一保留的时间段。",
        plan.claims[2].local_text,
    ]
    assert "重复段落" not in result.answer_text
    assert result.retained_cloud_segments == 1


def test_all_fact_conflict_segments_report_full_fallback():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core",))
    result = validate_and_repair_segments(
        _generation(
            [
                {
                    "claim_ids": [plan.claims[0].id],
                    "text": "你必定发财。",
                }
            ]
        ),
        plan,
        _context(),
    )

    assert result.full_fallback is True
    assert result.retained_cloud_segments == 0
    assert result.answer_text == plan.claims[0].local_text
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)
```

这些测试必须断言：

- 最终段落顺序与 `AnalysisPlan.claims` 一致；
- 每个 claim 只出现一次；
- 未覆盖 claim 使用 `local_text`；
- 任何含未知编号的云端正文都不进入答案。

- [ ] **Step 5: 运行段落守卫测试**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_segment_guard.py -q
```

Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add core/ai_segment_guard.py tests/test_ai_segment_guard.py
git commit -m "fix: repair invalid cloud segments locally"
```

---

### Task 3: 在编排层区分局部成功与三类结构失败

**Files:**
- Modify: `core/ai_orchestrator.py`
- Test: `tests/test_ai_orchestrator.py`

**Interfaces:**
- Consumes: `SegmentGuardResult`
- Produces: `AnswerResult.source`, `degraded_reason`, `violation_codes`
- Stable codes: `CLOUD_UNKNOWN_CLAIM_ID`, `CLOUD_SEGMENT_GUARD_ERROR`, `CLOUD_ANSWER_TOO_LONG`

- [ ] **Step 1: 写入编排层失败测试**

```python
def test_mixed_valid_and_unknown_segments_keep_cloud_source():
    client = _SegmentClient(
        [
            {"claim_ids": ["wealth.core"], "text": "合格云端段落。"},
            {"claim_ids": ["unknown.claim"], "text": "不得展示。"},
        ]
    )

    result = answer_question(
        _chart(),
        "财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 31),
    )

    assert client.calls == 1
    assert result.source == "cloud_validated"
    assert result.degraded_reason is None
    assert "合格云端段落。" in result.answer
    assert "不得展示" not in result.answer
    assert "CLOUD_UNKNOWN_CLAIM_ID" in result.violation_codes
```

```python
def test_all_unknown_segments_use_specific_local_fallback_code():
    client = _SegmentClient(
        [{"claim_ids": ["unknown.claim"], "text": "不得展示。"}]
    )

    result = answer_question(
        _chart(),
        "财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 31),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.degraded_reason == "local_validation_failed"
    assert result.violation_codes == ("CLOUD_UNKNOWN_CLAIM_ID",)
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_orchestrator.py::test_mixed_valid_and_unknown_segments_keep_cloud_source \
  tests/test_ai_orchestrator.py::test_all_unknown_segments_use_specific_local_fallback_code -v
```

Expected: FAIL；当前编排层把未知编号统一记为 `CLOUD_STRUCTURE_INVALID` 并整篇回退。

- [ ] **Step 3: 实现精确编排分支**

将守卫异常改为独立代码：

```python
try:
    guarded = validate_and_repair_segments(generation, plan, context)
except Exception:
    emit("degraded")
    return _local_result(
        local,
        resolved,
        "local_validation_failed",
        violation_codes=("CLOUD_SEGMENT_GUARD_ERROR",),
    )
```

只有 `guarded.full_fallback` 才返回本地来源：

```python
if guarded.full_fallback:
    emit("degraded")
    return _local_result(
        local,
        resolved,
        "local_validation_failed",
        violation_codes=guarded.violation_codes,
    )
```

局部修复仍是 `cloud_validated`，并携带 `guarded.violation_codes`。不得再次调用 Kimi。

- [ ] **Step 4: 将答案容量错误单独编码**

新增内部异常：

```python
class CloudAnswerCapacityError(ValueError):
    pass
```

在 `_cloud_answer_text()` 中：

```python
if not text or len(text) > 6000:
    raise CloudAnswerCapacityError("cloud_answer_capacity_invalid")
```

在 `answer_question()` 中仅捕获该异常并返回：

```python
except CloudAnswerCapacityError:
    emit("degraded")
    return _local_result(
        local,
        resolved,
        "local_validation_failed",
        violation_codes=("CLOUD_ANSWER_TOO_LONG",),
    )
```

- [ ] **Step 5: 验证一次调用与状态机**

主测试已经断言 `client.calls == 1`。再增加守卫异常与容量异常测试：

```python
def test_segment_guard_exception_has_specific_code(monkeypatch):
    import core.ai_orchestrator as orchestrator

    client = _SegmentClient(
        [{"claim_ids": ["wealth.core"], "text": "云端段落。"}]
    )
    monkeypatch.setattr(
        orchestrator,
        "validate_and_repair_segments",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("guard failed")
        ),
    )

    result = orchestrator.answer_question(
        _chart(),
        "财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 31),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.violation_codes == ("CLOUD_SEGMENT_GUARD_ERROR",)


def test_cloud_answer_over_capacity_has_specific_code(monkeypatch):
    import core.ai_orchestrator as orchestrator

    client = _SegmentClient(
        [{"claim_ids": ["wealth.core"], "text": "云端段落。"}]
    )

    def _too_long(*_args, **_kwargs):
        raise orchestrator.CloudAnswerCapacityError(
            "cloud_answer_capacity_invalid"
        )

    monkeypatch.setattr(orchestrator, "_cloud_answer_text", _too_long)
    result = orchestrator.answer_question(
        _chart(),
        "财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 31),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.violation_codes == ("CLOUD_ANSWER_TOO_LONG",)
```

每个测试断言 `client.calls == 1`；局部修复进度最终为 `completed`，全量本地回退最终为 `degraded`。

- [ ] **Step 6: 运行编排测试**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_orchestrator.py -q
```

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add core/ai_orchestrator.py tests/test_ai_orchestrator.py
git commit -m "fix: distinguish partial cloud repairs"
```

---

### Task 4: 在网页和匿名日志中显示可诊断结果

**Files:**
- Modify: `core/ai_session.py`
- Modify: `ui/inquiry_page.py`
- Modify: `utils/logger.py`
- Test: `tests/test_ai_session.py`
- Test: `tests/test_inquiry_chat_page.py`
- Test: `tests/test_ai_logging_privacy.py`

**Interfaces:**
- Consumes: `AnswerResult.violation_codes`
- Produces: 会话安全字段 `details["violation_codes"]`
- Produces: 客户可读提示，不显示内部 claim 编号或云端原文

- [ ] **Step 1: 写入会话与页面失败测试**

```python
def test_session_keeps_only_safe_violation_codes():
    state = {}
    append_chat_message(
        state,
        "assistant",
        "安全正文",
        source="cloud_validated",
        details={
            "violation_codes": [
                "CLOUD_UNKNOWN_CLAIM_ID",
                "非法 code 含客户文本",
            ]
        },
    )

    details = state[CHAT_MESSAGES_KEY][0]["details"]
    assert details["violation_codes"] == ["CLOUD_UNKNOWN_CLAIM_ID"]
```

```python
def test_partial_repair_has_customer_readable_source_note():
    text = repair_notice(("CLOUD_UNKNOWN_CLAIM_ID",))
    assert text == "部分云端段落引用异常，已按本地四柱规则替换。"
    assert "claim" not in text.lower()
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_session.py::test_session_keeps_only_safe_violation_codes \
  tests/test_inquiry_chat_page.py::test_partial_repair_has_customer_readable_source_note -v
```

Expected: FAIL；当前会话没有保存 `violation_codes`，页面也没有局部修复说明。

- [ ] **Step 3: 保存白名单内的安全代码**

在 `core/ai_session.py` 增加：

```python
_VIOLATION_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
```

保存详情时仅接受最多 12 个符合该模式的代码：

```python
raw_codes = details.get("violation_codes", [])
safe_codes = [
    code
    for code in raw_codes[:12]
    if isinstance(code, str)
    and _VIOLATION_CODE_PATTERN.fullmatch(code)
]
if safe_codes:
    safe_details["violation_codes"] = list(dict.fromkeys(safe_codes))
```

在 `_save_answer()` 中传入 `result.violation_codes`。

- [ ] **Step 4: 添加客户可读提示**

在 `ui/inquiry_page.py` 新增：

```python
def repair_notice(codes: tuple[str, ...] | list[str]) -> str:
    values = set(codes)
    if "CLOUD_UNKNOWN_CLAIM_ID" in values:
        return "部分云端段落引用异常，已按本地四柱规则替换。"
    if "CLOUD_ANSWER_TOO_LONG" in values:
        return "云端回答超过安全展示范围，已切换为本地完整分析。"
    if "CLOUD_SEGMENT_GUARD_ERROR" in values:
        return "云端段落校验出现异常，已切换为本地完整分析。"
    return ""
```

`cloud_validated` 且存在局部修复代码时显示 `st.info()`；`local_rules` 时仍显示当前降级警告。原始代码只进入折叠的机器校验明细，不显示 claim 内容。

- [ ] **Step 5: 验证匿名日志不泄露**

增加测试，向 `log_ai_event()` 传入问题、姓名、命盘和 Key 等禁止字段，断言日志记录只含：

```python
{
    "event_code",
    "category",
    "time_scope",
    "model_alias",
    "latency_bucket",
    "reason_code",
    "violation_code",
}
```

并断言三个新代码均可稳定记录：

```python
@pytest.mark.parametrize(
    "code",
    [
        "CLOUD_UNKNOWN_CLAIM_ID",
        "CLOUD_SEGMENT_GUARD_ERROR",
        "CLOUD_ANSWER_TOO_LONG",
    ],
)
def test_structural_failure_codes_are_privacy_safe(code):
    from utils.logger import build_ai_log_record

    record = build_ai_log_record(
        event_code="AI_QA_SEGMENT_REPLACED",
        category="wealth",
        model_alias="kimi:kimi-k3",
        violation_code=code,
        question="张三的财运如何",
        birth_data="1999-08-11 10:00",
        api_key="moonshot-secret",
    )

    assert set(record) == {
        "event_code",
        "category",
        "time_scope",
        "model_alias",
        "latency_bucket",
        "reason_code",
        "violation_code",
    }
    assert record["violation_code"] == code
    serialized = str(record)
    assert "张三" not in serialized
    assert "1999-08-11" not in serialized
    assert "moonshot-secret" not in serialized
```

- [ ] **Step 6: 运行页面、会话和日志测试**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_session.py \
  tests/test_inquiry_chat_page.py \
  tests/test_ai_logging_privacy.py -q
```

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add core/ai_session.py ui/inquiry_page.py utils/logger.py \
  tests/test_ai_session.py tests/test_inquiry_chat_page.py \
  tests/test_ai_logging_privacy.py
git commit -m "feat: expose safe cloud repair diagnostics"
```

---

### Task 5: 回归、真实 Kimi 验收与文档

**Files:**
- Modify: `tests/test_lunar_1999_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Verifies: 1999 命例排盘回执保持 `己卯/壬申/乙未/辛巳`
- Verifies: 本地规则事实不被云端覆盖
- Verifies: Kimi 每题最多调用一次

- [ ] **Step 1: 增加离线端到端回归**

在 `tests/test_lunar_1999_acceptance.py` 增加一个固定假云端响应，其中一个段落引用合法 claim、另一个段落引用未知 claim，断言：

```python
assert result.source == "cloud_validated"
assert result.provider == "kimi"
assert "CLOUD_UNKNOWN_CLAIM_ID" in result.violation_codes
assert valid_cloud_text in result.answer
assert unknown_cloud_text not in result.answer
assert expected_local_replacement in result.answer
assert client.calls == 1
```

同时保留原排盘断言：

```python
assert receipt.solar_text == "1999-08-11 10:00"
assert receipt.pillars == ("己卯", "壬申", "乙未", "辛巳")
```

- [ ] **Step 2: 运行 AI 专项回归**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_kimi_bazi_client.py \
  tests/test_bazi_ai_prompt.py \
  tests/test_ai_segment_guard.py \
  tests/test_ai_orchestrator.py \
  tests/test_ai_session.py \
  tests/test_inquiry_chat_page.py \
  tests/test_ai_logging_privacy.py \
  tests/test_lunar_1999_acceptance.py -q
```

Expected: 全部 PASS，0 failure。

- [ ] **Step 3: 运行完整测试**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: 全部 PASS，0 failure；不得只凭专项测试宣称完成。

- [ ] **Step 4: 更新 README**

加入以下客户行为说明：

```text
云端回答按本地 AnalysisPlan 分段校验。单段引用错误、事实冲突或漏答时，
仅该段使用本地四柱规则结论替换；其他合格云端段落继续保留。
当没有任何云端段落可安全使用时，才显示本地完整答案。
诊断日志只记录匿名失败代码，不保存问题、回答、命盘或出生资料。
```

- [ ] **Step 5: 在用户明确允许后做一次真实 Kimi 验收**

使用农历 1999 年七月初一巳时命例，仅测试：

1. `这个八字的财运怎么样`
2. `这个八字什么时候走财运`
3. `这个八字明年的财运怎么样`

验收标准：

- 每题最多一次 Kimi 调用；
- 单题不超过 90 秒硬截止；
- 页面不再出现笼统的 `CLOUD_STRUCTURE_INVALID`；
- 存在合格云端段落时来源为 `Kimi 云端分析 · 本地规则校验`；
- 局部失败只显示“部分段落已按本地规则替换”；
- 所有年份、大运、强弱、格局和十神仍与本地事实一致。

- [ ] **Step 6: 检查工作树并提交**

Run:

```bash
git status --short
git diff --check
```

Expected: 仅包含本计划范围内的文件，`git diff --check` 无输出。

Commit:

```bash
git add README.md tests/test_lunar_1999_acceptance.py
git commit -m "test: verify kimi partial segment recovery"
```

---

## Final Verification Checklist

- [ ] 动态 JSON Schema 只允许当前 `AnalysisPlan` 的 claim 编号。
- [ ] Kimi 提示词明确要求原样复制合法编号。
- [ ] 未知编号正文永不进入最终回答。
- [ ] 单段失败只替换单段，其他合格云端段落保留。
- [ ] 所有云端段落失败时返回完整本地答案。
- [ ] 每题最多一次云端调用，没有自动二次请求。
- [ ] 三类结构错误拥有独立代码。
- [ ] 页面能区分局部修复和整篇本地回退。
- [ ] 日志与会话详情不含客户隐私和云端原文。
- [ ] 1999 排盘回执保持 `己卯/壬申/乙未/辛巳`。
- [ ] AI 专项测试与完整测试均为 0 failure。
- [ ] 真实 Kimi 验收仅在用户明确允许后执行。
