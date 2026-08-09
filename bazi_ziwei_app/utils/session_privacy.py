"""当前会话中的出生资料与派生结果生命周期管理。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping


LAST_ACTIVE_KEY = "private_session_last_active_at"
PENDING_INQUIRY_KEY = "inquiry_pending_question"
PRIVATE_SESSION_KEYS = (
    "profile_draft",
    "profile_use_solar_time",
    "profile_privacy_consent",
    "profile_birth_preview",
    "profile_birth_preview_input",
    "current_profile",
    "current_chart",
    "current_report",
    "current_luck_data",
    "current_yearly_data",
    "current_monthly_data",
    "current_monthly_event_results",
    "life_overview_expanded_term_id",
    "life_overview_term_focus_return",
    "report_card_index",
    "bazi_chat_messages",
    "bazi_chat_profile_fingerprint",
    "bazi_chat_last_activity",
    "bazi_chat_request_state",
    PENDING_INQUIRY_KEY,
    LAST_ACTIVE_KEY,
)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def touch_private_session(state: MutableMapping, now: datetime | None = None) -> None:
    timestamp = _as_utc(now or datetime.now(timezone.utc))
    state[LAST_ACTIVE_KEY] = timestamp.isoformat()


def clear_private_session(state: MutableMapping) -> list[str]:
    removed: list[str] = []
    for key in PRIVATE_SESSION_KEYS:
        if key in state:
            state.pop(key, None)
            removed.append(key)
    return removed


def expire_private_session(
    state: MutableMapping,
    now: datetime | None = None,
    ttl_minutes: int = 30,
) -> bool:
    raw = state.get(LAST_ACTIVE_KEY)
    if not raw:
        return False
    try:
        last_active = _as_utc(datetime.fromisoformat(str(raw)))
    except (TypeError, ValueError):
        clear_private_session(state)
        return True
    current = _as_utc(now or datetime.now(timezone.utc))
    if (current - last_active).total_seconds() >= max(1, ttl_minutes) * 60:
        clear_private_session(state)
        return True
    return False


def maintain_private_session(
    state: MutableMapping,
    now: datetime | None = None,
    ttl_minutes: int = 30,
) -> bool:
    """先执行到期清除；仍有效且含个人资料时刷新活动时间。"""
    current = _as_utc(now or datetime.now(timezone.utc))
    expired = expire_private_session(state, current, ttl_minutes)
    if not expired and any(
        key in state
        for key in (
            "profile_birth_preview",
            "current_profile",
            "current_chart",
            "current_report",
        )
    ):
        touch_private_session(state, current)
    return expired
