"""Per-session lifecycle for the Bazi question-and-answer chat."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import MutableMapping

from core.ai_models import ChatMessage


CHAT_MESSAGES_KEY = "bazi_chat_messages"
CHAT_FINGERPRINT_KEY = "bazi_chat_profile_fingerprint"
CHAT_LAST_ACTIVITY_KEY = "bazi_chat_last_activity"
CHAT_REQUEST_STATE_KEY = "bazi_chat_request_state"
CHAT_SESSION_KEYS = (
    CHAT_MESSAGES_KEY,
    CHAT_FINGERPRINT_KEY,
    CHAT_LAST_ACTIVITY_KEY,
    CHAT_REQUEST_STATE_KEY,
)
DETAIL_KEYS = ("chart_evidence", "rule_evidence", "uncertainty", "cautions")


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _timestamp(now: datetime | None = None) -> str:
    return _as_utc(now or datetime.now(timezone.utc)).isoformat()


def clear_chat_session(state: MutableMapping) -> list[str]:
    removed: list[str] = []
    for key in CHAT_SESSION_KEYS:
        if key in state:
            state.pop(key, None)
            removed.append(key)
    return removed


def initialize_chat_for_chart(
    state: MutableMapping,
    chart_fingerprint: str,
    now: datetime | None = None,
) -> bool:
    """Initialize chat and return True when a profile switch cleared history."""
    previous = state.get(CHAT_FINGERPRINT_KEY)
    switched = bool(previous and previous != chart_fingerprint)
    if switched:
        clear_chat_session(state)
    state.setdefault(CHAT_MESSAGES_KEY, [])
    state[CHAT_FINGERPRINT_KEY] = str(chart_fingerprint)
    state[CHAT_LAST_ACTIVITY_KEY] = _timestamp(now)
    state.setdefault(CHAT_REQUEST_STATE_KEY, {"busy": False})
    return switched


def touch_chat_session(state: MutableMapping, now: datetime | None = None) -> None:
    state[CHAT_LAST_ACTIVITY_KEY] = _timestamp(now)


def expire_chat_session(
    state: MutableMapping,
    now: datetime | None = None,
    ttl_minutes: int = 30,
) -> bool:
    raw = state.get(CHAT_LAST_ACTIVITY_KEY)
    if not raw:
        return False
    try:
        last = _as_utc(datetime.fromisoformat(str(raw)))
    except (TypeError, ValueError):
        clear_chat_session(state)
        return True
    current = _as_utc(now or datetime.now(timezone.utc))
    if (current - last).total_seconds() >= max(1, ttl_minutes) * 60:
        clear_chat_session(state)
        return True
    return False


def append_chat_message(
    state: MutableMapping,
    role: str,
    content: str,
    *,
    source: str | None = None,
    details: dict | None = None,
) -> None:
    messages = list(state.get(CHAT_MESSAGES_KEY, []))
    safe_role = role if role in {"user", "assistant"} else "assistant"
    item = {"role": safe_role, "content": str(content), "created_at": _timestamp()}
    if source in {"cloud_validated", "local_rules"}:
        item["source"] = source
    if details:
        safe_details: dict[str, list[str]] = {}
        for key in DETAIL_KEYS:
            values = details.get(key, [])
            if isinstance(values, (list, tuple)):
                safe_details[key] = [
                    str(value).strip()
                    for value in values[:12]
                    if isinstance(value, str) and value.strip()
                ]
        if any(safe_details.values()):
            item["details"] = safe_details
    messages.append(item)
    state[CHAT_MESSAGES_KEY] = messages[-20:]
    touch_chat_session(state)


def recent_context_messages(state: MutableMapping) -> list[ChatMessage]:
    items = list(state.get(CHAT_MESSAGES_KEY, []))[-6:]
    return [
        ChatMessage(role=str(item.get("role", "user")), content=str(item.get("content", "")))
        for item in items
        if isinstance(item, dict) and item.get("content")
    ]


def validate_question(question: str) -> tuple[bool, str]:
    text = str(question or "").strip()
    if not text:
        return False, "请输入您想问的问题。"
    if len(text) > 500:
        return False, "问题请控制在 500 字以内。"
    return True, ""
