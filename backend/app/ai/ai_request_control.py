"""Process-local request controls for cloud Bazi AI generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from threading import Lock
from typing import Literal

ControlReason = Literal[
    "rate_limited",
    "daily_budget",
    "duplicate_request",
    "concurrency_limit",
]


@dataclass(frozen=True)
class PreflightDecision:
    allowed: bool
    reason: ControlReason | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AIRequestController:
    """Protect process-local request, concurrency, and token budgets."""

    def __init__(
        self,
        *,
        per_minute: int = 3,
        daily_requests: int = 30,
        daily_tokens: int = 500_000,
        max_concurrent: int = 4,
    ) -> None:
        self._per_minute = max(0, int(per_minute))
        self._daily_requests = max(0, int(daily_requests))
        self._daily_tokens = max(0, int(daily_tokens))
        self._max_concurrent = max(0, int(max_concurrent))
        self._lock = Lock()
        self._minute_counts: dict[tuple[str, str], int] = {}
        self._daily_request_counts: dict[tuple[str, str], int] = {}
        self._daily_token_totals: dict[str, int] = {}
        self._in_flight: dict[str, str] = {}

    @staticmethod
    def _session_hash(session_id: str) -> str:
        return sha256(str(session_id or "anonymous").encode("utf-8")).hexdigest()

    def _discard_expired_buckets(self, day: str, minute: str) -> None:
        self._minute_counts = {
            key: value
            for key, value in self._minute_counts.items()
            if key[0] == minute
        }
        self._daily_request_counts = {
            key: value
            for key, value in self._daily_request_counts.items()
            if key[0] == day
        }
        self._daily_token_totals = {
            key: value
            for key, value in self._daily_token_totals.items()
            if key == day
        }

    def preflight(self, session_id: str, request_id: str) -> PreflightDecision:
        now = _utc_now()
        day = now.date().isoformat()
        minute = now.strftime("%Y-%m-%dT%H:%M")
        session_hash = self._session_hash(session_id)
        request_key = str(request_id)
        minute_key = (minute, session_hash)
        day_key = (day, session_hash)

        with self._lock:
            self._discard_expired_buckets(day, minute)
            if request_key in self._in_flight:
                return PreflightDecision(False, "duplicate_request")
            if self._daily_token_totals.get(day, 0) >= self._daily_tokens:
                return PreflightDecision(False, "daily_budget")
            if len(self._in_flight) >= self._max_concurrent:
                return PreflightDecision(False, "concurrency_limit")
            if (
                self._minute_counts.get(minute_key, 0) >= self._per_minute
                or self._daily_request_counts.get(day_key, 0)
                >= self._daily_requests
            ):
                return PreflightDecision(False, "rate_limited")

            self._minute_counts[minute_key] = (
                self._minute_counts.get(minute_key, 0) + 1
            )
            self._daily_request_counts[day_key] = (
                self._daily_request_counts.get(day_key, 0) + 1
            )
            self._in_flight[request_key] = day
            return PreflightDecision(True)

    def record_usage(
        self,
        request_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        request_key = str(request_id)
        with self._lock:
            day = self._in_flight.get(request_key)
            if day is None:
                return
            safe_input = (
                max(0, input_tokens) if type(input_tokens) is int else 0
            )
            safe_output = (
                max(0, output_tokens) if type(output_tokens) is int else 0
            )
            self._daily_token_totals[day] = (
                self._daily_token_totals.get(day, 0)
                + safe_input
                + safe_output
            )

    def release(self, request_id: str) -> None:
        with self._lock:
            self._in_flight.pop(str(request_id), None)


_CONTROLLER_REGISTRY: dict[
    tuple[int, int, int, int],
    AIRequestController,
] = {}
_CONTROLLER_REGISTRY_LOCK = Lock()


def request_controller_for_config(config: object) -> AIRequestController:
    """Return the process-shared controller for one configured limit set."""
    limits = (
        int(getattr(config, "per_session_per_minute", 3)),
        int(getattr(config, "per_session_daily_requests", 30)),
        int(getattr(config, "daily_token_budget", 500_000)),
        int(getattr(config, "max_concurrent_requests", 4)),
    )
    with _CONTROLLER_REGISTRY_LOCK:
        controller = _CONTROLLER_REGISTRY.get(limits)
        if controller is None:
            controller = AIRequestController(
                per_minute=limits[0],
                daily_requests=limits[1],
                daily_tokens=limits[2],
                max_concurrent=limits[3],
            )
            _CONTROLLER_REGISTRY[limits] = controller
        return controller
