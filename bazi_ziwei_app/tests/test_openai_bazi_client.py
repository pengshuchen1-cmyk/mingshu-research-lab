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


class _ProviderError(Exception):
    def __init__(self, message, *, status_code=None, code=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class _ProviderConnectionError(Exception):
    pass


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
    from core.ai_models import CloudBaziAnalysis

    return CloudBaziAnalysis(
        analysis_conclusion="财运需要结合承载能力。",
    )


def test_client_uses_structured_responses_api_without_storage():
    from core.ai_models import AIConfig, CloudBaziAnalysis
    from services.openai_bazi_client import OpenAIBaziClient

    responses = _Responses(parsed=_answer())
    client = OpenAIBaziClient(
        AIConfig("server-key", True, "gpt-5.6-sol", "medium", 30),
        client=_Client(responses),
    )
    result = client.answer(_context())
    call = responses.calls[0]

    assert result.analysis_conclusion
    assert result.chart_evidence == []
    assert result.rule_evidence == []
    assert call["model"] == "gpt-5.6-sol"
    assert call["store"] is False
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text_format"] is CloudBaziAnalysis
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


def test_client_classifies_pydantic_parse_failure_as_retryable_unparseable():
    from pydantic import ValidationError
    from core.ai_models import AIConfig, BaziAIAnswer
    from services.openai_bazi_client import AIServiceError, OpenAIBaziClient

    with pytest.raises(ValidationError) as captured:
        BaziAIAnswer.model_validate(
            {
                "analysis_conclusion": "",
                "chart_evidence": [""],
                "rule_evidence": [""],
                "timing_conditions": [""],
                "practical_advice": [""],
                "uncertainty_limitations": [""],
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
                    "analysis_conclusion": "含有未知字段。",
                    "extra": "not allowed",
                }
            )
        ),
    )

    with pytest.raises(AIServiceError) as captured:
        client.answer(_context())

    assert captured.value.code == "unparseable_response"


def test_openai_prompt_requires_adaptive_answer_and_only_supplied_evidence():
    from services.openai_bazi_client import build_messages

    system_prompt = build_messages(_context())[0]["content"]

    assert "完整自然回答" in system_prompt
    assert "不得固定套用六个栏目" in system_prompt
    assert "不得重新计算四柱" in system_prompt
    assert "仅使用请求中提供" in system_prompt
    assert "不得补充未提供" in system_prompt
    assert "按问题范围自适应回答深度" in system_prompt
    assert "单点问题" in system_prompt
    assert "专题问题" in system_prompt
    assert "长周期问题" in system_prompt
    assert "命盘证据" in system_prompt
    assert "现实建议" in system_prompt
    assert "只返回 analysis_conclusion" in system_prompt
    assert "强弱结论必须原样使用" in system_prompt
