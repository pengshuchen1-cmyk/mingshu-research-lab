from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_chat_is_cleared_on_profile_switch_and_expiry():
    from core.ai_session import initialize_chat_for_chart, expire_chat_session

    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    state = {}
    initialize_chat_for_chart(state, "chart-a", now)
    state["bazi_chat_messages"] = [{"role": "user", "content": "旧问题"}]

    assert initialize_chat_for_chart(state, "chart-b", now) is True
    assert state["bazi_chat_messages"] == []
    assert state["bazi_chat_profile_fingerprint"] == "chart-b"

    state["bazi_chat_messages"] = [{"role": "assistant", "content": "旧回答"}]
    assert expire_chat_session(state, now + timedelta(minutes=31)) is True
    assert "bazi_chat_messages" not in state


def test_chat_keeps_twenty_display_messages_and_sends_six_recent_messages():
    from core.ai_session import append_chat_message, recent_context_messages

    state = {}
    for index in range(24):
        append_chat_message(state, "user", f"message-{index}")

    assert len(state["bazi_chat_messages"]) == 20
    assert state["bazi_chat_messages"][0]["content"] == "message-4"
    assert [item.content for item in recent_context_messages(state)] == [
        f"message-{index}" for index in range(18, 24)
    ]


def test_question_validation_rejects_blank_and_more_than_two_thousand_chars():
    from core.ai_session import validate_question

    assert validate_question("  ")[0] is False
    assert validate_question("甲" * 2000) == (True, "")
    assert validate_question("甲" * 2001) == (False, "问题请控制在 2000 字以内。")
    assert validate_question("这个八字的财运怎么样？") == (True, "")


def test_chat_message_has_timestamp_and_allowlisted_details_without_sections():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "回答",
        source="cloud_validated",
        provider="openai",
        details={
            "chart_evidence": ["命盘证据", 123, ""],
            "rule_evidence": ["规则证据"],
            "timing_conditions": ["阶段条件"],
            "practical_advice": ["现实建议"],
            "uncertainty": ["不确定性"],
            "sections": {"分析结论": "不应保存"},
            "degraded_reason": "network_error",
            "raw_payload": {"customer_name": "不应保存"},
        },
    )

    item = state["bazi_chat_messages"][0]
    assert item["created_at"].endswith("+00:00")
    assert item["provider"] == "openai"
    assert set(item["details"]) == {
        "chart_evidence",
        "rule_evidence",
        "timing_conditions",
        "practical_advice",
        "uncertainty",
        "degraded_reason",
    }
    assert item["details"]["chart_evidence"] == ["命盘证据"]
    assert "sections" not in item["details"]
    assert item["details"]["degraded_reason"] == "network_error"


def test_chat_message_keeps_safe_request_receipt_and_retry_metadata():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "本地完整回答",
        source="local_rules",
        request_id="request-123",
        details={
            "degraded_reason": "timeout",
            "interpretation_receipt": "已按 2027 年理解。",
            "retryable": True,
            "request_id": "伪造字段不应进入 details",
        },
    )

    item = state["bazi_chat_messages"][0]
    assert item["request_id"] == "request-123"
    assert item["details"] == {
        "degraded_reason": "timeout",
        "interpretation_receipt": "已按 2027 年理解。",
        "retryable": True,
    }


def test_chat_message_revalidates_retryability_before_saving():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "云端回答",
        source="cloud_validated",
        request_id="request-cloud",
        details={
            "degraded_reason": "timeout",
            "retryable": True,
        },
    )
    append_chat_message(
        state,
        "assistant",
        "认证失败的本地回答",
        source="local_rules",
        request_id="request-auth",
        details={
            "degraded_reason": "invalid_credentials",
            "retryable": True,
        },
    )

    cloud_details = state["bazi_chat_messages"][0]["details"]
    auth_details = state["bazi_chat_messages"][1]["details"]
    assert "retryable" not in cloud_details
    assert "retryable" not in auth_details


def test_chat_drops_unknown_cloud_provider_label():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "回答",
        source="cloud_validated",
        provider="attacker-controlled",
    )

    assert "provider" not in state["bazi_chat_messages"][0]


def test_chat_drops_arbitrary_degradation_reason_and_sections():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "回答",
        source="local_rules",
        details={
            "sections": {
                "分析结论": "安全结论",
                "命盘依据": {"raw_exception": "姓名：不应保存"},
            },
            "degraded_reason": "姓名：不应保存 Exception",
        },
    )

    details = state["bazi_chat_messages"][0].get("details", {})
    assert "sections" not in details
    assert "degraded_reason" not in details
    assert "不应保存" not in repr(details)


def test_recent_context_truncates_long_answers_without_changing_saved_display():
    from core.ai_session import append_chat_message, recent_context_messages

    state = {}
    full_answer = "甲" * 4500
    append_chat_message(state, "assistant", full_answer)

    history = recent_context_messages(state)

    assert state["bazi_chat_messages"][0]["content"] == full_answer
    assert len(history) == 1
    assert history[0].content == full_answer[:4000]


def test_chat_summary_and_request_idempotency():
    from core.ai_models import ResolvedQuestion
    from core.ai_session import (
        begin_chat_request, complete_chat_request, dialogue_summary,
    )

    state = {}
    resolved = ResolvedQuestion(
        safe_question="2027年财运怎么样",
        domain="wealth",
        time_scope="target_year",
        target_years=[2027],
        requested_depth="single_year",
    )
    first = begin_chat_request(state, "chart-fp", resolved)
    duplicate = begin_chat_request(state, "chart-fp", resolved)
    assert first.accepted is True
    assert duplicate.accepted is False
    assert duplicate.request_id == first.request_id

    complete_chat_request(
        state, first.request_id, resolved=resolved,
        answer="已验证答案", source="cloud_validated",
    )
    assert dialogue_summary(state).domain == "wealth"
    assert dialogue_summary(state).target_years == [2027]

    completed_duplicate = begin_chat_request(state, "chart-fp", resolved)
    assert completed_duplicate.accepted is False
    assert completed_duplicate.request_id == first.request_id
    assert completed_duplicate.cached_answer == "已验证答案"


def test_dialogue_summary_round_trips_nonidentifying_safety_and_time_scope():
    from core.ai_models import ResolvedQuestion
    from core.ai_session import (
        previous_resolved_question,
        remember_dialogue_summary,
    )

    state = {}
    resolved = ResolvedQuestion(
        safe_question="她是否已婚以及后续大运倾向",
        domain="relationship",
        time_scope="dayun",
        requested_depth="long_range",
        current_marriage_status_requested=True,
    )

    remember_dialogue_summary(state, resolved)
    previous = previous_resolved_question(state)

    assert previous is not None
    assert previous.domain == "relationship"
    assert previous.time_scope == "dayun"
    assert previous.requested_depth == "long_range"
    assert previous.current_marriage_status_requested is True
    assert "她是否已婚" not in repr(state)


def test_overview_dayun_summary_is_not_treated_as_empty():
    from core.ai_models import ResolvedQuestion
    from core.ai_session import (
        previous_resolved_question,
        remember_dialogue_summary,
    )

    state = {}
    resolved = ResolvedQuestion(
        safe_question="大运如何",
        domain="overview",
        time_scope="dayun",
        requested_depth="topic",
    )

    remember_dialogue_summary(state, resolved)
    previous = previous_resolved_question(state)

    assert previous is not None
    assert previous.domain == "overview"
    assert previous.time_scope == "dayun"
    assert previous.requested_depth == "topic"


def _resolved_question(question: str = "2027年财运怎么样"):
    from core.ai_models import ResolvedQuestion

    return ResolvedQuestion(
        safe_question=question,
        domain="wealth",
        time_scope="target_year",
        target_years=[2027],
        requested_depth="single_year",
    )


def test_busy_request_rejects_different_fingerprint_without_returning_its_cache():
    from core.ai_session import begin_chat_request, complete_chat_request

    state = {}
    first_resolved = _resolved_question()
    second_resolved = _resolved_question("2028年财运怎么样")
    first = begin_chat_request(state, "chart-fp", first_resolved)
    rejected = begin_chat_request(state, "chart-fp", second_resolved)

    assert rejected.accepted is False
    assert rejected.request_id == first.request_id
    assert rejected.cached_answer == ""

    complete_chat_request(
        state,
        first.request_id,
        resolved=first_resolved,
        answer="仅属于第一个问题的答案",
        source="cloud_validated",
    )
    completed_second = begin_chat_request(state, "chart-fp", second_resolved)
    assert completed_second.accepted is True
    assert completed_second.cached_answer == ""


def test_chart_switch_clears_completed_chat_cache():
    from core.ai_session import begin_chat_request, complete_chat_request

    state = {}
    resolved = _resolved_question()
    first = begin_chat_request(state, "chart-a", resolved)
    complete_chat_request(
        state,
        first.request_id,
        resolved=resolved,
        answer="只属于命盘 A 的答案",
        source="cloud_validated",
    )

    switched = begin_chat_request(state, "chart-b", resolved)

    assert switched.accepted is True
    assert switched.cached_answer == ""
    assert "result" not in state["bazi_chat_request_state"]


def test_expired_chat_cache_is_not_read_or_restored():
    from core.ai_session import begin_chat_request, cached_answer, complete_chat_request, request_fingerprint

    state = {}
    resolved = _resolved_question()
    first = begin_chat_request(state, "chart-fp", resolved)
    complete_chat_request(
        state,
        first.request_id,
        resolved=resolved,
        answer="已经到期的答案",
        source="cloud_validated",
    )
    state["bazi_chat_last_activity"] = (
        datetime.now(timezone.utc) - timedelta(minutes=31)
    ).isoformat()

    assert cached_answer(state, request_fingerprint("chart-fp", resolved)) == ""
    assert "bazi_chat_request_state" not in state


def test_expired_request_id_cannot_write_a_late_answer():
    from core.ai_session import begin_chat_request, complete_chat_request

    state = {}
    resolved = _resolved_question()
    first = begin_chat_request(state, "chart-fp", resolved)
    state["bazi_chat_last_activity"] = (
        datetime.now(timezone.utc) - timedelta(minutes=31)
    ).isoformat()

    complete_chat_request(
        state,
        first.request_id,
        resolved=resolved,
        answer="迟到的答案不应写回",
        source="cloud_validated",
    )

    assert "bazi_chat_request_state" not in state
    assert "bazi_chat_messages" not in state
