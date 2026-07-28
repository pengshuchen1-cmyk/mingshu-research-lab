"""Per-session lifecycle for the Bazi question-and-answer chat."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import MutableMapping
from uuid import uuid4

from pydantic import ValidationError

from core.ai_models import (
    ChatMessage,
    DialogueSummary,
    RequestStart,
    ResolvedQuestion,
)


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
DETAIL_KEYS = (
    "chart_evidence",
    "rule_evidence",
    "timing_conditions",
    "practical_advice",
    "uncertainty",
    "degraded_reason",
)
_LIST_DETAIL_KEYS = (
    "chart_evidence",
    "rule_evidence",
    "timing_conditions",
    "practical_advice",
    "uncertainty",
)
_DEGRADATION_REASONS = frozenset(
    {
        "missing_api_key",
        "insufficient_quota",
        "invalid_credentials",
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
        "unparseable_response",
        "local_validation_failed",
    }
)


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
    provider: str | None = None,
    details: dict | None = None,
) -> None:
    messages = list(state.get(CHAT_MESSAGES_KEY, []))
    safe_role = role if role in {"user", "assistant"} else "assistant"
    item = {"role": safe_role, "content": str(content), "created_at": _timestamp()}
    if source in {"cloud_validated", "local_rules"}:
        item["source"] = source
    if provider in {"kimi", "openai"}:
        item["provider"] = provider
    if details:
        safe_details: dict[str, object] = {}
        for key in _LIST_DETAIL_KEYS:
            values = details.get(key, [])
            if isinstance(values, (list, tuple)):
                safe_values = [
                    str(value).strip()
                    for value in values[:12]
                    if isinstance(value, str) and value.strip()
                ]
                if safe_values:
                    safe_details[key] = safe_values
        degraded_reason = details.get("degraded_reason")
        if degraded_reason in _DEGRADATION_REASONS:
            safe_details["degraded_reason"] = degraded_reason
        if safe_details:
            item["details"] = safe_details
    messages.append(item)
    state[CHAT_MESSAGES_KEY] = messages[-20:]
    touch_chat_session(state)


def recent_context_messages(state: MutableMapping) -> list[ChatMessage]:
    items = list(state.get(CHAT_MESSAGES_KEY, []))[-6:]
    return [
        ChatMessage(
            role=str(item.get("role", "user")),
            content=str(item.get("content", ""))[:4000],
        )
        for item in items
        if isinstance(item, dict) and item.get("content")
    ]


def request_fingerprint(
    chart_fingerprint: str,
    resolved: ResolvedQuestion,
) -> str:
    """Return a stable, de-identified key for one chart-question request."""
    payload = f"{chart_fingerprint}{resolved.model_dump_json()}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _request_state(state: MutableMapping) -> dict:
    request_state = state.get(CHAT_REQUEST_STATE_KEY)
    if not isinstance(request_state, dict):
        request_state = {}
        state[CHAT_REQUEST_STATE_KEY] = request_state
    return request_state


def dialogue_summary(state: MutableMapping) -> DialogueSummary:
    request_state = _request_state(state)
    stored = request_state.get("summary")
    if not isinstance(stored, dict):
        return DialogueSummary()
    try:
        return DialogueSummary.model_validate(stored)
    except ValidationError:
        return DialogueSummary()


def cached_answer(
    state: MutableMapping,
    fingerprint: str,
) -> str:
    request_state = _request_state(state)
    result = request_state.get("result")
    if (
        request_state.get("busy")
        or request_state.get("fingerprint") != fingerprint
        or not isinstance(result, dict)
    ):
        return ""
    answer = result.get("answer")
    return str(answer) if isinstance(answer, str) else ""


def begin_chat_request(
    state: MutableMapping,
    chart_fingerprint: str,
    resolved: ResolvedQuestion,
) -> RequestStart:
    """Start one request, returning the current result for a duplicate click."""
    expire_chat_session(state)
    initialize_chat_for_chart(state, chart_fingerprint)
    request_state = _request_state(state)
    fingerprint = request_fingerprint(chart_fingerprint, resolved)
    existing_request_id = str(request_state.get("request_id") or "")

    if request_state.get("fingerprint") == fingerprint and existing_request_id:
        return RequestStart(
            accepted=False,
            request_id=existing_request_id,
            cached_answer=cached_answer(state, fingerprint),
        )
    if request_state.get("busy") and existing_request_id:
        return RequestStart(accepted=False, request_id=existing_request_id)

    request_id = uuid4().hex
    state[CHAT_REQUEST_STATE_KEY] = {
        "busy": True,
        "request_id": request_id,
        "fingerprint": fingerprint,
        "summary": dialogue_summary(state).model_dump(mode="json"),
    }
    touch_chat_session(state)
    return RequestStart(accepted=True, request_id=request_id)


def complete_chat_request(
    state: MutableMapping,
    request_id: str,
    *,
    resolved: ResolvedQuestion,
    answer: str,
    source: str,
) -> None:
    """Store a validated answer only when it belongs to the active request."""
    request_state = _request_state(state)
    if (
        not request_state.get("busy")
        or request_state.get("request_id") != request_id
    ):
        return
    summary = DialogueSummary(
        domain=resolved.domain,
        target_years=resolved.target_years,
        target_months=resolved.target_months,
    )
    request_state.update(
        {
            "busy": False,
            "result": {"answer": str(answer), "source": str(source)},
            "summary": summary.model_dump(mode="json"),
        }
    )
    touch_chat_session(state)


def validate_question(question: str) -> tuple[bool, str]:
    text = str(question or "").strip()
    if not text:
        return False, "请输入您想问的问题。"
    if len(text) > 2000:
        return False, "问题请控制在 2000 字以内。"
    return True, ""
