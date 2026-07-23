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


def test_question_validation_rejects_blank_and_more_than_five_hundred_chars():
    from core.ai_session import validate_question

    assert validate_question("  ")[0] is False
    assert validate_question("甲" * 501)[0] is False
    assert validate_question("这个八字的财运怎么样？") == (True, "")


def test_chat_message_has_timestamp_and_allowlisted_details_only():
    from core.ai_session import append_chat_message

    state = {}
    append_chat_message(
        state,
        "assistant",
        "回答",
        source="cloud_validated",
        details={
            "chart_evidence": ["命盘证据", 123, ""],
            "rule_evidence": ["规则证据"],
            "timing_conditions": ["阶段条件"],
            "practical_advice": ["现实建议"],
            "uncertainty": ["不确定性"],
            "sections": {
                "分析结论": "结论",
                "命盘依据": "- 命盘证据",
                "规则依据": "- 规则证据",
                "阶段与触发条件": "- 阶段条件",
                "现实建议": "- 现实建议",
                "不确定性与限制": "- 不确定性",
                "任意标题": "不应保存",
            },
            "degraded_reason": "network_error",
            "raw_payload": {"customer_name": "不应保存"},
        },
    )

    item = state["bazi_chat_messages"][0]
    assert item["created_at"].endswith("+00:00")
    assert set(item["details"]) == {
        "chart_evidence",
        "rule_evidence",
        "timing_conditions",
        "practical_advice",
        "uncertainty",
        "sections",
        "degraded_reason",
    }
    assert item["details"]["chart_evidence"] == ["命盘证据"]
    assert list(item["details"]["sections"]) == [
        "分析结论",
        "命盘依据",
        "规则依据",
        "阶段与触发条件",
        "现实建议",
        "不确定性与限制",
    ]
    assert "任意标题" not in item["details"]["sections"]
    assert item["details"]["degraded_reason"] == "network_error"


def test_chat_drops_arbitrary_degradation_reason_and_non_string_sections():
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

    details = state["bazi_chat_messages"][0]["details"]
    assert details["sections"] == {"分析结论": "安全结论"}
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
