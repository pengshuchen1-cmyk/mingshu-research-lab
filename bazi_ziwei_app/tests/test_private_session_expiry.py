from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _private_state(now):
    return {
        "profile_draft": {"name": "金丝雀姓名"},
        "profile_birth_preview": {
            "profile": {"name": "金丝雀姓名", "birth_date": "1990-01-01"}
        },
        "profile_birth_preview_input": "preview-input-fingerprint",
        "current_profile": {"birth_date": "1990-01-01"},
        "current_chart": {"pillars": {"day": "甲子"}},
        "current_report": {"summary": "私密报告"},
        "current_luck_data": {"private": True},
        "current_yearly_data": {"private": True},
        "current_monthly_data": [{"private": True}],
        "current_monthly_event_results": [{"private": True}],
        "bazi_chat_messages": [{"role": "user", "content": "私密问题"}],
        "bazi_chat_profile_fingerprint": "private-fingerprint",
        "bazi_chat_last_activity": now.isoformat(),
        "bazi_chat_request_state": {"busy": True},
        "life_overview_expanded_term_id": "wealth-star",
        "private_session_last_active_at": now.isoformat(),
        "sidebar_navigation": "个人命盘",
    }


def test_clear_private_session_removes_raw_and_derived_data_but_keeps_navigation():
    from utils.session_privacy import PRIVATE_SESSION_KEYS, clear_private_session

    state = _private_state(datetime.now(timezone.utc))
    removed = clear_private_session(state)

    assert set(PRIVATE_SESSION_KEYS).issuperset(removed)
    assert all(key not in state for key in PRIVATE_SESSION_KEYS)
    assert "profile_birth_preview" not in state
    assert "profile_birth_preview_input" not in state
    assert state["sidebar_navigation"] == "个人命盘"


def test_expiry_clears_after_thirty_minutes_and_touch_refreshes_activity():
    from utils.session_privacy import expire_private_session, touch_private_session

    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    state = _private_state(now - timedelta(minutes=31))
    assert expire_private_session(state, now, ttl_minutes=30) is True
    assert "current_profile" not in state

    touch_private_session(state, now)
    assert expire_private_session(state, now + timedelta(minutes=29), ttl_minutes=30) is False
    assert state["private_session_last_active_at"] == now.isoformat()


def test_active_private_session_is_refreshed_but_expired_session_is_not_revived():
    from utils.session_privacy import maintain_private_session

    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    active = _private_state(now - timedelta(minutes=10))
    assert maintain_private_session(active, now) is False
    assert active["private_session_last_active_at"] == now.isoformat()

    expired = _private_state(now - timedelta(minutes=31))
    assert maintain_private_session(expired, now) is True
    assert "current_profile" not in expired


def test_preview_only_private_session_refreshes_on_activity():
    from utils.session_privacy import maintain_private_session

    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    state = {
        "profile_birth_preview": {"profile": {"name": "金丝雀姓名"}},
        "profile_birth_preview_input": "preview-input-fingerprint",
        "private_session_last_active_at": (now - timedelta(minutes=10)).isoformat(),
    }

    assert maintain_private_session(state, now) is False
    assert state["private_session_last_active_at"] == now.isoformat()
