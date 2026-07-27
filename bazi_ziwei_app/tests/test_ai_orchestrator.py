from __future__ import annotations

import pytest


class _FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.contexts = []

    def answer(self, context):
        self.contexts.append(context)
        item = self.answers.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_orchestrator_builds_configured_provider_when_client_not_injected(monkeypatch):
    import core.ai_orchestrator as orchestrator
    from core.ai_models import AIConfig

    fake = _FakeClient([_answer("壬日主的财务重点是现金流。", "壬日主")])
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
    assert result.provider == "kimi"


def test_unknown_disabled_provider_returns_service_unavailable_not_missing_key():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("", False, provider="unknown"),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "service_unavailable"


def test_unexpected_client_construction_error_returns_safe_complete_fallback(
    monkeypatch,
):
    import core.ai_orchestrator as orchestrator
    from core.ai_models import AIConfig

    def _explode(_config):
        raise RuntimeError("constructor leaked sk-secret and provider internals")

    monkeypatch.setattr(orchestrator, "build_ai_client", _explode)

    result = orchestrator.answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True, provider="kimi"),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "service_unavailable"
    assert result.answer.strip()
    assert "constructor leaked" not in result.answer


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
    )


def _answer(
    text,
    evidence,
    rule_evidence="财运承载需结合日主强弱、印比支持与食伤生财路径判断。",
):
    from core.ai_models import BaziAIAnswer

    return BaziAIAnswer(
        analysis_conclusion=text,
        chart_evidence=[evidence],
        rule_evidence=[rule_evidence],
        timing_conditions=["具体阶段需结合流年事实观察。"],
        practical_advice=["先核对现金流，再决定行动。"],
        uncertainty_limitations=["现实结果取决于执行，不替代财务决策。"],
    )


def test_orchestrator_does_not_retry_after_guard_rejection():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient(
        [
            _answer("乙巳日主肯定发财。", "日柱乙巳"),
            _answer("丙午日主一定会发财。", "日柱丙午"),
        ]
    )
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.sections == {}
    assert result.answer.strip()
    assert result.timing_conditions
    assert result.practical_advice
    assert result.degraded_reason == "local_validation_failed"
    assert len(fake.contexts) == 1


def test_orchestrator_uses_local_rules_when_cloud_disabled():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient([])
    result = answer_question(
        _chart(),
        "她现在结婚了吗？",
        [],
        config=AIConfig("", False),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.sections == {}
    assert result.answer.strip()
    assert result.timing_conditions
    assert result.practical_advice
    assert result.degraded_reason == "missing_api_key"
    assert len(fake.contexts) == 0
    assert "单凭八字，不能确认现实中的婚姻登记状态。" in result.answer
    assert "但如果一定要根据命盘作倾向判断：" in result.answer
    assert "我更偏向" in result.answer
    assert "仍需以本人现实情况为准" in result.answer


def test_missing_api_key_returns_complete_wealth_fallback_with_exact_reason():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("", False),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert result.sections == {}
    assert result.answer.strip()


def test_orchestrator_does_not_retry_malformed_structured_output():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from services.openai_bazi_client import AIServiceError

    fake = _FakeClient(
        [
            AIServiceError("unparseable_response"),
            _answer("壬日主的财务重点是承载能力和现金流。", "壬日主"),
        ]
    )
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "unparseable_response"
    assert len(fake.contexts) == 1


@pytest.mark.parametrize(
    "error_code",
    [
        "insufficient_quota",
        "invalid_credentials",
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
    ],
)
def test_orchestrator_preserves_service_error_reason_without_retry(error_code):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from services.openai_bazi_client import AIServiceError

    fake = _FakeClient([AIServiceError(error_code)])
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == error_code
    assert result.sections == {}
    assert result.answer.strip()
    assert len(fake.contexts) == 1


def test_orchestrator_returns_unparseable_reason_after_one_call():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from services.openai_bazi_client import AIServiceError

    fake = _FakeClient(
        [
            AIServiceError("unparseable_response"),
            AIServiceError("unparseable_response"),
        ]
    )
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "unparseable_response"
    assert len(fake.contexts) == 1


def test_orchestrator_returns_validation_reason_after_one_guard_rejection():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient(
        [
            _answer("乙巳日主肯定发财。", "日柱乙巳"),
            _answer("丙午日主一定会发财。", "日柱丙午"),
        ]
    )
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "local_validation_failed"
    assert len(fake.contexts) == 1


def test_cloud_rule_paraphrase_is_replaced_by_local_evidence():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient(
        [
            _answer(
                "壬日主身强，财务重点是承载能力、现金流和风险边界。",
                "云端自行改写、不能逐字映射的命盘证据",
                "云端自行改写、不能逐字映射的规则证据",
            )
        ]
    )

    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "cloud_validated"
    assert result.degraded_reason is None
    assert len(fake.contexts) == 1
    assert result.chart_evidence
    assert result.rule_evidence
    assert all("云端自行改写" not in item for item in result.chart_evidence)
    assert all("云端自行改写" not in item for item in result.rule_evidence)


def test_cloud_strength_contradiction_is_still_rejected_once():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient(
        [
            _answer(
                "壬日主身弱，财务重点是先控制风险。",
                "云端证据",
            ),
            _answer("壬日主身强。", "第二次不应被读取"),
        ]
    )

    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "local_validation_failed"
    assert len(fake.contexts) == 1


def test_orchestrator_does_not_expose_raw_unexpected_exception():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient([RuntimeError("provider leaked secret details")])
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=fake,
    )

    assert result.degraded_reason == "service_unavailable"
    assert "provider leaked secret details" not in result.answer
    assert len(fake.contexts) == 1


@pytest.mark.parametrize(
    "question",
    [
        "房贷要注意什么？",
        "按揭买房可以吗？",
        "借钱创业可以吗？",
    ],
)
def test_borrowing_synonym_fallback_has_complete_risk_advice(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        question,
        [],
        config=AIConfig("", False),
    )
    advice = "。".join(result.practical_advice)

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert result.sections == {}
    assert result.answer.strip()
    for required in ("现金流", "最坏情景", "还款", "退出"):
        assert required in advice
    assert "一定能" not in result.answer
    assert "保证成功" not in result.answer


@pytest.mark.parametrize(
    "question",
    [
        "她是否已婚？",
        "她已婚了吗？",
        "现在是未婚还是已婚？",
    ],
)
def test_current_marriage_variant_fallback_cannot_confirm_status(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    chart = _chart()
    relationship_summary = chart["facts"]["relationship"]["summary"]
    result = answer_question(
        chart,
        question,
        [],
        config=AIConfig("", False),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert "单凭八字，不能确认现实中的婚姻登记状态。" in result.answer
    assert "但如果一定要根据命盘作倾向判断：" in result.answer
    assert "我更偏向" in result.answer
    assert relationship_summary in result.answer
    assert "仍需以本人现实情况为准" in result.answer
    assert any("关系状态的倾向判断" in item for item in result.timing_conditions)
    assert any(
        "不代表确定已婚或未婚" in item
        for item in result.uncertainty
    )


@pytest.mark.parametrize(
    ("birth_date", "birth_hour", "expected_polarity", "expected_tendency"),
    [
        (
            "1996-09-04",
            23,
            "support",
            "更偏向已经结婚，或者至少曾有过一段接近婚姻的长期正式关系",
        ),
        (
            "1993-04-05",
            20,
            "pressure",
            "更偏向目前未必处于稳定婚姻中，或曾有关系但经历明显波折",
        ),
        (
            "1994-09-23",
            18,
            "mixed",
            "现有中性信号不足以让某一现实状态显著更可能",
        ),
    ],
)
def test_canonical_relationship_polarity_drives_end_to_end_local_tendency(
    birth_date,
    birth_hour,
    expected_polarity,
    expected_tendency,
):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from core.bazi_engine import build_bazi_chart

    chart = build_bazi_chart(
        {
            "gender": "女",
            "birth_date": birth_date,
            "birth_hour": birth_hour,
            "birth_minute": 0,
        }
    )

    result = answer_question(
        chart,
        "她是否已婚？",
        [],
        config=AIConfig("", False),
    )

    assert (
        chart["facts"]["relationship"]["stability_signals"][0]["polarity"]
        == expected_polarity
    )
    assert expected_tendency in result.answer


def test_old_attached_relationship_facts_without_polarity_stay_neutral():
    from copy import deepcopy

    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    chart = deepcopy(_chart())
    chart["facts"]["relationship"].pop("stability_signals", None)
    chart["facts"]["relationship"]["summary"] = (
        "未见明显波折，但配偶星有力不足。"
    )

    result = answer_question(
        chart,
        "她是否已婚？",
        [],
        config=AIConfig("", False),
    )

    assert "现有中性信号不足以让某一现实状态显著更可能" in result.answer


def test_current_timing_wording_only_appears_when_timing_facts_are_supplied():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import chart_facts_from_chart
    from core.local_bazi_answer import build_local_answer

    chart = build_bazi_chart(
        {
            "gender": "女",
            "birth_date": "1996-09-04",
            "birth_hour": 23,
            "birth_minute": 45,
        }
    )
    facts = chart_facts_from_chart(chart)
    untimed = build_local_answer(build_ai_context(facts, "她是否已婚？", []))
    timed = build_local_answer(build_ai_context(facts, "今年她是否已婚？", []))

    assert "当前时运" not in untimed.analysis_conclusion
    assert "结合本盘提供的关系结构与稳定条件" in untimed.analysis_conclusion
    assert "当前时运" in timed.analysis_conclusion


@pytest.mark.parametrize(
    ("enabled", "service_error", "expected_reason"),
    [
        (False, None, "missing_api_key"),
        (True, "network_error", "network_error"),
    ],
)
def test_long_attached_wealth_fact_still_returns_bounded_local_fallback(
    enabled,
    service_error,
    expected_reason,
):
    from copy import deepcopy

    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from services.openai_bazi_client import AIServiceError

    chart = deepcopy(_chart())
    chart["facts"]["wealth"]["summary"] = "保留-wealth-" + ("长" * 3200)
    client = (
        _FakeClient([AIServiceError(service_error)])
        if service_error
        else None
    )

    result = answer_question(
        chart,
        "财运如何？",
        [],
        config=AIConfig("key" if enabled else "", enabled),
        client=client,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == expected_reason
    assert result.sections == {}
    assert "保留-wealth-" in result.answer
    assert len(result.answer) <= 6000


def test_orchestrator_uses_attached_facts_even_when_legacy_fields_are_poisoned():
    from copy import deepcopy
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    chart = _chart()
    poisoned = deepcopy(chart)
    poisoned["day_master"] = "庚"
    poisoned["day_master_strength"] = {"strength": "从旺"}
    poisoned["pattern_analysis"] = {"plain_text": "七杀格"}
    poisoned["wealth_analysis"] = {"public_text": "旧财富"}
    poisoned["relationship_analysis"] = {"public_text": "旧姻缘"}

    result = answer_question(
        poisoned,
        "请概括命盘",
        [],
        config=AIConfig("", False),
    )

    assert "壬日主" not in result.answer or poisoned["facts"]["day_master"] == "壬"
    assert poisoned["facts"]["day_master"] == "壬"
    assert "七杀格" not in result.answer
    assert "旧财富" not in result.answer
    assert "旧姻缘" not in result.answer
