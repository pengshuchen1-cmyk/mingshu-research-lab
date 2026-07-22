"""本地数据备份与导入。"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

from utils import database
from utils.runtime_mode import require_local_storage


def export_profiles_to_json() -> str:
    """
    导出所有命盘为 JSON 字符串。
    """
    require_local_storage()
    items = []
    for profile in database.list_profiles():
        loaded = database.get_profile(profile["id"])
        if loaded:
            items.append(loaded)
    payload = {
        "app": "命数研究室",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profiles": items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def import_profiles_from_json(payload: str) -> dict:
    """
    从 JSON 字符串导入命盘。
    """
    require_local_storage()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return {"imported": 0, "error": f"导入文件格式有误：{exc}"}
    profiles = data.get("profiles", [])
    imported = 0
    for item in profiles:
        profile = {
            "name": item.get("name", ""),
            "gender": item.get("gender", ""),
            "calendar_type": item.get("calendar_type", "solar"),
            "birth_date": item.get("birth_date", ""),
            "lunar_birth_date": item.get("lunar_birth_date"),
            "birth_hour": item.get("birth_hour", 0),
            "birth_minute": item.get("birth_minute", 0),
            "birth_place": item.get("birth_place", ""),
            "is_leap_month": bool(item.get("is_leap_month")),
            "time_mode": "china_standard",
            "use_solar_time": False,
            "note": item.get("note", ""),
        }
        database.save_profile(profile, item.get("chart", {}), item.get("report", {}))
        imported += 1
    return {"imported": imported}


def backup_database(target_path: str | None = None) -> dict:
    """
    备份 SQLite 数据库文件。
    """
    require_local_storage()
    if not os.path.exists(database.DB_PATH):
        return {"ok": False, "message": "当前还没有可备份的数据库。"}
    target_path = target_path or os.path.join(
        os.path.dirname(database.DB_PATH),
        f"profiles_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
    )
    shutil.copy2(database.DB_PATH, target_path)
    return {"ok": True, "path": target_path}


def restore_database(source_path: str) -> dict:
    """
    从 SQLite 文件恢复数据库。
    """
    require_local_storage()
    if not os.path.exists(source_path):
        return {"ok": False, "message": "未找到要恢复的数据库文件。"}
    os.makedirs(os.path.dirname(database.DB_PATH), exist_ok=True)
    shutil.copy2(source_path, database.DB_PATH)
    return {"ok": True, "path": database.DB_PATH}
