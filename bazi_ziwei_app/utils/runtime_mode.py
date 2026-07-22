"""区分公网无落盘模式与本机档案模式。"""

from __future__ import annotations

import os


RUNTIME_ENV_KEY = "MINGSHU_RUNTIME_MODE"


def get_runtime_mode() -> str:
    value = os.getenv(RUNTIME_ENV_KEY, "public").strip().lower()
    return "local" if value == "local" else "public"


def is_public_mode() -> bool:
    return get_runtime_mode() == "public"


def require_local_storage() -> None:
    if is_public_mode():
        raise RuntimeError("公网模式不允许读取或写入本机命盘数据库。")
