from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest


def _legacy_database(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute(
            "CREATE TABLE bazi_charts (id INTEGER PRIMARY KEY, profile_id INTEGER, chart_json TEXT)"
        )
        conn.execute("INSERT INTO profiles (id, name) VALUES (1, 'legacy')")
        conn.execute(
            "INSERT INTO bazi_charts (id, profile_id, chart_json) VALUES (1, 1, '{}')"
        )


def test_migration_backs_up_once_then_deletes_child_before_parent(tmp_path: Path):
    from utils.database import migrate_rule_engine_v2

    db_path = tmp_path / "profiles.db"
    _legacy_database(db_path)
    backup = migrate_rule_engine_v2(
        str(db_path), now=datetime(2026, 7, 22, 12, 30, 45)
    )

    assert backup == str(tmp_path / "profiles.db.pre-rule-v2-20260722123045.bak")
    assert Path(backup).exists()
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM bazi_charts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 0
        assert conn.execute(
            "SELECT value FROM schema_meta WHERE key='rule_engine_schema'"
        ).fetchone()[0] == "2"


def test_migration_is_idempotent_and_preserves_new_v2_rows(tmp_path: Path):
    from utils.database import migrate_rule_engine_v2

    db_path = tmp_path / "profiles.db"
    _legacy_database(db_path)
    first = migrate_rule_engine_v2(str(db_path))
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO profiles (id, name) VALUES (2, 'new-v2')")

    second = migrate_rule_engine_v2(str(db_path))

    assert first is not None
    assert second is None
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT name FROM profiles WHERE id=2").fetchone()[0] == "new-v2"
    assert len(list(tmp_path.glob("*.pre-rule-v2-*.bak"))) == 1


def test_backup_failure_leaves_legacy_rows_untouched(tmp_path: Path, monkeypatch):
    import utils.database as database

    db_path = tmp_path / "profiles.db"
    _legacy_database(db_path)

    def fail_copy(*_args, **_kwargs):
        raise OSError("backup unavailable")

    monkeypatch.setattr(database.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="backup unavailable"):
        database.migrate_rule_engine_v2(str(db_path))
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM bazi_charts").fetchone()[0] == 1
