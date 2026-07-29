from __future__ import annotations

from types import SimpleNamespace


def test_request_controller_blocks_duplicate_rate_and_budget():
    from core.ai_request_control import AIRequestController

    controller = AIRequestController(
        per_minute=2,
        daily_requests=3,
        daily_tokens=1000,
        max_concurrent=1,
    )
    first = controller.preflight("session-a", "request-1")
    assert first.allowed is True
    duplicate = controller.preflight("session-a", "request-1")
    assert duplicate.allowed is False
    assert duplicate.reason == "duplicate_request"
    controller.record_usage("request-1", input_tokens=600, output_tokens=500)
    controller.release("request-1")
    blocked = controller.preflight("session-a", "request-2")
    assert blocked.allowed is False
    assert blocked.reason == "daily_budget"


def test_request_controller_enforces_concurrency_and_session_rate_limits():
    from core.ai_request_control import AIRequestController

    controller = AIRequestController(
        per_minute=1,
        daily_requests=1,
        daily_tokens=1000,
        max_concurrent=1,
    )
    assert controller.preflight("session-a", "request-1").allowed is True

    concurrent = controller.preflight("session-b", "request-2")
    assert concurrent.allowed is False
    assert concurrent.reason == "concurrency_limit"

    controller.release("request-1")
    rate_limited = controller.preflight("session-a", "request-3")
    assert rate_limited.allowed is False
    assert rate_limited.reason == "rate_limited"


def test_ai_config_exposes_safe_request_control_defaults():
    from core.ai_models import AIConfig

    config = AIConfig("", False)

    assert config.per_session_per_minute == 3
    assert config.per_session_daily_requests == 30
    assert config.daily_token_budget == 500_000
    assert config.max_concurrent_requests == 4


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {
            "gender": "男",
            "birth_date": "1994-09-23",
            "birth_hour": 18,
            "birth_minute": 0,
        }
    )


class _ControllerSpy:
    def __init__(self, *, allowed: bool = True, reason: str = ""):
        self.allowed = allowed
        self.reason = reason
        self.preflights = []
        self.usages = []
        self.releases = []

    def preflight(self, session_id, request_id):
        self.preflights.append((session_id, request_id))
        return SimpleNamespace(allowed=self.allowed, reason=self.reason)

    def record_usage(self, request_id, *, input_tokens, output_tokens):
        self.usages.append((request_id, input_tokens, output_tokens))

    def release(self, request_id):
        self.releases.append(request_id)


class _TokenClient:
    def __init__(self):
        self.calls = 0

    def answer(self, context):
        from core.ai_models import CloudBaziAnalysis, CloudGeneration

        self.calls += 1
        return CloudGeneration(
            analysis=CloudBaziAnalysis(
                segments=[
                    {
                        "claim_ids": [context.analysis_plan.claims[0].id],
                        "text": "财务倾向需要结合现实现金流持续核对。",
                    }
                ]
            ),
            input_tokens=120,
            output_tokens=80,
        )


class _FailingClient:
    def answer(self, _context):
        raise RuntimeError("cloud failure")


def test_orchestrator_rejection_does_not_construct_cloud_client(monkeypatch):
    import core.ai_orchestrator as orchestrator
    from core.ai_models import AIConfig

    controller = _ControllerSpy(allowed=False, reason="daily_budget")
    constructed = []
    monkeypatch.setattr(
        orchestrator,
        "build_ai_client",
        lambda _config: constructed.append(True),
    )

    result = orchestrator.answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        request_controller=controller,
        session_id="session-a",
        request_id="request-1",
    )

    assert result.degraded_reason == "daily_budget"
    assert constructed == []
    assert controller.releases == []


def test_orchestrator_records_cloud_tokens_and_releases_allowed_request():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    controller = _ControllerSpy()
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=_TokenClient(),
        request_controller=controller,
        session_id="session-a",
        request_id="request-1",
    )

    assert result.input_tokens == 120
    assert result.output_tokens == 80
    assert controller.usages == [("request-1", 120, 80)]
    assert controller.releases == ["request-1"]


def test_orchestrator_releases_allowed_request_after_cloud_exception():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    controller = _ControllerSpy()
    result = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=AIConfig("key", True),
        client=_FailingClient(),
        request_controller=controller,
        session_id="session-a",
        request_id="request-1",
    )

    assert result.degraded_reason == "service_unavailable"
    assert controller.usages == []
    assert controller.releases == ["request-1"]


def test_default_orchestrator_controller_persists_limits_across_calls():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    client = _TokenClient()
    config = AIConfig(
        "key",
        True,
        per_session_per_minute=1,
        per_session_daily_requests=30,
        daily_token_budget=991_337,
        max_concurrent_requests=4,
    )

    first = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=config,
        client=client,
        session_id="default-controller-session",
        request_id="default-controller-request-1",
    )
    second = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=config,
        client=client,
        session_id="default-controller-session",
        request_id="default-controller-request-2",
    )

    assert first.degraded_reason is None
    assert second.degraded_reason == "rate_limited"
    assert client.calls == 1


def test_default_controller_keeps_session_limit_when_request_id_is_omitted():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question

    client = _TokenClient()
    config = AIConfig(
        "key",
        True,
        per_session_per_minute=1,
        per_session_daily_requests=30,
        daily_token_budget=991_338,
        max_concurrent_requests=4,
    )

    first = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=config,
        client=client,
        session_id="session-with-generated-request-id",
    )
    second = answer_question(
        _chart(),
        "财运如何？",
        [],
        config=config,
        client=client,
        session_id="session-with-generated-request-id",
    )

    assert first.degraded_reason is None
    assert second.degraded_reason == "rate_limited"
    assert client.calls == 1


def test_boundary_and_clarification_sources_are_not_saved_as_cloud_failures():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "超出范围",
        source="boundary",
        details={"degraded_reason": "service_unavailable"},
    )
    append_chat_message(
        state,
        "assistant",
        "请确认年龄口径",
        source="clarification",
        details={"degraded_reason": "network_error"},
    )

    boundary, clarification = state["bazi_chat_messages"]
    assert boundary["source"] == "boundary"
    assert clarification["source"] == "clarification"
    assert "degraded_reason" not in boundary.get("details", {})
    assert "degraded_reason" not in clarification.get("details", {})
