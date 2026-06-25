"""文本处理工具。"""

from __future__ import annotations


def safe_join(items: list[str], sep: str = "、", fallback: str = "暂无") -> str:
    """
    安全拼接文本列表。
    """
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return sep.join(cleaned) if cleaned else fallback
