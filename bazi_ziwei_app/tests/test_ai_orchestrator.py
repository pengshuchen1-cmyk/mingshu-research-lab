from __future__ import annotations


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


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
    )


def _answer(text, evidence):
    from core.ai_models import BaziAIAnswer

    return BaziAIAnswer(
        answer=text,
        chart_evidence=[evidence],
        rule_evidence=["财运承载需结合日主强弱、印比支持与食伤生财路径判断。"],
        uncertainty=["现实结果取决于执行"],
        cautions=["不替代财务决策"],
    )


def test_orchestrator_retries_once_after_guard_rejection():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    fake = _FakeClient(
        [
            _answer("乙巳日主肯定发财。", "日柱乙巳"),
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

    assert result.source == "cloud_validated"
    assert len(fake.contexts) == 2
    assert "纠正要求" in fake.contexts[1].question


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
    assert len(fake.contexts) == 0
    assert "不能确认当前是否已婚" in result.answer


def test_orchestrator_retries_once_for_malformed_structured_output():
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

    assert result.source == "cloud_validated"
    assert len(fake.contexts) == 2
