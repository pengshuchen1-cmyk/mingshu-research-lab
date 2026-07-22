"""SQLite 本地数据库。"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime

from utils.runtime_mode import require_local_storage

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "profiles.db")


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
                int(profile.get("birth_hour", 0)),
                int(profile.get("birth_minute", 0)),
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



def _ensure_chart_fields(chart: dict) -> dict:
    """填充旧版本命盘缺失的计算字段（向后兼容）。

    早期版本导出/保存的命盘可能缺少 five_elements、ten_god_counts、
    day_master_strength 等计算字段，重新补齐以免 UI 页面空显示。
    """
    if not chart or not chart.get("pillars"):
        return chart
    if "five_elements" not in chart or not chart["five_elements"]:
        try:
            from core.five_elements import calculate_five_elements
            chart["five_elements"] = calculate_five_elements(chart)
        except Exception:
            pass
    if "ten_god_counts" not in chart or not chart["ten_god_counts"]:
        try:
            from core.ten_gods import count_ten_gods
            chart["ten_god_counts"] = count_ten_gods(chart)
        except Exception:
            pass
    if "day_master_strength" not in chart or not chart["day_master_strength"]:
        try:
            from core.strength_engine import analyze_day_master_strength
            chart["day_master_strength"] = analyze_day_master_strength(chart)
        except Exception:
            pass
    return chart


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
        result["chart"] = _ensure_chart_fields(json.loads(chart_row["chart_json"]))
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
                int(profile.get("birth_hour", 0)),
                int(profile.get("birth_minute", 0)),
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
