from __future__ import annotations

from pathlib import Path

import pytest


def test_runtime_mode_defaults_to_public_and_only_accepts_explicit_local(monkeypatch):
    from utils.runtime_mode import get_runtime_mode, is_public_mode

    monkeypatch.delenv("MINGSHU_RUNTIME_MODE", raising=False)
    assert get_runtime_mode() == "public"
    assert is_public_mode() is True
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "local")
    assert get_runtime_mode() == "local"
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "unexpected")
    assert get_runtime_mode() == "public"


def test_public_pages_replace_archive_and_remove_storage_routes(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    import app

    pages = app.get_pages()

    assert pages["设置/档案"].__name__ == "render_privacy_center_page"
    assert "命盘档案" not in pages
    assert "数据备份" not in pages


def test_public_database_access_fails_before_creating_a_file(monkeypatch, tmp_path):
    from utils import database

    target = tmp_path / "profiles.db"
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    monkeypatch.setattr(database, "DB_PATH", str(target))

    with pytest.raises(RuntimeError, match="公网模式不允许"):
        database.init_db()

    assert not target.exists()


def test_public_backup_and_restore_are_blocked_even_if_a_local_db_exists(monkeypatch, tmp_path):
    from utils import backup, database

    target = tmp_path / "profiles.db"
    target.write_bytes(b"private")
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    monkeypatch.setattr(database, "DB_PATH", str(target))

    with pytest.raises(RuntimeError, match="公网模式不允许"):
        backup.backup_database(str(tmp_path / "copy.db"))
    with pytest.raises(RuntimeError, match="公网模式不允许"):
        backup.restore_database(str(target))


def test_local_launchers_explicitly_enable_local_storage():
    root = Path(__file__).resolve().parents[1]
    for launcher in ("start.command", "run_mac.sh"):
        assert "MINGSHU_RUNTIME_MODE=local" in (root / launcher).read_text(encoding="utf-8")
