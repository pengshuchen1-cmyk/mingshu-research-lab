"""本地错误日志。"""

from __future__ import annotations

import logging
import os
import re

from utils.runtime_mode import is_public_mode


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "app.log")
_SAFE_TEXT = re.compile(r"[^A-Za-z0-9_.:-]+")
_ERROR_TYPE = re.compile(r"[A-Za-z][A-Za-z0-9_.]{0,79}")
_EVENT_CODES = {
    "app_start",
    "chart_build",
    "report_build",
    "privacy_clear",
    "request_error",
}
_AI_EVENT_CODES = {
    "AI_QA_REQUESTED",
    "AI_QA_VALIDATED",
    "AI_QA_FALLBACK",
    "AI_QA_CLEARED",
}


def _sanitize_log_value(value: object, fallback: str = "unknown") -> str:
    cleaned = _SAFE_TEXT.sub("-", str(value or "").strip()).strip("-._:")
    return cleaned[:80] or fallback


def build_safe_log_record(
    *,
    event_code: str,
    request_id: str = "anonymous",
    algorithm_version: str = "unknown",
    duration_ms: float = 0.0,
    success: bool = True,
    error_type: str = "none",
    **_forbidden_fields,
) -> dict:
    return {
        "event_code": event_code if event_code in _EVENT_CODES else "unknown_event",
        "request_id": _sanitize_log_value(request_id),
        "algorithm_version": _sanitize_log_value(algorithm_version),
        "duration_ms": round(max(0.0, float(duration_ms or 0.0)), 2),
        "success": bool(success),
        "error_type": (_ERROR_TYPE.match(str(error_type or "")) or _ERROR_TYPE.match("none")).group(0),
    }


def _latency_bucket(latency_ms: float) -> str:
    value = max(0.0, float(latency_ms or 0.0))
    if value < 1000:
        return "under-1s"
    if value < 3000:
        return "1-3s"
    if value < 10000:
        return "3-10s"
    return "over-10s"


def build_ai_log_record(
    *,
    event_code: str,
    category: str = "other",
    model_alias: str = "local",
    latency_ms: float = 0.0,
    reason_code: str = "none",
    **_forbidden_fields,
) -> dict:
    """Return a strict metadata-only AI audit record."""
    return {
        "event_code": event_code if event_code in _AI_EVENT_CODES else "AI_QA_UNKNOWN",
        "category": _sanitize_log_value(category),
        "model_alias": _sanitize_log_value(model_alias),
        "latency_bucket": _latency_bucket(latency_ms),
        "reason_code": _sanitize_log_value(reason_code, "none"),
    }


def log_ai_event(**metadata: object) -> None:
    get_logger().info("%s", build_ai_log_record(**metadata))


def get_logger() -> logging.Logger:
    """
    返回应用日志对象。
    """
    logger = logging.getLogger("命数研究室")
    if not logger.handlers:
        if is_public_mode():
            handler = logging.StreamHandler()
        else:
            os.makedirs(LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def log_exception(message: str, exc: Exception) -> None:
    """
    写入异常日志。
    """
    record = build_safe_log_record(
        event_code=message,
        success=False,
        error_type=type(exc).__name__,
    )
    get_logger().error("%s", record)
