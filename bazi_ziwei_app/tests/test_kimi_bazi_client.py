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
