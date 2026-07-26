"""Privacy-safe error normalization shared by cloud AI providers."""

from __future__ import annotations

_QUOTA_ERROR_MARKERS = {
    "insufficient_quota",
    "exceeded_current_quota",
    "exceeded_current_quota_error",
    "balance_not_enough",
    "billing",
    "quota",
}


class AIServiceError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def classify_service_error(exc: Exception) -> str:
    exception_name = type(exc).__name__.lower()
    status = getattr(exc, "status_code", None)
    code = str(getattr(exc, "code", "") or "").lower()
    error_type = str(getattr(exc, "type", "") or "").lower()

    if isinstance(exc, TimeoutError) or "timeout" in exception_name:
        return "timeout"
    if {code, error_type} & _QUOTA_ERROR_MARKERS and status in {402, 403, 429}:
        return "insufficient_quota"
    if status in {401, 403}:
        return "invalid_credentials"
    if status == 429:
        return "rate_limited"
    if status in {500, 502, 503, 504}:
        return "service_unavailable"
    if (
        isinstance(exc, (ConnectionError, OSError))
        or "connection" in exception_name
    ):
        return "network_error"
    return "service_unavailable"
