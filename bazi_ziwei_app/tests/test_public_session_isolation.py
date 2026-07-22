from datetime import datetime, timezone


def test_two_sessions_never_share_private_state_and_clear_is_scoped():
    from utils.session_privacy import clear_private_session, touch_private_session

    session_a = {"current_profile": {"name": "金丝雀甲"}, "current_report": {"text": "甲报告"}}
    session_b = {"current_profile": {"name": "金丝雀乙"}, "current_report": {"text": "乙报告"}}
    touch_private_session(session_a, datetime.now(timezone.utc))
    touch_private_session(session_b, datetime.now(timezone.utc))

    clear_private_session(session_a)

    assert "current_profile" not in session_a
    assert session_b["current_profile"]["name"] == "金丝雀乙"
    assert "金丝雀甲" not in repr(session_b)
