"""Thread-safe, process-local API sessions and confirmation challenges.

This is not a distributed store: all state disappears on process restart and
is isolated per worker. Sensitive canonical charts are cleared at expiry or
replacement. Pending previews retain hashes only, never raw birth input.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Literal


StoreState = Literal[
    "ok", "missing", "expired", "invalidated", "forbidden", "conflict", "mismatch"
]


@dataclass
class PendingPreview:
    preview_id: str
    input_hash: str
    chart_hash: str
    token: str
    expires_at: float
    reservation: str | None = None


@dataclass
class SessionRecord:
    expires_at: float
    chart_id: str | None = None
    pending: PendingPreview | None = None


@dataclass
class ChartRecord:
    owner: str
    chart: dict[str, object]
    facts: dict[str, object]
    fingerprint: str
    expires_at: float


@dataclass(frozen=True)
class ChartSnapshot:
    facts: dict[str, object]
    fingerprint: str


@dataclass(frozen=True)
class Tombstone:
    state: Literal["expired", "invalidated"]
    expires_at: float


class SessionCapacityError(RuntimeError):
    """The process-local store is full of active sessions."""


class SessionStore:
    def __init__(
        self,
        ttl_seconds: int,
        clock: Callable[[], float] = time.monotonic,
        *,
        tombstone_limit: int = 4096,
        session_capacity: int = 4096,
    ):
        self.ttl_seconds = ttl_seconds
        self.preview_ttl_seconds = min(ttl_seconds, 300)
        self.tombstone_ttl_seconds = min(ttl_seconds, 300)
        self.tombstone_limit = tombstone_limit
        self.session_capacity = session_capacity
        self._clock = clock
        self._secret = secrets.token_bytes(32)
        self._sessions: dict[str, SessionRecord] = {}
        self._charts: dict[str, ChartRecord] = {}
        self._tombstones: OrderedDict[str, Tombstone] = OrderedDict()
        self._lock = threading.RLock()

    def issue(self) -> tuple[str, str]:
        with self._lock:
            if len(self._sessions) >= self.session_capacity:
                self._cleanup_locked(self._clock())
            if len(self._sessions) >= self.session_capacity:
                raise SessionCapacityError("active session capacity reached")
            session_id = secrets.token_urlsafe(32)
            self._sessions[session_id] = SessionRecord(
                expires_at=self._clock() + self.ttl_seconds
            )
        return session_id, self.sign(session_id)

    def sign(self, session_id: str) -> str:
        signature = hmac.new(self._secret, session_id.encode(), hashlib.sha256).hexdigest()
        return f"{session_id}.{signature}"

    def verify(self, cookie: str | None) -> str | None:
        state, session_id = self.verify_status(cookie)
        return session_id if state == "ok" else None

    def verify_status(self, cookie: str | None) -> tuple[StoreState, str | None]:
        if not cookie or "." not in cookie:
            return "missing", None
        session_id, signature = cookie.rsplit(".", 1)
        expected = hmac.new(self._secret, session_id.encode(), hashlib.sha256).hexdigest()
        if not session_id or not hmac.compare_digest(signature, expected):
            return "forbidden", None
        now = self._clock()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return "expired", None
            if session.expires_at <= now:
                self._expire_session_locked(session_id, session, now)
                return "expired", None
            session.expires_at = now + self.ttl_seconds
        return "ok", session_id

    def create_preview(
        self, session_id: str, input_hash: str, chart_hash: str
    ) -> tuple[StoreState, str | None, str | None]:
        now = self._clock()
        with self._lock:
            session = self._live_session_locked(session_id, now)
            if session is None:
                return "expired", None, None
            preview_id = secrets.token_urlsafe(24)
            token = self._preview_token(session_id, preview_id, input_hash)
            session.pending = PendingPreview(
                preview_id=preview_id,
                input_hash=input_hash,
                chart_hash=chart_hash,
                token=token,
                expires_at=now + self.preview_ttl_seconds,
            )
            return "ok", preview_id, token

    def begin_confirmation(
        self,
        session_id: str,
        preview_id: str,
        token: str,
        chart_hash: str,
        input_hash: str,
    ) -> tuple[StoreState, str | None]:
        now = self._clock()
        with self._lock:
            session = self._live_session_locked(session_id, now)
            if session is None:
                return "expired", None
            pending = session.pending
            if pending is None or pending.expires_at <= now:
                session.pending = None
                return "conflict", None
            if pending.reservation is not None:
                return "conflict", None
            if (
                not hmac.compare_digest(pending.preview_id, preview_id)
                or not hmac.compare_digest(pending.token, token)
                or not hmac.compare_digest(pending.chart_hash, chart_hash)
                or not hmac.compare_digest(pending.input_hash, input_hash)
            ):
                return "conflict", None
            reservation = secrets.token_urlsafe(24)
            pending.reservation = reservation
            return "ok", reservation

    def cancel_confirmation(self, session_id: str, reservation: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.pending and session.pending.reservation == reservation:
                session.pending = None

    def finish_confirmation(
        self,
        session_id: str,
        reservation: str,
        input_hash: str,
        chart_hash: str,
        chart: dict[str, object],
        facts: dict[str, object],
    ) -> tuple[StoreState, str | None]:
        now = self._clock()
        with self._lock:
            session = self._live_session_locked(session_id, now)
            if session is None:
                return "expired", None
            pending = session.pending
            if pending is None or pending.reservation != reservation:
                return "conflict", None
            session.pending = None
            if pending.expires_at <= now:
                return "expired", None
            if not hmac.compare_digest(pending.input_hash, input_hash):
                return "mismatch", None
            if not hmac.compare_digest(pending.chart_hash, chart_hash):
                return "mismatch", None

            previous_id = session.chart_id
            if previous_id:
                self._remove_chart_locked(previous_id, "invalidated", now)
            chart_id = secrets.token_urlsafe(24)
            self._charts[chart_id] = ChartRecord(
                owner=session_id,
                # The store owns its copies. API response serialization and
                # callers may continue using or mutate their objects while a
                # later confirmation concurrently scrubs the stored chart.
                chart=copy.deepcopy(chart),
                facts=copy.deepcopy(facts),
                fingerprint=chart_hash,
                expires_at=now + self.ttl_seconds,
            )
            session.chart_id = chart_id
            session.expires_at = now + self.ttl_seconds
            return "ok", chart_id

    def get(self, session_id: str, chart_id: str) -> tuple[StoreState, ChartSnapshot | None]:
        now = self._clock()
        with self._lock:
            session = self._live_session_locked(session_id, now)
            if session is None:
                tombstone = self._tombstones.get(chart_id)
                return (tombstone.state if tombstone else "expired"), None
            record = self._charts.get(chart_id)
            if record is None:
                tombstone = self._tombstones.get(chart_id)
                return (tombstone.state if tombstone else "missing"), None
            if record.expires_at <= now:
                self._remove_chart_locked(chart_id, "expired", now)
                return "expired", None
            if record.owner != session_id:
                return "forbidden", None
            record.expires_at = now + self.ttl_seconds
            session.expires_at = now + self.ttl_seconds
            return "ok", ChartSnapshot(
                facts=copy.deepcopy(record.facts), fingerprint=record.fingerprint
            )

    def cleanup(self) -> None:
        """Scrub idle sensitive state; called periodically by app lifespan."""
        with self._lock:
            self._cleanup_locked(self._clock())

    def is_live(self, session_id: str) -> bool:
        """Check session liveness without extending its TTL."""
        now = self._clock()
        with self._lock:
            return self._live_session_locked(session_id, now) is not None

    def clear(self) -> None:
        """Clear all process-local state during graceful shutdown."""
        with self._lock:
            for record in self._charts.values():
                record.chart.clear()
                record.facts.clear()
            self._charts.clear()
            self._sessions.clear()
            self._tombstones.clear()

    def counts(self) -> tuple[int, int, int]:
        with self._lock:
            return len(self._sessions), len(self._charts), len(self._tombstones)

    def _preview_token(self, session_id: str, preview_id: str, input_hash: str) -> str:
        payload = f"{session_id}\0{preview_id}\0{input_hash}".encode()
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    def _cleanup_locked(self, now: float) -> None:
        for session_id, session in list(self._sessions.items()):
            if session.expires_at <= now:
                self._expire_session_locked(session_id, session, now)
            elif session.pending and session.pending.expires_at <= now:
                session.pending = None
        for chart_id, record in list(self._charts.items()):
            if record.expires_at <= now:
                self._remove_chart_locked(chart_id, "expired", now)
        for chart_id, tombstone in list(self._tombstones.items()):
            if tombstone.expires_at <= now:
                self._tombstones.pop(chart_id, None)

    def _live_session_locked(self, session_id: str, now: float) -> SessionRecord | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.expires_at <= now:
            self._expire_session_locked(session_id, session, now)
            return None
        return session

    def _expire_session_locked(
        self, session_id: str, session: SessionRecord, now: float
    ) -> None:
        session.pending = None
        if session.chart_id:
            self._remove_chart_locked(session.chart_id, "expired", now)
        self._sessions.pop(session_id, None)

    def _remove_chart_locked(
        self,
        chart_id: str,
        state: Literal["expired", "invalidated"],
        now: float,
    ) -> None:
        record = self._charts.pop(chart_id, None)
        if record is None:
            return
        record.chart.clear()
        record.facts.clear()
        self._tombstones[chart_id] = Tombstone(
            state=state, expires_at=now + self.tombstone_ttl_seconds
        )
        self._tombstones.move_to_end(chart_id)
        while len(self._tombstones) > self.tombstone_limit:
            self._tombstones.popitem(last=False)
