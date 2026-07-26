# Kimi K3 云端问答接入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让“命数研究室”通过本机 Streamlit secrets 或服务器环境变量安全调用 Kimi K3，并把问答改为问题自适应呈现，同时保留本地四柱事实校验和完整降级。

**Architecture:** 在现有问答编排器与供应商客户端之间加入小型客户端工厂，默认选择 Kimi，保留 OpenAI 适配器。Kimi 使用 OpenAI 兼容的 Chat Completions 与 JSON Schema；内部仍返回可校验字段，页面只展示自然主回答，不固定六段。配置层按“服务器环境变量 → Streamlit secrets → 安全默认值”读取，不允许真实密钥进入版本库。

**Tech Stack:** Python 3、Streamlit、OpenAI Python SDK 2.x、Pydantic 2、pytest、Kimi Chat Completions API

## Global Constraints

- 默认服务商必须是 `kimi`，默认模型必须是 `kimi-k3`。
- 国内 API 地址固定默认值为 `https://api.moonshot.cn/v1`。
- 本机真实密钥只放在 `.streamlit/secrets.toml`；正式部署使用服务器环境变量，且环境变量优先。
- Kimi 只接收去身份化的 `AIRequestContext`，不得接收姓名、原始出生日期时间、地点、经纬度、档案编号或 API Key。
- 本地“四柱八字分析规则”继续作为排盘事实与回答校验的唯一规范来源。
- 页面不固定显示六个回答栏目；简单问题简洁回答，复杂问题自然分段。
- 云端异常必须沿用本地完整回答与明确降级提示。
- 六个真实命例只能用于隔离测试和验收；生产代码不得读取命例文件，命例不得进入提示词、规则库、训练、评分、模板或客户运行时上下文。
- 不删除现有 OpenAI 适配器；默认不启用。

---

## File Map

- Modify: `core/ai_models.py` — 扩展服务商配置，放宽机器辅助列表，保留自然主回答。
- Modify: `core/ai_answer_format.py` — 从固定六段渲染改为自然主回答。
- Modify: `core/ai_answer_guard.py` — 对自然主回答与非空机器证据执行现有事实校验。
- Modify: `core/local_bazi_answer.py` — 组合与问题相关的本地自然回答，不固定六段。
- Modify: `core/ai_orchestrator.py` — 使用客户端工厂，保持重试、校验和降级。
- Create: `services/bazi_ai_prompt.py` — Kimi 与 OpenAI 共用的四柱问答约束和消息构造。
- Create: `services/ai_service_errors.py` — 供应商无关的安全错误分类。
- Modify: `services/openai_bazi_client.py` — 复用共享错误类型，保留 OpenAI 适配。
- Create: `services/kimi_bazi_client.py` — Kimi K3 Chat Completions + JSON Schema 适配器。
- Create: `services/ai_client_factory.py` — 根据配置选择 Kimi/OpenAI 客户端。
- Modify: `ui/inquiry_page.py` — 安全传入 Streamlit secrets，展示自然回答与可选校验明细。
- Modify: `.gitignore` — 忽略真实 secrets，同时允许提交示例文件。
- Create: `.streamlit/secrets.toml.example` — 不含真实密钥的本机配置示例。
- Modify: `README.md` — 记录 Kimi 本机与服务器配置方式。
- Create: `tests/test_kimi_bazi_client.py` — Kimi 请求、结构化解析、隐私与异常测试。
- Create: `tests/test_ai_client_factory.py` — 服务商选择测试。
- Modify: `tests/test_ai_models.py` — 配置优先级与默认值测试。
- Modify: `tests/test_ai_answer_format.py` — 自适应回答契约测试。
- Modify: `tests/test_ai_answer_guard.py` — 自然主回答校验测试。
- Modify: `tests/test_local_bazi_answer.py` — 本地回答不固定六段测试。
- Modify: `tests/test_ai_orchestrator.py` — 工厂路径、重试与降级测试。
- Modify: `tests/test_inquiry_chat_page.py` — 页面不固定六栏和 secrets 注入测试。
- Modify: `tests/test_user_five_ai_acceptance.py` — 只在测试层验证五个命例。
- Modify: `tests/test_lunar_1999_acceptance.py` — 只在测试层验证 1999 命例。
- Modify: `scripts/run_user_five_ai_acceptance.py` — 验收输出适配自然回答，不改变生产路径。

---

### Task 1: 自适应回答契约与本地呈现

**Files:**
- Modify: `tests/test_ai_models.py`
- Modify: `tests/test_ai_answer_format.py`
- Modify: `tests/test_local_bazi_answer.py`
- Modify: `tests/test_ai_answer_guard.py`
- Modify: `tests/test_openai_bazi_client.py`
- Modify: `core/ai_models.py`
- Modify: `core/ai_answer_format.py`
- Modify: `core/local_bazi_answer.py`
- Modify: `core/ai_answer_guard.py`
- Modify: `core/ai_orchestrator.py`
- Create: `services/bazi_ai_prompt.py`
- Modify: `services/openai_bazi_client.py`

**Interfaces:**
- Consumes: `AIRequestContext`, 现有本地命盘事实和规则证据。
- Produces: `BaziAIAnswer.analysis_conclusion: str` 作为完整自然主回答；机器辅助列表仍保留但允许为空；`render_adaptive_markdown(answer) -> str`。

- [ ] **Step 1: 写出自适应回答的失败测试**

将 `tests/test_ai_answer_format.py` 的固定六段断言替换为：

```python
def _adaptive_answer_data() -> dict[str, object]:
    return {
        "analysis_conclusion": (
            "这个命盘的财务重点是先确认承载能力。\n\n"
            "建议先验证现金流，再决定投入规模。"
        ),
        "chart_evidence": ["日主为乙，强弱结论为身弱。"],
        "rule_evidence": ["承财能力需结合日主强弱。"],
        "timing_conditions": [],
        "practical_advice": ["先验证现金流。"],
        "uncertainty_limitations": [],
    }


def test_answer_keeps_one_natural_main_response_without_fixed_six_titles():
    from core.ai_answer_format import render_adaptive_markdown
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer.model_validate(_adaptive_answer_data())
    rendered = render_adaptive_markdown(answer)

    assert rendered == answer.analysis_conclusion
    for title in (
        "### 分析结论",
        "### 命盘依据",
        "### 规则依据",
        "### 阶段与触发条件",
        "### 现实建议",
        "### 不确定性与限制",
    ):
        assert title not in rendered


def test_machine_support_lists_may_be_empty_but_main_answer_may_not():
    from pydantic import ValidationError
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer.model_validate(_adaptive_answer_data())
    assert answer.timing_conditions == []
    assert answer.uncertainty_limitations == []

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate(
            {**_adaptive_answer_data(), "analysis_conclusion": "  "}
        )
```

在 `tests/test_ai_models.py` 将“机器列表必须非空”的断言改为：

```python
def test_ai_answer_allows_empty_machine_lists_and_rejects_unknown_fields():
    from core.ai_models import BaziAIAnswer

    data = {
        "analysis_conclusion": "这是可直接展示的自然回答。",
        "chart_evidence": [],
        "rule_evidence": [],
        "timing_conditions": [],
        "practical_advice": [],
        "uncertainty_limitations": [],
    }
    answer = BaziAIAnswer.model_validate(data)
    assert answer.analysis_conclusion

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate({**data, "extra": "not allowed"})
```

在 `tests/test_local_bazi_answer.py` 新增：

```python
@pytest.mark.parametrize(
    ("category", "question", "requires_timing"),
    [
        ("overview", "请概括命盘", False),
        ("wealth", "财运如何？", False),
        ("career", "事业如何发展？", False),
        ("relationship", "姻缘如何？", False),
        ("family", "家庭关系如何？", False),
        ("timing", "2027年什么时候需要注意？", True),
    ],
)
def test_local_answer_is_detailed_but_not_a_fixed_six_section_template(
    category,
    question,
    requires_timing,
):
    from core.local_bazi_answer import build_local_answer

    context = _context(
        category,
        question,
        requires_timing=requires_timing,
    )
    answer = build_local_answer(context)

    assert len(answer.analysis_conclusion) > 80
    assert "主要依据" in answer.analysis_conclusion
    assert "现实建议" in answer.analysis_conclusion
    assert "规则依据" not in answer.analysis_conclusion
    assert "不确定性与限制" not in answer.analysis_conclusion
```

这个测试完整替换现有
`test_local_answer_has_six_non_empty_sections`；同时将文件内所有
`render_structured_answer(answer)["分析结论"]` 改为
`answer.analysis_conclusion`。

在 `tests/test_ai_answer_guard.py` 新增：

```python
def test_guard_checks_the_natural_main_answer_even_when_optional_lists_are_empty():
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion="乙巳日主一定会发财。",
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())
    assert result.accepted is False
    assert "deterministic_claim" in result.violations
```

在 `tests/test_openai_bazi_client.py` 将固定六段提示词测试替换为：

```python
def test_openai_prompt_requires_adaptive_answer_and_only_supplied_evidence():
    from services.openai_bazi_client import build_messages

    system_prompt = build_messages(_context())[0]["content"]

    assert "完整自然回答" in system_prompt
    assert "不得固定套用六个栏目" in system_prompt
    assert "不得重新计算四柱" in system_prompt
    assert "仅使用请求中提供" in system_prompt
    assert "不得补充未提供" in system_prompt
```

在 `tests/test_ai_orchestrator.py` 机械替换固定结构断言：

```python
assert result.sections == {}
assert result.answer.strip()
```

婚姻状态断言统一直接检查 `result.answer`：

```python
assert "单凭八字，不能确认现实中的婚姻登记状态。" in result.answer
assert "但如果一定要根据命盘作倾向判断：" in result.answer
assert "我更偏向" in result.answer
```

删除该文件的 `SIX_SECTION_TITLES` 常量。

- [ ] **Step 2: 运行测试并确认因固定六段契约而失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_ai_answer_format.py \
  tests/test_local_bazi_answer.py \
  tests/test_ai_answer_guard.py \
  tests/test_openai_bazi_client.py -q
```

Expected: FAIL，至少包含“列表不允许为空”“缺少 `render_adaptive_markdown`”或本地回答仍为旧结构。

- [ ] **Step 3: 实现最小自适应契约**

在 `core/ai_models.py` 中保留主字段并允许机器列表为空：

```python
class BaziAIAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    analysis_conclusion: str = Field(min_length=1, max_length=6000)
    chart_evidence: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=12
    )
    rule_evidence: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=12
    )
    timing_conditions: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=12
    )
    practical_advice: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=12
    )
    uncertainty_limitations: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=8
    )
```

将 `core/ai_answer_format.py` 改为：

```python
"""Presentation helpers for adaptive Bazi answers."""

from __future__ import annotations

from core.ai_models import BaziAIAnswer


def render_adaptive_markdown(answer: BaziAIAnswer) -> str:
    return answer.analysis_conclusion.strip()


def render_structured_answer(answer: BaziAIAnswer) -> dict[str, str]:
    """Compatibility hook: new answers no longer expose fixed UI sections."""
    return {}


def render_structured_markdown(answer: BaziAIAnswer) -> str:
    return render_adaptive_markdown(answer)
```

创建 `services/bazi_ai_prompt.py`：

```python
"""Shared prompt and message construction for Bazi cloud providers."""

from __future__ import annotations

import json

from core.ai_models import AIRequestContext


SYSTEM_INSTRUCTION = """你是命数研究室的四柱问答助手。
仅使用请求中提供的去身份化命盘事实和本地规则，不得补充未提供的事实、
规则或现实状态。不得重新计算四柱、节气、起运或大运。
analysis_conclusion 必须是一段可直接展示给客户的完整自然回答：
简单问题简洁直接，复杂问题可自然分段，但不得固定套用六个栏目。
其余列表是机器校验材料，可按问题相关性返回空列表。
不得保证结婚、离婚、发财、疾病、死亡、法律、投资或借贷结果。
询问当前婚姻状态时，主回答必须先以
“单凭八字，不能确认现实中的婚姻登记状态。”开头，再给概率倾向。
"""


def build_messages(context: AIRequestContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {
            "role": "user",
            "content": json.dumps(
                context.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
    ]
```

在 `services/openai_bazi_client.py` 删除本地提示词和 `build_messages`，
改为：

```python
from services.bazi_ai_prompt import build_messages
```

在 `core/local_bazi_answer.py` 增加自然组合函数：

```python
def _bullet_block(title: str, items: Sequence[str], limit: int) -> str:
    selected = _deduplicated(items, limit=limit)
    if not selected:
        return ""
    return f"**{title}**\n" + "\n".join(f"- {item}" for item in selected)


def _adaptive_local_text(
    context: AIRequestContext,
    conclusion: str,
    chart_evidence: Sequence[str],
    rule_evidence: Sequence[str],
    timing: Sequence[str],
    advice: Sequence[str],
    limitations: Sequence[str],
) -> str:
    parts = [_bounded_string(conclusion)]
    evidence = [*chart_evidence[:4], *rule_evidence[:2]]
    if evidence:
        parts.append(_bullet_block("主要依据", evidence, 6))
    if (context.requires_timing or context.category == "timing") and timing:
        parts.append(_bullet_block("阶段观察", timing, 4))
    if advice:
        parts.append(_bullet_block("现实建议", advice, 4))
    if limitations and (
        context.category == "relationship"
        or context.requires_timing
        or any(term in context.question for term in _BORROWING_TERMS)
    ):
        parts.append(_bullet_block("需要说明", limitations, 4))
    return "\n\n".join(part for part in parts if part)
```

在 `build_local_answer()` 中先计算各列表，再返回：

```python
    conclusion = _analysis_conclusion(context, facts)
    timing = _timing_conditions(context, facts)
    advice = _practical_advice(context)
    limitations = _limitations(context)
    return BaziAIAnswer(
        analysis_conclusion=_adaptive_local_text(
            context,
            conclusion,
            chart_evidence,
            rule_evidence,
            timing,
            advice,
            limitations,
        ),
        chart_evidence=chart_evidence,
        rule_evidence=rule_evidence,
        timing_conditions=timing,
        practical_advice=advice,
        uncertainty_limitations=limitations,
    )
```

保持 `core/ai_answer_guard.py` 的 `combined` 仍以 `analysis_conclusion` 开头；将空列表视为允许，不新增空证据违规：

```python
    if answer.chart_evidence and not all(
        any(fact in item or item in fact for fact in authorized_facts)
        for item in answer.chart_evidence
    ):
        violations.append("unmapped_chart_evidence")
    if answer.rule_evidence and not all(
        any(statement in item or item in statement for statement in rule_statements)
        for item in answer.rule_evidence
    ):
        violations.append("unmapped_rule_evidence")
```

在 `core/ai_orchestrator.py` 中继续构造 `AnswerResult`，但新回答不再生成固定 sections：

```python
    return AnswerResult(
        answer=render_adaptive_markdown(answer),
        sections={},
        chart_evidence=tuple(answer.chart_evidence),
        rule_evidence=tuple(answer.rule_evidence),
        timing_conditions=tuple(answer.timing_conditions),
        practical_advice=tuple(answer.practical_advice),
        uncertainty=tuple(answer.uncertainty_limitations),
        source=source,
        degraded_reason=degraded_reason,
    )
```

- [ ] **Step 4: 运行目标测试并确认通过**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_ai_answer_format.py \
  tests/test_local_bazi_answer.py \
  tests/test_ai_answer_guard.py \
  tests/test_openai_bazi_client.py \
  tests/test_ai_orchestrator.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add \
  core/ai_models.py \
  core/ai_answer_format.py \
  core/local_bazi_answer.py \
  core/ai_answer_guard.py \
  core/ai_orchestrator.py \
  services/bazi_ai_prompt.py \
  services/openai_bazi_client.py \
  tests/test_ai_models.py \
  tests/test_ai_answer_format.py \
  tests/test_local_bazi_answer.py \
  tests/test_ai_answer_guard.py \
  tests/test_openai_bazi_client.py \
  tests/test_ai_orchestrator.py
git commit -m "refactor: render adaptive bazi answers"
```

---

### Task 2: Kimi 配置与本机 secrets

**Files:**
- Modify: `tests/test_ai_models.py`
- Modify: `tests/test_inquiry_chat_page.py`
- Modify: `core/ai_models.py`
- Modify: `ui/inquiry_page.py`
- Modify: `.gitignore`
- Create: `.streamlit/secrets.toml.example`

**Interfaces:**
- Consumes: 环境变量映射、可选 Streamlit secrets 映射。
- Produces: `AIConfig.from_environment(secrets: Mapping[str, object] | None = None) -> AIConfig`，字段 `provider`、`base_url`。

- [ ] **Step 1: 写出配置优先级失败测试**

在 `tests/test_ai_models.py` 添加：

```python
def test_kimi_is_default_and_streamlit_secrets_enable_cloud(monkeypatch):
    from core.ai_models import AIConfig

    for name in (
        "MINGSHU_AI_PROVIDER",
        "MOONSHOT_API_KEY",
        "MINGSHU_AI_MODEL",
        "MINGSHU_AI_BASE_URL",
        "MINGSHU_AI_REASONING",
    ):
        monkeypatch.delenv(name, raising=False)

    config = AIConfig.from_environment(
        {"MOONSHOT_API_KEY": "local-secret"}
    )

    assert config.enabled is True
    assert config.api_key == "local-secret"
    assert config.provider == "kimi"
    assert config.model == "kimi-k3"
    assert config.base_url == "https://api.moonshot.cn/v1"
    assert config.reasoning_effort == "high"


def test_server_environment_overrides_streamlit_secrets(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_PROVIDER", "kimi")
    monkeypatch.setenv("MOONSHOT_API_KEY", "server-secret")
    monkeypatch.setenv("MINGSHU_AI_MODEL", "kimi-k3")
    monkeypatch.setenv("MINGSHU_AI_BASE_URL", "https://api.moonshot.cn/v1")
    monkeypatch.setenv("MINGSHU_AI_REASONING", "max")

    config = AIConfig.from_environment(
        {
            "MOONSHOT_API_KEY": "local-secret",
            "MINGSHU_AI_MODEL": "should-not-win",
        }
    )

    assert config.api_key == "server-secret"
    assert config.model == "kimi-k3"
    assert config.reasoning_effort == "max"


def test_openai_provider_keeps_its_own_key(monkeypatch):
    from core.ai_models import AIConfig

    monkeypatch.setenv("MINGSHU_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

    config = AIConfig.from_environment()
    assert config.provider == "openai"
    assert config.api_key == "openai-secret"
```

在 `tests/test_inquiry_chat_page.py` 添加：

```python
def test_question_page_passes_streamlit_secrets_to_config(monkeypatch):
    import ui.inquiry_page as inquiry_page
    from core.ai_models import AnswerResult

    captured = []
    fake = _FakeStreamlit()
    fake.secrets = {"MOONSHOT_API_KEY": "local-secret"}
    result = AnswerResult(
        answer="本地回答",
        sections={},
        chart_evidence=(),
        rule_evidence=(),
        timing_conditions=(),
        practical_advice=(),
        uncertainty=(),
        source="local_rules",
        degraded_reason="missing_api_key",
    )
    monkeypatch.setattr(inquiry_page, "st", fake)
    monkeypatch.setattr(
        inquiry_page.AIConfig,
        "from_environment",
        classmethod(lambda cls, secrets=None: captured.append(secrets) or SimpleNamespace(
            enabled=False,
            provider="kimi",
            model="kimi-k3",
        )),
    )
    monkeypatch.setattr(
        inquiry_page,
        "answer_question",
        lambda *_a, **_k: result,
    )
    monkeypatch.setattr(inquiry_page, "log_ai_event", lambda **_kwargs: None)
    monkeypatch.setattr(inquiry_page, "touch_private_session", lambda _state: None)
    monkeypatch.setattr(inquiry_page, "_render_message", lambda _item: None)

    inquiry_page._answer({"pillars": {}}, "财运如何？")
    assert captured == [fake.secrets]
```

- [ ] **Step 2: 运行测试并确认默认仍是 OpenAI 而失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_inquiry_chat_page.py -q
```

Expected: FAIL，显示 `AIConfig` 缺少 `provider/base_url`、默认模型不符或方法不接受 secrets。

- [ ] **Step 3: 实现配置读取**

在 `core/ai_models.py` 中添加：

```python
from collections.abc import Mapping


def _setting(
    secrets: Mapping[str, object],
    name: str,
    default: str = "",
) -> str:
    environment_value = os.environ.get(name)
    if environment_value is not None and environment_value.strip():
        return environment_value.strip()
    secret_value = secrets.get(name, default)
    return str(secret_value or default).strip()
```

扩展 `AIConfig`，保持旧位置参数兼容：

```python
@dataclass(frozen=True)
class AIConfig:
    api_key: str = field(repr=False)
    enabled: bool
    model: str = "kimi-k3"
    reasoning_effort: str = "high"
    timeout_seconds: int = 30
    provider: str = "kimi"
    base_url: str = "https://api.moonshot.cn/v1"

    @classmethod
    def from_environment(
        cls,
        secrets: Mapping[str, object] | None = None,
    ) -> "AIConfig":
        source = secrets if secrets is not None else {}
        provider = _setting(source, "MINGSHU_AI_PROVIDER", "kimi").lower()
        key_name = "OPENAI_API_KEY" if provider == "openai" else "MOONSHOT_API_KEY"
        api_key = _setting(source, key_name)
        default_model = "gpt-5.6-sol" if provider == "openai" else "kimi-k3"
        default_base_url = (
            "https://api.openai.com/v1"
            if provider == "openai"
            else "https://api.moonshot.cn/v1"
        )
        model = _setting(source, "MINGSHU_AI_MODEL", default_model)
        reasoning = _setting(source, "MINGSHU_AI_REASONING", "high").lower()
        if provider == "kimi":
            reasoning = "high" if reasoning == "medium" else reasoning
            if reasoning not in {"low", "high", "max"}:
                reasoning = "high"
        elif reasoning not in {"low", "medium", "high"}:
            reasoning = "medium"
        try:
            timeout = int(_setting(source, "MINGSHU_AI_TIMEOUT_SECONDS", "30"))
        except ValueError:
            timeout = 30
        return cls(
            api_key=api_key,
            enabled=bool(api_key) and provider in {"kimi", "openai"},
            model=model,
            reasoning_effort=reasoning,
            timeout_seconds=min(60, max(5, timeout)),
            provider=provider,
            base_url=_setting(source, "MINGSHU_AI_BASE_URL", default_base_url),
        )
```

在 `ui/inquiry_page.py` 中增加：

```python
def _runtime_ai_config() -> AIConfig:
    try:
        secrets = st.secrets
    except (FileNotFoundError, RuntimeError):
        secrets = {}
    return AIConfig.from_environment(secrets)
```

并把 `_answer()` 内的配置读取改为：

```python
    config = _runtime_ai_config()
    model_alias = (
        f"{config.provider}:{config.model}" if config.enabled else "local"
    )
```

将 `.gitignore` 中的 `.streamlit/` 改为：

```gitignore
.streamlit/*
!.streamlit/secrets.toml.example
```

创建 `.streamlit/secrets.toml.example`：

```toml
MINGSHU_AI_PROVIDER = "kimi"
MOONSHOT_API_KEY = "replace-with-your-own-key"
MINGSHU_AI_MODEL = "kimi-k3"
MINGSHU_AI_BASE_URL = "https://api.moonshot.cn/v1"
MINGSHU_AI_REASONING = "high"
MINGSHU_AI_TIMEOUT_SECONDS = "30"
```

- [ ] **Step 4: 验证配置和密钥文件边界**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_models.py \
  tests/test_inquiry_chat_page.py -q
git check-ignore .streamlit/secrets.toml
git check-ignore -v .streamlit/secrets.toml.example || true
```

Expected: pytest PASS；真实 `secrets.toml` 被忽略；示例文件不被忽略。

- [ ] **Step 5: 提交**

```bash
git add \
  core/ai_models.py \
  ui/inquiry_page.py \
  tests/test_ai_models.py \
  tests/test_inquiry_chat_page.py \
  .gitignore \
  .streamlit/secrets.toml.example
git commit -m "feat: load Kimi settings securely"
```

---

### Task 3: 供应商无关错误分类

**Files:**
- Create: `services/ai_service_errors.py`
- Modify: `services/openai_bazi_client.py`
- Modify: `tests/test_openai_bazi_client.py`
- Create: `tests/test_ai_service_errors.py`

**Interfaces:**
- Produces: `AIServiceError(code: str)`；`classify_service_error(exc: Exception) -> str`。
- Consumes: OpenAI/Kimi SDK 异常的 `status_code`、`code`、`type` 和类名。

- [ ] **Step 1: 写出 Kimi 余额与认证错误的失败测试**

创建 `tests/test_ai_service_errors.py`：

```python
from __future__ import annotations

import pytest


class ProviderError(Exception):
    def __init__(self, message, *, status_code=None, code=None, error_type=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.type = error_type


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ProviderError("bad key", status_code=401), "invalid_credentials"),
        (
            ProviderError(
                "balance unavailable",
                status_code=403,
                error_type="exceeded_current_quota_error",
            ),
            "insufficient_quota",
        ),
        (ProviderError("forbidden", status_code=403), "invalid_credentials"),
        (ProviderError("slow down", status_code=429), "rate_limited"),
        (TimeoutError("slow"), "timeout"),
        (ConnectionError("offline"), "network_error"),
        (ProviderError("upstream", status_code=503), "service_unavailable"),
    ],
)
def test_shared_error_classifier_is_deterministic(error, expected):
    from services.ai_service_errors import classify_service_error

    assert classify_service_error(error) == expected


def test_service_error_never_exposes_raw_provider_message():
    from services.ai_service_errors import AIServiceError

    error = AIServiceError("invalid_credentials")
    assert str(error) == "invalid_credentials"
    assert error.code == "invalid_credentials"
```

- [ ] **Step 2: 运行测试并确认模块不存在**

Run:

```bash
.venv/bin/python -m pytest tests/test_ai_service_errors.py -q
```

Expected: FAIL with `ModuleNotFoundError: services.ai_service_errors`。

- [ ] **Step 3: 实现共享错误模块并让 OpenAI 复用**

创建 `services/ai_service_errors.py`：

```python
"""Privacy-safe error normalization shared by cloud AI providers."""

from __future__ import annotations


class AIServiceError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def classify_service_error(exc: Exception) -> str:
    exception_name = type(exc).__name__.lower()
    status = getattr(exc, "status_code", None)
    code = str(getattr(exc, "code", "") or "").lower()
    error_type = str(getattr(exc, "type", "") or "").lower()
    safe_tokens = f"{code} {error_type}".lower()

    if isinstance(exc, TimeoutError) or "timeout" in exception_name:
        return "timeout"
    if any(
        token in safe_tokens
        for token in (
            "insufficient_quota",
            "exceeded_current_quota",
            "balance_not_enough",
            "billing",
            "quota",
        )
    ) and status in {402, 403, 429}:
        return "insufficient_quota"
    if status in {401, 403}:
        return "invalid_credentials"
    if status == 429:
        return "rate_limited"
    if status in {500, 502, 503, 504}:
        return "service_unavailable"
    if (
        isinstance(exc, (ConnectionError, OSError))
        or "connection" in exception_name
    ):
        return "network_error"
    return "service_unavailable"
```

在 `services/openai_bazi_client.py` 删除本地定义并导入：

```python
from services.ai_service_errors import AIServiceError, classify_service_error
```

保留这个导入在模块顶层，使既有的
`from services.openai_bazi_client import AIServiceError`
仍然可用。

- [ ] **Step 4: 运行共享与 OpenAI 回归测试**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_service_errors.py \
  tests/test_openai_bazi_client.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add \
  services/ai_service_errors.py \
  services/openai_bazi_client.py \
  tests/test_ai_service_errors.py \
  tests/test_openai_bazi_client.py
git commit -m "refactor: share cloud AI error handling"
```

---

### Task 4: Kimi K3 Chat Completions 适配器

**Files:**
- Create: `tests/test_kimi_bazi_client.py`
- Create: `services/kimi_bazi_client.py`

**Interfaces:**
- Consumes: `AIConfig`、`AIRequestContext`。
- Produces: `KimiBaziClient.answer(context: AIRequestContext) -> BaziAIAnswer`。

- [ ] **Step 1: 写出 Kimi 请求和解析失败测试**

创建 `tests/test_kimi_bazi_client.py`：

```python
from __future__ import annotations

import json

import pytest


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content, finish_reason="stop"):
        self.message = _Message(content)
        self.finish_reason = finish_reason


class _Response:
    def __init__(self, content, finish_reason="stop"):
        self.choices = [_Choice(content, finish_reason)]


class _Completions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class _Client:
    def __init__(self, completions):
        self.chat = type("Chat", (), {"completions": completions})()


def _context():
    from core.ai_models import AIRequestContext

    return AIRequestContext(
        question="财运如何？",
        category="wealth",
        requires_timing=False,
        chart_facts={
            "pillars": ["甲子", "乙丑", "丙寅", "丁卯"],
            "day_master": "丙",
        },
        rule_evidence=[
            {"id": "WEALTH-CAPACITY", "statement": "承财看日主能力"}
        ],
        history=[],
    )


def _payload():
    return json.dumps(
        {
            "analysis_conclusion": "财务重点是承载能力。",
            "chart_evidence": ["丙日主"],
            "rule_evidence": ["承财看日主能力"],
            "timing_conditions": [],
            "practical_advice": ["先核对现金流"],
            "uncertainty_limitations": [],
        },
        ensure_ascii=False,
    )


def test_kimi_client_uses_k3_json_schema_and_deidentified_messages():
    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    completions = _Completions(_Response(_payload()))
    config = AIConfig(
        "moonshot-secret",
        True,
        "kimi-k3",
        "high",
        30,
        "kimi",
        "https://api.moonshot.cn/v1",
    )
    result = KimiBaziClient(config, client=_Client(completions)).answer(_context())
    call = completions.calls[0]

    assert result.analysis_conclusion == "财务重点是承载能力。"
    assert call["model"] == "kimi-k3"
    assert call["stream"] is False
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["extra_body"] == {"reasoning_effort": "high"}
    assert call["timeout"] == 30
    serialized = json.dumps(call["messages"], ensure_ascii=False)
    assert "财运如何" in serialized
    assert "承财看日主能力" in serialized
    assert "moonshot-secret" not in serialized


@pytest.mark.parametrize(
    "response",
    [
        _Response("not json"),
        _Response("{}"),
        _Response(_payload(), finish_reason="length"),
        type("NoChoices", (), {"choices": []})(),
    ],
)
def test_kimi_client_rejects_incomplete_or_invalid_responses(response):
    from core.ai_models import AIConfig
    from services.ai_service_errors import AIServiceError
    from services.kimi_bazi_client import KimiBaziClient

    client = KimiBaziClient(
        AIConfig("key", True),
        client=_Client(_Completions(response)),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())
    assert captured.value.code == "unparseable_response"
```

- [ ] **Step 2: 运行测试并确认适配器不存在**

Run:

```bash
.venv/bin/python -m pytest tests/test_kimi_bazi_client.py -q
```

Expected: FAIL with `ModuleNotFoundError: services.kimi_bazi_client`。

- [ ] **Step 3: 实现 Kimi 客户端**

创建 `services/kimi_bazi_client.py`：

```python
"""Kimi K3 Chat Completions adapter for de-identified Bazi facts."""

from __future__ import annotations

import json

from core.ai_models import AIConfig, AIRequestContext, BaziAIAnswer
from services.bazi_ai_prompt import build_messages
from services.ai_service_errors import AIServiceError, classify_service_error


def _response_format() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "bazi_ai_answer",
            "strict": True,
            "schema": BaziAIAnswer.model_json_schema(),
        },
    }


class KimiBaziClient:
    def __init__(self, config: AIConfig, client: object | None = None):
        self._config = config
        if client is not None:
            self._client = client
        elif config.enabled:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
            )
        else:
            self._client = None

    def answer(self, context: AIRequestContext) -> BaziAIAnswer:
        if self._client is None:
            raise AIServiceError("disabled")
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=build_messages(context),
                response_format=_response_format(),
                stream=False,
                max_completion_tokens=4000,
                extra_body={
                    "reasoning_effort": self._config.reasoning_effort,
                },
                timeout=self._config.timeout_seconds,
            )
            choices = getattr(response, "choices", None) or []
            if not choices or getattr(choices[0], "finish_reason", None) == "length":
                raise AIServiceError("unparseable_response")
            content = getattr(getattr(choices[0], "message", None), "content", None)
            parsed = json.loads(content) if isinstance(content, str) else None
            return BaziAIAnswer.model_validate(parsed)
        except AIServiceError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError):
            raise AIServiceError("unparseable_response") from None
        except Exception as exc:
            raise AIServiceError(classify_service_error(exc)) from None
```

- [ ] **Step 4: 运行适配器测试**

Run:

```bash
.venv/bin/python -m pytest tests/test_kimi_bazi_client.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add services/kimi_bazi_client.py tests/test_kimi_bazi_client.py
git commit -m "feat: add Kimi K3 bazi client"
```

---

### Task 5: 客户端工厂与问答编排接线

**Files:**
- Create: `tests/test_ai_client_factory.py`
- Modify: `tests/test_ai_orchestrator.py`
- Create: `services/ai_client_factory.py`
- Modify: `core/ai_orchestrator.py`

**Interfaces:**
- Consumes: `AIConfig`。
- Produces: `build_ai_client(config: AIConfig) -> object`，返回具有 `answer(context)` 方法的客户端。

- [ ] **Step 1: 写出服务商选择失败测试**

创建 `tests/test_ai_client_factory.py`：

```python
from __future__ import annotations

import pytest


def test_factory_selects_kimi_by_default():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.kimi_bazi_client import KimiBaziClient

    client = build_ai_client(AIConfig("key", True))
    assert isinstance(client, KimiBaziClient)


def test_factory_keeps_openai_available():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.openai_bazi_client import OpenAIBaziClient

    client = build_ai_client(
        AIConfig(
            "key",
            True,
            "gpt-5.6-sol",
            "medium",
            30,
            "openai",
            "https://api.openai.com/v1",
        )
    )
    assert isinstance(client, OpenAIBaziClient)


def test_factory_rejects_unknown_provider_without_external_call():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.ai_service_errors import AIServiceError

    with pytest.raises(AIServiceError) as captured:
        build_ai_client(
            AIConfig("key", True, provider="unknown")
        )
    assert captured.value.code == "service_unavailable"
```

在 `tests/test_ai_orchestrator.py` 新增工厂替换测试：

```python
def test_orchestrator_builds_configured_provider_when_client_not_injected(monkeypatch):
    import core.ai_orchestrator as orchestrator
    from core.ai_models import AIConfig

    fake = _FakeClient([
        _answer("壬日主的财务重点是现金流。", "壬日主")
    ])
    captured = []
    monkeypatch.setattr(
        orchestrator,
        "build_ai_client",
        lambda config: captured.append(config.provider) or fake,
    )

    result = orchestrator.answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True, provider="kimi"),
    )

    assert captured == ["kimi"]
    assert result.source == "cloud_validated"
```

- [ ] **Step 2: 运行测试并确认工厂不存在**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_client_factory.py \
  tests/test_ai_orchestrator.py -q
```

Expected: FAIL with `ModuleNotFoundError` 或编排器仍直接创建 `OpenAIBaziClient`。

- [ ] **Step 3: 实现工厂并接线**

创建 `services/ai_client_factory.py`：

```python
"""Select the configured cloud AI adapter."""

from __future__ import annotations

from core.ai_models import AIConfig
from services.ai_service_errors import AIServiceError
from services.kimi_bazi_client import KimiBaziClient
from services.openai_bazi_client import OpenAIBaziClient


def build_ai_client(config: AIConfig) -> object:
    if config.provider == "kimi":
        return KimiBaziClient(config)
    if config.provider == "openai":
        return OpenAIBaziClient(config)
    raise AIServiceError("service_unavailable")
```

在 `core/ai_orchestrator.py` 改为：

```python
from services.ai_client_factory import build_ai_client
from services.ai_service_errors import AIServiceError
```

并替换客户端构造：

```python
    try:
        service = client or build_ai_client(config)
    except AIServiceError as exc:
        return _local_result(context, _degradation_reason(exc.code))
```

- [ ] **Step 4: 运行编排回归**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_ai_client_factory.py \
  tests/test_ai_orchestrator.py \
  tests/test_openai_bazi_client.py \
  tests/test_kimi_bazi_client.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add \
  services/ai_client_factory.py \
  core/ai_orchestrator.py \
  tests/test_ai_client_factory.py \
  tests/test_ai_orchestrator.py
git commit -m "feat: route bazi questions to configured AI provider"
```

---

### Task 6: 网页自然回答与安全状态显示

**Files:**
- Modify: `tests/test_inquiry_chat_page.py`
- Modify: `tests/test_inquiry_chat_source_contract.py`
- Modify: `ui/inquiry_page.py`
- Modify: `core/ai_session.py`

**Interfaces:**
- Consumes: `AnswerResult.answer` 与可选证据列表。
- Produces: 页面主区域只显示自然回答；非空机器证据只在折叠明细中显示；来源显示 Kimi 云端分析通过本地校验。

- [ ] **Step 1: 写出不固定六栏的页面失败测试**

将 `tests/test_inquiry_chat_page.py` 的固定六栏测试替换为：

```python
def test_assistant_message_renders_natural_answer_without_fixed_section_headers(
    monkeypatch,
):
    import ui.inquiry_page as inquiry_page

    fake = _FakeStreamlit()
    monkeypatch.setattr(inquiry_page, "st", fake)

    inquiry_page._render_message(
        {
            "role": "assistant",
            "content": "这是针对当前问题的自然回答。",
            "source": "cloud_validated",
            "details": {
                "chart_evidence": ["壬日主"],
                "rule_evidence": ["承财先看强弱"],
            },
        }
    )

    assert fake.markdowns == ["这是针对当前问题的自然回答。", "**命盘证据**", "**规则依据**"]
    assert all(not text.startswith("### ") for text in fake.markdowns)
    assert fake.expanders == ["查看补充的机器校验明细"]
    assert fake.captions == ["Kimi 云端分析 · 本地规则校验"]
```

在 `tests/test_inquiry_chat_source_contract.py` 将云端来源预期改为：

```python
assert answer_source_label("cloud_validated", None) == "Kimi 云端分析 · 本地规则校验"
```

- [ ] **Step 2: 运行测试并确认页面仍固定渲染 sections**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_inquiry_chat_page.py \
  tests/test_inquiry_chat_source_contract.py \
  tests/test_ai_session.py -q
```

Expected: FAIL，页面仍输出固定 `###` 标题或来源标签仍为通用云端 AI。

- [ ] **Step 3: 实现自然回答呈现**

在 `ui/inquiry_page.py`：

```python
def answer_source_label(source: str, degraded_reason: str | None) -> str:
    if source == "cloud_validated":
        return "Kimi 云端分析 · 本地规则校验"
    # 保留现有本地降级映射
```

将 `_render_message()` 的 assistant 分支改为：

```python
        if role == "assistant":
            degraded_reason = details.get("degraded_reason")
            warning = degradation_warning(degraded_reason)
            if warning:
                st.warning(warning)
            st.markdown(str(item.get("content", "")))
            st.caption(
                answer_source_label(
                    str(item.get("source", "local_rules")),
                    degraded_reason,
                )
            )
            _render_supporting_details(item)
```

从 `ui/inquiry_page.py` 删除 `SIX_SECTION_TITLES` 和固定 sections 循环。`_save_answer()` 不再保存 sections：

```python
        details={
            "chart_evidence": list(result.chart_evidence),
            "rule_evidence": list(result.rule_evidence),
            "timing_conditions": list(result.timing_conditions),
            "practical_advice": list(result.practical_advice),
            "uncertainty": list(result.uncertainty),
            "degraded_reason": result.degraded_reason,
        },
```

在 `core/ai_session.py` 从新消息的安全明细契约中删除 `sections` 处理；保留其他列表与降级原因。

- [ ] **Step 4: 运行页面与会话测试**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_inquiry_chat_page.py \
  tests/test_inquiry_chat_source_contract.py \
  tests/test_ai_session.py -q
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add \
  ui/inquiry_page.py \
  core/ai_session.py \
  tests/test_inquiry_chat_page.py \
  tests/test_inquiry_chat_source_contract.py \
  tests/test_ai_session.py
git commit -m "refactor: show adaptive Kimi answers"
```

---

### Task 7: 文档、命例隔离与完整验收

**Files:**
- Modify: `README.md`
- Modify: `tests/test_user_five_ai_acceptance.py`
- Modify: `tests/test_lunar_1999_acceptance.py`
- Modify: `scripts/run_user_five_ai_acceptance.py`
- Modify: `acceptance_samples/user_five_ai_acceptance.md`
- Modify: `acceptance_samples/lunar_1999_acceptance.md` only if the deterministic renderer changes it
- Create: `tests/test_acceptance_fixture_isolation.py`

**Interfaces:**
- Consumes: 前六个任务完成的配置、Kimi 客户端和自然回答。
- Produces: 文档、隔离证明、离线完整验收；可选显式 live smoke test。

- [ ] **Step 1: 写出真实命例不得进入生产代码的失败测试**

创建 `tests/test_acceptance_fixture_isolation.py`：

```python
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIRS = ("core", "services", "ui", "utils")
FORBIDDEN_CASE_MARKERS = (
    "1986-08",
    "1977-",
    "1974-",
    "1994-09-23",
    "1996-09-04",
    "1999-08-11",
    "user_five_bazi_cases.json",
    "lunar_1999_bazi_case.json",
)


def test_production_code_does_not_read_or_embed_acceptance_cases():
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for directory in PRODUCTION_DIRS
        for path in (ROOT / directory).rglob("*.py")
    )

    for marker in FORBIDDEN_CASE_MARKERS:
        assert marker not in production
```

将 `tests/test_user_five_ai_acceptance.py` 中所有 `len(result.sections) == 6` 和固定标题断言改为：

```python
assert result.answer.strip()
assert result.sections == {}
assert "### 分析结论" not in result.answer
```

将 `tests/test_lunar_1999_acceptance.py` 的云端/本地固定六段断言改为：

```python
assert cloud.answer.strip()
assert cloud.sections == {}
assert local.answer.strip()
assert local.sections == {}
```

- [ ] **Step 2: 运行验收测试并确认旧固定六段预期失败**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_acceptance_fixture_isolation.py \
  tests/test_user_five_ai_acceptance.py \
  tests/test_lunar_1999_acceptance.py -q
```

Expected: isolation test PASS；旧验收渲染或固定标题断言 FAIL。

- [ ] **Step 3: 更新离线验收渲染和配置文档**

在 `scripts/run_user_five_ai_acceptance.py` 中让模拟客户端返回自然主回答，并直接输出：

```python
            result = answer_question(
                chart,
                question,
                [],
                config=config,
                client=client,
            )
            lines.extend(
                [
                    f"### Q{index}",
                    "",
                    f"问：{question}",
                    "",
                    "答：",
                    "",
                    result.answer,
                    "",
                    f"来源：{result.source}",
                    "",
                ]
            )
```

把 live 模式缺密钥提示改为：

```python
if live and not config.enabled:
    raise RuntimeError("live mode requires configured Kimi/OpenAI API credentials")
```

更新 `README.md` 的 AI 配置部分：

````markdown
### 本机 Kimi K3

复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml`，
只把自己的 Kimi 开放平台 Key 填入本机文件。真实 secrets 文件已被 Git 忽略。

### 服务器部署

```bash
export MINGSHU_AI_PROVIDER="kimi"
export MOONSHOT_API_KEY="your-server-side-key"
export MINGSHU_AI_MODEL="kimi-k3"
export MINGSHU_AI_BASE_URL="https://api.moonshot.cn/v1"
export MINGSHU_AI_REASONING="high"
```

Kimi 只接收去身份化命盘事实、相关规则、问题和最近六条清理后的对话。
````

重新生成离线验收文件：

```bash
.venv/bin/python scripts/run_user_five_ai_acceptance.py
.venv/bin/python scripts/render_lunar_1999_acceptance.py
```

- [ ] **Step 4: 运行完整测试**

Run:

```bash
.venv/bin/python -m pytest -q
```

Expected: 全部 PASS，且无 warning/error。

- [ ] **Step 5: 验证真实密钥未进入 Git**

Run:

```bash
git status --short
git ls-files .streamlit
git grep -nE 'sk-[A-Za-z0-9_-]{20,}|MOONSHOT_API_KEY = "[^"]{12,}"' -- . \
  ':!*.example' || true
```

Expected:

- `git ls-files .streamlit` 只包含 `.streamlit/secrets.toml.example`。
- 密钥扫描无输出。
- `git status` 只包含本任务预期文件。

- [ ] **Step 6: 在存在本机 secrets 时运行一次显式 Kimi live smoke**

先只检查文件是否存在，不读取或输出内容：

```bash
test -f .streamlit/secrets.toml
```

如果存在，通过 Streamlit 页面发起一个不含姓名和原始出生资料的问题：

```text
请概括这个命盘的财运重点，并给出两条现实建议。
```

Expected:

- 页面来源显示“Kimi 云端分析 · 本地规则校验”。
- 不显示“未配置 AI 服务”。
- 回答不固定六段。
- 回答引用当前命盘事实，不出现其他命例信息。
- 控制台和页面不显示 API Key。

如果文件不存在，跳过 live smoke，并明确记录“代码与离线验收完成，等待用户在本机 secrets 中填入密钥”，不得伪称云端调用成功。

- [ ] **Step 7: 提交**

```bash
git add \
  README.md \
  scripts/run_user_five_ai_acceptance.py \
  acceptance_samples/user_five_ai_acceptance.md \
  acceptance_samples/lunar_1999_acceptance.md \
  tests/test_user_five_ai_acceptance.py \
  tests/test_lunar_1999_acceptance.py \
  tests/test_acceptance_fixture_isolation.py
git commit -m "test: verify isolated Kimi acceptance flow"
```

---

## Final Verification

- [ ] Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
git status --short --branch
```

Expected:

- 全部测试通过。
- `git diff --check` 无输出。
- 工作树干净。
- 默认配置为 Kimi K3。
- 真实密钥没有被跟踪。
- 六个真实命例只存在于测试、验收脚本或验收产物中，生产模块不读取它们。
