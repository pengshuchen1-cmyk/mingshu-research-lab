"""本地错误日志。"""

from __future__ import annotations

import logging
import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "app.log")


def get_logger() -> logging.Logger:
    """
    返回应用日志对象。
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("命数研究室")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_exception(message: str, exc: Exception) -> None:
    """
    写入异常日志。
    """
    get_logger().exception("%s：%s", message, exc)
