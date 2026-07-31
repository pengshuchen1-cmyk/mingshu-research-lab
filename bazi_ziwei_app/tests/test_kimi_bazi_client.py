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
    def __init__(self, content, finish_reason="stop", usage=None):
        self.choices = [_Choice(content, finish_reason)]
        if usage is not None:
            self.usage = usage


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
        chart_facts={
            "legacy": "旧命盘字段不应进入云端提示词。",
        },
        rule_evidence=[
            {"id": "LEGACY-RULE", "statement": "旧规则不应进入云端提示词。"}
        ],
        history=[],
        resolved_question=resolved,
        fact_packet=fact_packet,
        analysis_plan=analysis_plan,
    )


def _payload(claim_id="wealth.core"):
    return json.dumps(
        {
            "segments": [
                {
                    "claim_ids": [claim_id],
                    "text": "财务重点是承载能力。",
                }
            ],
        },
        ensure_ascii=False,
    )


def test_kimi_client_uses_k3_json_schema_and_deidentified_messages():
    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    usage = type(
        "Usage",
        (),
        {"prompt_tokens": 120, "completion_tokens": 80},
    )()
    completions = _Completions(_Response(_payload(), usage=usage))
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

    assert result.analysis.segments[0].claim_ids == ["wealth.core"]
    assert result.analysis.segments[0].text == "财务重点是承载能力。"
    assert result.input_tokens == 120
    assert result.output_tokens == 80
    assert call["model"] == "kimi-k3"
    assert call["stream"] is False
    assert call["max_completion_tokens"] == 6000
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["name"] == "bazi_cloud_analysis"
    assert call["response_format"]["json_schema"]["strict"] is True
    claim_items = call["response_format"]["json_schema"]["schema"]["$defs"][
        "CloudSegment"
    ]["properties"]["claim_ids"]["items"]
    assert claim_items["enum"] == ["wealth.core"]
    assert call["extra_body"] == {"reasoning_effort": "high"}
    assert call["timeout"] == 30
    serialized = json.dumps(call["messages"], ensure_ascii=False)
    assert "财运如何" in serialized
    assert "承财看日主能力" in serialized
    assert "旧问题字段不应进入云端提示词" not in serialized
    assert "旧命盘字段不应进入云端提示词" not in serialized
    assert "旧规则不应进入云端提示词" not in serialized
    assert "moonshot-secret" not in serialized


def test_kimi_client_defaults_missing_usage_to_zero():
    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    result = KimiBaziClient(
        AIConfig("key", True),
        client=_Client(_Completions(_Response(_payload()))),
    ).answer(_context())

    assert result.input_tokens == 0
    assert result.output_tokens == 0


def test_kimi_client_leaves_unknown_claim_id_for_segment_guard():
    from core.ai_models import AIConfig
    from services.kimi_bazi_client import KimiBaziClient

    result = KimiBaziClient(
        AIConfig("key", True),
        client=_Client(
            _Completions(_Response(_payload("wealth.outside-plan")))
        ),
    ).answer(_context())

    assert result.analysis.segments[0].claim_ids == ["wealth.outside-plan"]


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
            "max_retries": 0,
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
