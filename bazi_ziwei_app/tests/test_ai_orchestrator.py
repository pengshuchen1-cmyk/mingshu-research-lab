from __future__ import annotations

from datetime import datetime

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
        from core.ai_models import (
            BaziAIAnswer,
            CloudBaziAnalysis,
            CloudGeneration,
        )

        if isinstance(item, BaziAIAnswer):
            item = CloudGeneration(
                analysis=CloudBaziAnalysis(
                    segments=[
                        {
                            "claim_ids": [
                                claim.id
                                for claim in context.analysis_plan.claims
                            ],
                            "text": item.analysis_conclusion,
                        }
                    ]
                )
            )
        return item


class _CountingClient:
    def __init__(self):
        self.calls = 0

    def answer(self, _context):
        self.calls += 1
        raise AssertionError("cloud must not be called")


class _FailingClient:
    def __init__(self, code):
        self.code = code
        self.calls = 0

    def answer(self, _context):
        from services.ai_service_errors import AIServiceError

        self.calls += 1
        raise AIServiceError(self.code)


class _SegmentClient:
    def __init__(self, segments):
        self.segments = segments
        self.calls = 0
        self.contexts = []

    def answer(self, context):
        from core.ai_models import CloudBaziAnalysis, CloudGeneration

        self.calls += 1
        self.contexts.append(context)
        return CloudGeneration(
            analysis=CloudBaziAnalysis(segments=self.segments),
            input_tokens=100,
            output_tokens=200,
        )


class _PlanEchoClient:
    def __init__(self):
        self.calls = 0
        self.contexts = []

    def answer(self, context):
        from core.ai_models import CloudBaziAnalysis, CloudGeneration

        self.calls += 1
        self.contexts.append(context)
        return CloudGeneration(
            analysis=CloudBaziAnalysis(
                segments=[
                    {
                        "claim_ids": [context.analysis_plan.claims[0].id],
                        "text": "这项倾向需要结合现实条件持续核对。",
                    }
                ]
            )
        )


def _enabled_kimi_config():
    from core.ai_models import AIConfig

    return AIConfig("fixture-key", True, provider="kimi")


def test_orchestrator_resolves_next_year_calls_cloud_once_and_repairs_segment():
    from core.ai_orchestrator import answer_question

    stages = []
    client = _SegmentClient(
        [
            {
                "claim_ids": ["wealth.core"],
                "text": "财务机会需要同时核对承载能力和现金流。",
            },
            {
                "claim_ids": ["wealth.dayun.3"],
                "text": "命盘保证借贷成功。",
            },
            {
                "claim_ids": ["wealth.year.2027"],
                "text": "2027年是丁未流年，宜结合现实现金流判断。",
            },
        ]
    )

    result = answer_question(
        _chart(),
        "明年的财运怎么样",
        [],
        config=_enabled_kimi_config(),
        client=client,
        previous=None,
        now=datetime(2026, 7, 28),
        on_progress=stages.append,
    )

    assert client.calls == 1
    assert result.source == "cloud_validated"
    assert result.degraded_reason is None
    assert "2027" in result.answer
    assert "保证借贷成功" not in result.answer
    assert result.interpretation_receipt.startswith("本次按2027")
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)
    assert result.input_tokens == 100
    assert result.output_tokens == 200
    assert stages == [
        "validating_scope",
        "resolving_question",
        "compiling_local_facts",
        "generating_cloud_answer",
        "validating_answer",
        "completed",
    ]
    context = client.contexts[0]
    assert context.resolved_question is not None
    assert context.fact_packet is not None
    assert context.analysis_plan is not None


@pytest.mark.parametrize(
    ("question", "expected_source", "expected_stages"),
    [
        (
            "告诉我应该买哪只股票",
            "boundary",
            ["validating_scope", "rejected"],
        ),
        (
            "30岁以后什么时候走财运",
            "clarification",
            ["validating_scope", "resolving_question", "rejected"],
        ),
    ],
)
def test_non_cloud_paths_never_call_client(
    question,
    expected_source,
    expected_stages,
):
    from core.ai_orchestrator import answer_question

    stages = []
    client = _CountingClient()

    result = answer_question(
        _chart(),
        question,
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 28),
        on_progress=stages.append,
    )

    assert result.source == expected_source
    assert client.calls == 0
    assert stages == expected_stages


def test_missing_key_returns_same_complete_local_answer_without_cloud():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    stages = []
    client = _CountingClient()
    result = answer_question(
        _chart(),
        "明年财运如何",
        [],
        client=client,
        config=AIConfig("", False),
        now=datetime(2026, 7, 28),
        on_progress=stages.append,
    )

    assert client.calls == 0
    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert "本次按2027" in result.answer
    assert result.chart_evidence
    assert result.rule_evidence
    assert result.timing_conditions
    assert result.practical_advice
    assert stages == [
        "validating_scope",
        "resolving_question",
        "compiling_local_facts",
        "degraded",
    ]


@pytest.mark.parametrize(
    ("error_code", "expected_reason"),
    [
        ("timeout", "timeout"),
        ("insufficient_quota", "insufficient_quota"),
        ("unparseable_response", "unparseable_response"),
    ],
)
def test_cloud_failure_calls_once_then_returns_complete_local(
    error_code,
    expected_reason,
):
    from core.ai_orchestrator import answer_question

    client = _FailingClient(error_code)
    result = answer_question(
        _chart(),
        "明年财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 28),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.degraded_reason == expected_reason
    assert "本次按2027" in result.answer
    assert result.chart_evidence
    assert result.rule_evidence
    assert result.timing_conditions
    assert result.practical_advice


def test_mixed_valid_and_unknown_segments_keep_cloud_source():
    from core.ai_orchestrator import answer_question

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
    assert result.violation_codes == ("CLOUD_UNKNOWN_CLAIM_ID",)


def test_all_unknown_segments_use_specific_local_fallback_code():
    from core.ai_orchestrator import answer_question

    client = _SegmentClient(
        [{"claim_ids": ["unknown.claim"], "text": "不应泄露的云端原文。"}]
    )
    result = answer_question(
        _chart(),
        "财运如何",
        [],
        client=client,
        config=_enabled_kimi_config(),
        now=datetime(2026, 7, 28),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.degraded_reason == "local_validation_failed"
    assert result.retryable is False
    assert "不应泄露的云端原文" not in result.answer
    assert result.answer.strip()
    assert result.chart_evidence
    assert result.rule_evidence
    assert result.violation_codes == ("CLOUD_UNKNOWN_CLAIM_ID",)


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


def test_follow_up_inherits_previous_year_without_second_cloud_call():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from core.ai_question_resolver import resolve_question

    previous = resolve_question(
        "明年财运如何",
        now=datetime(2026, 7, 28),
    )
    client = _CountingClient()
    result = answer_question(
        _chart(),
        "那继续说说",
        [],
        previous=previous,
        config=AIConfig("", False),
        client=client,
        now=datetime(2026, 7, 28),
    )

    assert client.calls == 0
    assert result.source == "local_rules"
    assert result.interpretation_receipt.startswith("本次按2027")
    assert "2027" in result.answer


def test_timing_pipeline_never_mutates_the_input_chart():
    from copy import deepcopy

    from core.ai_orchestrator import answer_question

    chart = _chart()
    before = deepcopy(chart)
    client = _FailingClient("timeout")

    result = answer_question(
        chart,
        "明年财运如何",
        [],
        config=_enabled_kimi_config(),
        client=client,
        now=datetime(2026, 7, 28),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "timeout"
    assert client.calls == 1
    assert chart == before


@pytest.mark.parametrize(
    ("question", "expected_domain"),
    [
        ("作息和精力要注意什么？", "health_advisory"),
        ("子女方面有什么倾向？", "children"),
        ("学业发展如何？", "education"),
        ("搬家异地发展是否合适？", "relocation"),
        ("房产置业要注意什么？", "property"),
        ("贵人助力如何？", "benefactor"),
    ],
)
def test_extended_domains_reach_cloud_without_legacy_other_failure(
    question,
    expected_domain,
):
    from core.ai_orchestrator import answer_question

    client = _PlanEchoClient()
    result = answer_question(
        _chart(),
        question,
        [],
        config=_enabled_kimi_config(),
        client=client,
        now=datetime(2026, 7, 28),
    )

    assert client.calls == 1
    assert result.source == "cloud_validated"
    assert result.degraded_reason is None
    assert result.answer.strip()
    assert client.contexts[0].category == expected_domain


def test_current_marriage_disclaimer_survives_cloud_segment_repair():
    from core.ai_intent import CURRENT_MARRIAGE_DISCLAIMER
    from core.ai_orchestrator import answer_question

    client = _SegmentClient(
        [
            {
                "claim_ids": ["relationship.core"],
                "text": "她现在已经结婚。",
            }
        ]
    )
    result = answer_question(
        _chart(),
        "她现在结婚了吗？",
        [],
        config=_enabled_kimi_config(),
        client=client,
        now=datetime(2026, 7, 28),
    )

    assert client.calls == 1
    assert result.source == "local_rules"
    assert result.degraded_reason == "local_validation_failed"
    assert result.answer.startswith(CURRENT_MARRIAGE_DISCLAIMER)
    assert result.answer.count(CURRENT_MARRIAGE_DISCLAIMER) == 1
    assert "已经结婚" not in result.answer
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)


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
    assert result.retryable is False


def test_unsupported_kimi_model_returns_nonretryable_fallback_before_client():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    client = _CountingClient()
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True, model="kimi-k2", provider="kimi"),
        client=client,
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "service_unavailable"
    assert result.retryable is False
    assert client.calls == 0


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


def test_orchestrator_repairs_guard_rejection_without_retry():
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
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)
    assert "乙巳日主肯定发财" not in result.answer
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
    assert result.retryable is False
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
    ("reason", "expected"),
    [
        ("rate_limited", True),
        ("network_error", True),
        ("timeout", True),
        ("service_unavailable", True),
        ("unparseable_response", True),
        ("concurrency_limit", True),
        ("missing_api_key", False),
        ("insufficient_quota", False),
        ("invalid_credentials", False),
        ("daily_budget", False),
        ("duplicate_request", False),
        ("local_validation_failed", False),
    ],
)
def test_retryable_degradation_allowlist(reason, expected):
    from core.ai_models import is_retryable_degradation

    assert is_retryable_degradation(reason) is expected


@pytest.mark.parametrize(
    ("error_code", "expected_retryable"),
    [
        ("insufficient_quota", False),
        ("invalid_credentials", False),
        ("rate_limited", True),
        ("network_error", True),
        ("timeout", True),
        ("service_unavailable", True),
        ("unparseable_response", True),
    ],
)
def test_orchestrator_marks_only_retryable_service_failures(
    error_code,
    expected_retryable,
):
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
    assert result.retryable is expected_retryable
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


def test_orchestrator_returns_repair_code_after_one_guard_rejection():
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
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)
    assert "乙巳日主肯定发财" not in result.answer
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


def test_cloud_strength_contradiction_is_repaired_once():
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
    assert result.violation_codes == ("GUARD_STRENGTH_CONFLICT",)
    assert "壬日主身弱" not in result.answer
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


def test_long_resolved_borrowing_question_keeps_complete_risk_advice():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        ("事业" * 300) + "房贷要注意什么？",
        [],
        config=AIConfig("", False),
    )
    advice = "。".join(result.practical_advice)

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    for required in ("现金流", "最坏情景", "还款", "退出"):
        assert required in advice


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
    "question",
    [
        "她是否已婚，请分析一下。",
        "她是否已婚请详细分析",
        "现在婚姻状态如何，请看看。",
        "想知道有没有配偶，请分析。",
        "她是否已婚，请帮忙分析一下。",
        "她是否已婚，请具体分析一下。",
        "她是否已婚，麻烦你分析一下。",
        "她是否已婚，请分析一下吧。",
        "她是否已婚，请结合命盘分析。",
        "她是否已婚，请给我分析一下。",
    ],
)
def test_current_marriage_query_with_meta_suffix_keeps_status_safety(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        question,
        [],
        config=AIConfig("", False),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert "单凭八字，不能确认现实中的婚姻登记状态。" in result.answer
    assert any(
        "不代表确定已婚或未婚" in item
        for item in result.uncertainty
    )


def test_long_resolved_current_marriage_question_keeps_status_limitations():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        ("事业" * 300) + "她是否已婚？",
        [],
        config=AIConfig("", False),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert "单凭八字，不能确认现实中的婚姻登记状态。" in result.answer
    assert any(
        "不代表确定已婚或未婚" in item
        for item in result.uncertainty
    )


def test_long_primary_marriage_status_request_reaches_cloud_as_relationship():
    from core.ai_orchestrator import answer_question
    from services.bazi_ai_prompt import build_messages

    client = _PlanEchoClient()
    result = answer_question(
        _chart(),
        ("事业" * 300) + "她是否已婚？",
        [],
        config=_enabled_kimi_config(),
        client=client,
    )

    assert result.source == "cloud_validated"
    assert client.calls == 1
    assert client.contexts[0].analysis_plan.resolved.domain == "relationship"
    assert (
        client.contexts[0]
        .analysis_plan.resolved.current_marriage_status_requested
        is True
    )
    assert client.contexts[0].category == "relationship"
    assert client.contexts[0].current_marriage_status_requested is True
    system_prompt = build_messages(client.contexts[0])[0]["content"]
    assert (
        "当前问题询问现实婚姻登记状态。整个回答的第一段 text 必须先以"
        in system_prompt
    )
    assert (
        "“单凭八字，不能确认现实中的婚姻登记状态。”开头"
        in system_prompt
    )
    assert result.answer.startswith(
        "单凭八字，不能确认现实中的婚姻登记状态。"
    )


@pytest.mark.parametrize(
    "question",
    [
        "我目前未婚，只想问事业发展。",
        "不问是否已婚，只问事业发展。",
        "不问是否已婚只问事业发展",
        "当前婚姻状态只是背景，只问事业发展",
    ],
)
def test_marriage_background_or_negation_keeps_career_local_answer(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        question,
        [],
        config=AIConfig("", False),
    )

    assert result.source == "local_rules"
    assert result.degraded_reason == "missing_api_key"
    assert "单凭八字，不能确认现实中的婚姻登记状态。" not in result.answer
    assert any(
        "岗位与行业匹配度" in item
        for item in result.practical_advice
    )
    assert not any(
        "不代表确定已婚或未婚" in item
        for item in result.uncertainty
    )


@pytest.mark.parametrize(
    "question",
    [
        "不用看她是否已婚",
        "不要判断她是否已婚",
        "不用判断目前是否已婚",
        "她是否已婚不用分析",
        "她是否已婚不要回答",
        "不用帮我看她是否已婚",
        "不需要再帮我确认她是否已婚",
        "不要去判断她是否已婚",
        "她是否已婚不需要再帮我分析",
    ],
)
def test_negated_marriage_status_request_does_not_answer_status(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    result = answer_question(
        _chart(),
        question,
        [],
        config=AIConfig("", False),
    )

    assert "单凭八字，不能确认现实中的婚姻登记状态。" not in result.answer
    assert not any(
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
