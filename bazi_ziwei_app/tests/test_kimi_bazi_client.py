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


class _ProviderError(Exception):
    def __init__(self, message, *, status_code=None, code=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class _ProviderConnectionError(Exception):
    pass


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
    from core.ai_models import AIConfig, BaziAIAnswer
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
    assert call["max_completion_tokens"] == 4000
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["name"] == "bazi_ai_answer"
    assert call["response_format"]["json_schema"]["strict"] is True
    assert call["response_format"]["json_schema"]["schema"] == BaziAIAnswer.model_json_schema()
    assert call["extra_body"] == {"reasoning_effort": "high"}
    assert call["timeout"] == 30
    serialized = json.dumps(call["messages"], ensure_ascii=False)
    assert "财运如何" in serialized
    assert "承财看日主能力" in serialized
    assert "moonshot-secret" not in serialized


def test_kimi_client_constructs_sdk_with_moonshot_key_and_base_url(monkeypatch):
    import openai

    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    calls = []

    class _OpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(openai, "OpenAI", _OpenAI)
    client = KimiBaziClient(
        AIConfig(
            "moonshot-secret",
            True,
            "kimi-k3",
            "high",
            30,
            "kimi",
            "https://api.moonshot.cn/v1",
        )
    )

    assert calls == [
        {
            "api_key": "moonshot-secret",
            "base_url": "https://api.moonshot.cn/v1",
        }
    ]
    assert "moonshot-secret" not in str(client)
    assert "moonshot-secret" not in repr(client)


def test_kimi_client_rejects_non_k3_model_before_request():
    from core.ai_models import AIConfig
    from services.ai_service_errors import AIServiceError
    from services.kimi_bazi_client import KimiBaziClient

    completions = _Completions(_Response(_payload()))
    client = KimiBaziClient(
        AIConfig("moonshot-secret", True, "kimi-k2"),
        client=_Client(completions),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())

    assert captured.value.code == "service_unavailable"
    assert str(captured.value) == "service_unavailable"
    assert "moonshot-secret" not in str(captured.value)
    assert completions.calls == []


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


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (_ProviderError("raw key moonshot-secret", status_code=401), "invalid_credentials"),
        (_ProviderError("raw key moonshot-secret", status_code=403), "invalid_credentials"),
        (
            _ProviderError(
                "raw key moonshot-secret",
                status_code=429,
                code="billing",
            ),
            "insufficient_quota",
        ),
        (
            _ProviderError(
                "raw key moonshot-secret",
                status_code=429,
                code="rate_limit",
            ),
            "rate_limited",
        ),
        (TimeoutError("raw key moonshot-secret"), "timeout"),
        (_ProviderConnectionError("raw key moonshot-secret"), "network_error"),
        (
            _ProviderError("raw key moonshot-secret", status_code=503),
            "service_unavailable",
        ),
    ],
)
def test_kimi_client_normalizes_provider_errors_without_raw_details(
    error,
    expected_code,
):
    from core.ai_models import AIConfig
    from services.ai_service_errors import AIServiceError
    from services.kimi_bazi_client import KimiBaziClient

    client = KimiBaziClient(
        AIConfig("moonshot-secret", True),
        client=_Client(_Completions(error=error)),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())

    assert captured.value.code == expected_code
    assert str(captured.value) == expected_code
    assert "moonshot-secret" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True
