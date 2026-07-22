from __future__ import annotations

import pytest


class _Response:
    def __init__(self, parsed):
        self.output_parsed = parsed


class _Responses:
    def __init__(self, parsed=None, error=None):
        self.parsed = parsed
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return _Response(self.parsed)


class _Client:
    def __init__(self, responses):
        self.responses = responses


def _context():
    from core.ai_models import AIRequestContext

    return AIRequestContext(
        question="财运如何？",
        category="wealth",
        requires_timing=False,
        chart_facts={"pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "day_master": "丙"},
        rule_evidence=[{"id": "WEALTH-CAPACITY", "statement": "承财看日主能力"}],
        history=[],
    )


def _answer():
    from core.ai_models import BaziAIAnswer

    return BaziAIAnswer(
        answer="财运需要结合承载能力。",
        chart_evidence=["丙日主"],
        rule_evidence=["承财看日主能力"],
        uncertainty=[],
        cautions=["不保证投资结果"],
    )


def test_client_uses_structured_responses_api_without_storage():
    from core.ai_models import AIConfig, BaziAIAnswer
    from services.openai_bazi_client import OpenAIBaziClient

    responses = _Responses(parsed=_answer())
    client = OpenAIBaziClient(
        AIConfig("server-key", True, "gpt-5.6-sol", "medium", 30),
        client=_Client(responses),
    )
    result = client.answer(_context())
    call = responses.calls[0]

    assert result.answer
    assert call["model"] == "gpt-5.6-sol"
    assert call["store"] is False
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text_format"] is BaziAIAnswer
    assert call["timeout"] == 30
    assert "server-key" not in str(call)


def test_client_wraps_service_and_parse_failures():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    config = AIConfig("server-key", True)
    for responses in (_Responses(parsed=None), _Responses(error=TimeoutError("slow"))):
        client = OpenAIBaziClient(config, client=_Client(responses))
        with pytest.raises(AIServiceError):
            client.answer(_context())
