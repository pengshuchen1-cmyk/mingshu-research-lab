"""SQLite 本地数据库。"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import datetime

from utils.runtime_mode import require_local_storage

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "profiles.db")


def _optional_int(value: object) -> int | None:
    return None if value is None or value == "" else int(value)


def _connect() -> sqlite3.Connection:
    """创建数据库连接。"""
    require_local_storage()
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_profile_note_column(conn: sqlite3.Connection) -> None:
    """确保 profiles 表存在 note 字段。"""
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(profiles)").fetchall()]
    if "note" not in columns:
        conn.execute("ALTER TABLE profiles ADD COLUMN note TEXT")


def init_db() -> None:
    """
    初始化 SQLite 数据库。
    """
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                gender TEXT,
                birth_date TEXT,
                birth_hour INTEGER,
                birth_minute INTEGER,
                birth_place TEXT,
                use_solar_time INTEGER,
                note TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bazi_charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                chart_json TEXT,
                report_json TEXT,
                created_at TEXT
            )
            """
        )
        _ensure_profile_note_column(conn)
        conn.commit()
    migrate_rule_engine_v2(DB_PATH)


def migrate_rule_engine_v2(
    db_path: str,
    *,
    now: datetime | None = None,
) -> str | None:
    """Back up and remove incompatible pre-rule-v2 profiles exactly once."""
    path = os.path.abspath(db_path)
    if not os.path.exists(path):
        return None
    with sqlite3.connect(path) as conn:
        has_meta = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_meta'"
        ).fetchone()
        if has_meta:
            current = conn.execute(
                "SELECT value FROM schema_meta WHERE key='rule_engine_schema'"
            ).fetchone()
            if current and current[0] == "2":
                return None
        table_names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        profile_count = (
            conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
            if "profiles" in table_names
            else 0
        )
        chart_count = (
            conn.execute("SELECT COUNT(*) FROM bazi_charts").fetchone()[0]
            if "bazi_charts" in table_names
            else 0
        )

    backup_path = None
    if profile_count or chart_count:
        timestamp = (now or datetime.now()).strftime("%Y%m%d%H%M%S")
        backup_path = f"{path}.pre-rule-v2-{timestamp}.bak"
        shutil.copy2(path, backup_path)

    with sqlite3.connect(path) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            if "bazi_charts" in table_names:
                conn.execute("DELETE FROM bazi_charts")
            if "profiles" in table_names:
                conn.execute("DELETE FROM profiles")
            conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
                ("rule_engine_schema", "2"),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return backup_path


def save_profile(profile: dict, chart: dict, report: dict) -> int:
    """
    保存用户资料、命盘和报告，返回 profile_id。
    """
    init_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO profiles
            (name, gender, birth_date, birth_hour, birth_minute, birth_place, use_solar_time, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.get("name", ""),
                profile.get("gender", ""),
                str(profile.get("birth_date", "")),
                _optional_int(profile.get("birth_hour", 0)),
                _optional_int(profile.get("birth_minute", 0)),
                profile.get("birth_place", ""),
                1 if profile.get("use_solar_time") else 0,
                profile.get("note", ""),
                created_at,
            ),
        )
        profile_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO bazi_charts (profile_id, chart_json, report_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                profile_id,
                json.dumps(chart, ensure_ascii=False),
                json.dumps(report, ensure_ascii=False),
                created_at,
            ),
        )
        conn.commit()
        return profile_id


def list_profiles() -> list[dict]:
    """
    返回已保存命盘列表。
    """
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, gender, birth_date, birth_hour, birth_minute, birth_place, use_solar_time, note, created_at
            FROM profiles
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]



def get_profile(profile_id: int) -> dict | None:
    """
    根据 ID 读取命盘档案。
    """
    init_db()
    with _connect() as conn:
        profile_row = conn.execute(
            """
            SELECT id, name, gender, birth_date, birth_hour, birth_minute, birth_place, use_solar_time, note, created_at
            FROM profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()
        chart_row = conn.execute(
            """
            SELECT chart_json, report_json
            FROM bazi_charts
            WHERE profile_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id,),
        ).fetchone()

    if profile_row is None:
        return None
    result = dict(profile_row)
    if chart_row:
        result["chart"] = json.loads(chart_row["chart_json"])
        result["report"] = json.loads(chart_row["report_json"])
    else:
        result["chart"] = {}
        result["report"] = {}
    return result


def load_profile_chart_report(profile_id: int) -> dict | None:
    """
    一次性读取 profile、chart、report。
    """
    return get_profile(profile_id)


def search_profiles(keyword: str = "", gender: str | None = None) -> list[dict]:
    """
    搜索命盘档案。
    """
    init_db()
    clauses = []
    params: list[object] = []
    keyword = keyword.strip()
    if keyword:
        clauses.append("(name LIKE ? OR birth_date LIKE ? OR birth_place LIKE ? OR note LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like, like, like])
    if gender and gender != "全部":
        clauses.append("gender = ?")
        params.append(gender)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT id, name, gender, birth_date, birth_hour, birth_minute, birth_place, use_solar_time, note, created_at
            FROM profiles
            {where}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def update_profile_basic(
    profile_id: int,
    name: str | None = None,
    birth_place: str | None = None,
    note: str | None = None,
) -> None:
    """
    更新命盘基础信息。
    """
    init_db()
    updates = []
    params: list[object] = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if birth_place is not None:
        updates.append("birth_place = ?")
        params.append(birth_place)
    if note is not None:
        updates.append("note = ?")
        params.append(note)
    if not updates:
        return
    params.append(profile_id)
    with _connect() as conn:
        conn.execute(f"UPDATE profiles SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()


def update_report(profile_id: int, report: dict) -> None:
    """
    更新某个命盘的报告。
    """
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE bazi_charts
            SET report_json = ?
            WHERE id = (
                SELECT id FROM bazi_charts
                WHERE profile_id = ?
                ORDER BY id DESC
                LIMIT 1
            )
            """,
            (json.dumps(report, ensure_ascii=False), profile_id),
        )
        conn.commit()


def update_profile_birth_info(profile_id: int, profile: dict) -> None:
    """
    更新命盘出生信息，用于重新排盘。
    """
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE profiles
            SET name = ?,
                gender = ?,
                birth_date = ?,
                birth_hour = ?,
                birth_minute = ?,
                birth_place = ?,
                use_solar_time = ?,
                note = ?
            WHERE id = ?
            """,
            (
                profile.get("name", ""),
                profile.get("gender", ""),
                str(profile.get("birth_date", "")),
                _optional_int(profile.get("birth_hour", 0)),
                _optional_int(profile.get("birth_minute", 0)),
                profile.get("birth_place", ""),
                1 if profile.get("use_solar_time") else 0,
                profile.get("note", ""),
                profile_id,
            ),
        )
        conn.commit()


def update_chart_and_report(profile_id: int, chart: dict, report: dict) -> None:
    """
    覆盖某个命盘最新的 chart 和 report。
    """
    init_db()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chart_json = json.dumps(chart, ensure_ascii=False)
    report_json = json.dumps(report, ensure_ascii=False)
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id FROM bazi_charts
            WHERE profile_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (profile_id,),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE bazi_charts
                SET chart_json = ?, report_json = ?
                WHERE id = ?
                """,
                (chart_json, report_json, row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO bazi_charts (profile_id, chart_json, report_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (profile_id, chart_json, report_json, created_at),
            )
        conn.commit()


def delete_profile(profile_id: int) -> None:
    """
    删除命盘档案。
    """
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM bazi_charts WHERE profile_id = ?", (profile_id,))
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
