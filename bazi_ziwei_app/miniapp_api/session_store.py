"""进程内测试会话；不改变现有 Streamlit 会话与数据库。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any


DEFAULT_SETTINGS = {
    "report_length": "标准版",
    "show_technical_details": False,
    "show_disclaimer": True,
    "default_export_format": "Markdown",
    "enable_quality_check": True,
}


@dataclass
class MiniappSession:
    profile: dict | None = None
    chart: dict | None = None
    report: dict | None = None
    chat_history: list[dict[str, str]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


class SessionStore:
    def __init__(self, ttl_minutes: int = 30) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._items: dict[str, MiniappSession] = {}
        self._lock = RLock()

    def get(self, session_id: str) -> MiniappSession:
        safe_id = (session_id or "test-session").strip()[:96] or "test-session"
        with self._lock:
            self._prune()
            session = self._items.setdefault(safe_id, MiniappSession())
            session.touch()
            return session

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._items.pop((session_id or "test-session").strip()[:96], None)

    def _prune(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [key for key, item in self._items.items() if now - item.updated_at > self._ttl]
        for key in expired:
            self._items.pop(key, None)


store = SessionStore()
