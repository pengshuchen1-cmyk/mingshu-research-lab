from __future__ import annotations

import pytest


class _Response:
    def __init__(self, parsed, usage=None):
        self.output_parsed = parsed
        if usage is not None:
            self.usage = usage


class _Responses:
    def __init__(self, parsed=None, error=None, usage=None):
        self.parsed = parsed
        self.error = error
        self.usage = usage
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return _Response(self.parsed, self.usage)


class _Client:
    def __init__(self, responses):
        self.responses = responses


class _ProviderError(Exception):
    def __init__(self, message, *, status_code=None, code=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class _ProviderConnectionError(Exception):
    pass


def _context(*, requested_depth="direct"):
    from core.ai_models import (
        AIRequestContext,
        AnalysisPlan,
        ClaimPlan,
        FactItem,
        FactPacket,
        ResolvedQuestion,
    )

    resolved = ResolvedQuestion(
        safe_question="财运如何？",
        domain="wealth",
        requested_depth=requested_depth,
    )
    fact_packet = FactPacket(
        resolved=resolved,
        facts=[
            FactItem(
                id="chart.wealth",
                kind="chart",
                text="财务判断要结合承载能力。",
                source="chart",
            )
        ],
        rule_evidence=[
            {"id": "WEALTH-CAPACITY", "statement": "承财看日主能力"}
        ],
    )
    analysis_plan = AnalysisPlan(
        resolved=resolved,
        claims=[
            ClaimPlan(
                id="wealth.core",
                topic="财务承载",
                allowed_conclusion="财务主题应同时观察机会与承载能力。",
                local_text="财务主题应同时观察机会与承载能力。",
                fact_ids=["chart.wealth"],
                rule_ids=["WEALTH-CAPACITY"],
                conditions=["结合现实现金流核对。"],
                uncertainty=["不保证具体财务结果。"],
                prohibited_expansion=["不得保证结果"],
            )
        ],
    )

    return AIRequestContext(
        question="旧问题字段不应进入云端提示词。",
        category="wealth",
        requires_timing=False,
        chart_facts={"legacy": "旧命盘字段不应进入云端提示词。"},
        rule_evidence=[
            {"id": "LEGACY-RULE", "statement": "旧规则不应进入云端提示词。"}
        ],
        history=[],
        resolved_question=resolved,
        fact_packet=fact_packet,
        analysis_plan=analysis_plan,
    )


def _answer(claim_id="wealth.core"):
    from core.ai_models import CloudBaziAnalysis

    return CloudBaziAnalysis(
        segments=[
            {
                "claim_ids": [claim_id],
                "text": "财运需要结合承载能力。",
            }
        ],
    )


def test_client_uses_structured_responses_api_without_storage():
    from core.ai_models import AIConfig, CloudBaziAnalysis
    from services.openai_bazi_client import OpenAIBaziClient

    usage = type("Usage", (), {"input_tokens": 75, "output_tokens": 45})()
    responses = _Responses(parsed=_answer(), usage=usage)
    client = OpenAIBaziClient(
        AIConfig("server-key", True, "gpt-5.6-sol", "medium", 30),
        client=_Client(responses),
    )
    result = client.answer(_context())
    call = responses.calls[0]

    assert result.analysis.segments[0].claim_ids == ["wealth.core"]
    assert result.analysis.segments[0].text == "财运需要结合承载能力。"
    assert result.input_tokens == 75
    assert result.output_tokens == 45
    assert call["model"] == "gpt-5.6-sol"
    assert call["store"] is False
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text_format"] is CloudBaziAnalysis
    assert call["timeout"] == 30
    assert "server-key" not in str(call)
    serialized = str(call["input"])
    assert "旧问题字段不应进入云端提示词" not in serialized
    assert "旧命盘字段不应进入云端提示词" not in serialized
    assert "旧规则不应进入云端提示词" not in serialized


def test_client_defaults_missing_usage_to_zero():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import OpenAIBaziClient

    result = OpenAIBaziClient(
        AIConfig("server-key", True),
        client=_Client(_Responses(parsed=_answer())),
    ).answer(_context())

    assert result.input_tokens == 0
    assert result.output_tokens == 0


def test_client_leaves_unknown_claim_id_for_segment_guard():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import OpenAIBaziClient

    result = OpenAIBaziClient(
        AIConfig("server-key", True),
        client=_Client(
            _Responses(parsed=_answer("wealth.outside-plan"))
        ),
    ).answer(_context())

    assert result.analysis.segments[0].claim_ids == ["wealth.outside-plan"]


def test_client_wraps_service_and_parse_failures():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    config = AIConfig("server-key", True)
    for responses in (_Responses(parsed=None), _Responses(error=TimeoutError("slow"))):
        client = OpenAIBaziClient(config, client=_Client(responses))
        with pytest.raises(AIServiceError):
            client.answer(_context())


def test_client_classifies_pydantic_parse_failure_as_retryable_unparseable():
    from pydantic import ValidationError
    from core.ai_models import AIConfig, CloudBaziAnalysis
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    with pytest.raises(ValidationError) as captured:
        CloudBaziAnalysis.model_validate(
            {
                "segments": [
                    {
                        "claim_ids": [],
                        "text": "",
                    }
                ],
            }
        )
    responses = _Responses(error=captured.value)
    client = OpenAIBaziClient(AIConfig("server-key", True), client=_Client(responses))

    with pytest.raises(AIServiceError) as captured_service:
        client.answer(_context())

    assert captured_service.value.code == "unparseable_response"


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (_ProviderError("unauthorized", status_code=401), "invalid_credentials"),
        (_ProviderError("forbidden", status_code=403), "invalid_credentials"),
        (
            _ProviderError(
                "requests exhausted",
                status_code=429,
                code="insufficient_quota",
            ),
            "insufficient_quota",
        ),
        (
            _ProviderError(
                "provider message is not used for classification",
                status_code=429,
                code="billing",
            ),
            "insufficient_quota",
        ),
        (_ProviderError("too many requests", status_code=429), "rate_limited"),
        (TimeoutError("provider timed out"), "timeout"),
        (_ProviderConnectionError("connection reset"), "network_error"),
        (_ProviderError("internal error", status_code=500), "service_unavailable"),
        (_ProviderError("bad gateway", status_code=502), "service_unavailable"),
        (_ProviderError("unavailable", status_code=503), "service_unavailable"),
    ],
)
def test_classify_service_error_returns_deterministic_codes(error, expected_code):
    from services.openai_bazi_client import classify_service_error

    assert classify_service_error(error) == expected_code


def test_classify_service_error_recognizes_openai_sdk_timeout():
    import httpx
    from openai import APIConnectionError, APITimeoutError
    from services.openai_bazi_client import classify_service_error

    error = APITimeoutError(
        request=httpx.Request("POST", "https://example.invalid/v1/responses")
    )

    assert isinstance(error, APIConnectionError)
    assert not isinstance(error, TimeoutError)
    assert classify_service_error(error) == "timeout"


def test_non_quota_429_stays_rate_limited_and_non_429_quota_is_not_billing_failure():
    from services.openai_bazi_client import classify_service_error

    assert (
        classify_service_error(
            _ProviderError("rate limit reached", status_code=429, code="rate_limit")
        )
        == "rate_limited"
    )
    assert (
        classify_service_error(
            _ProviderError("insufficient_quota", status_code=500)
        )
        == "service_unavailable"
    )


def test_client_exposes_only_classified_code_not_raw_provider_error():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    raw_message = "invalid token sk-provider-secret"
    client = OpenAIBaziClient(
        AIConfig("server-key", True),
        client=_Client(
            _Responses(error=_ProviderError(raw_message, status_code=401))
        ),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())

    assert captured.value.code == "invalid_credentials"
    assert str(captured.value) == "invalid_credentials"
    assert raw_message not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True


def test_invalid_parsed_object_is_unparseable_response():
    from core.ai_models import AIConfig
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    client = OpenAIBaziClient(
        AIConfig("server-key", True),
        client=_Client(
            _Responses(
                parsed={
                    "segments": [
                        {
                            "claim_ids": ["wealth.core"],
                            "text": "含有未知字段。",
                        }
                    ],
                    "extra": "not allowed",
                }
            )
        ),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())

    assert captured.value.code == "unparseable_response"
