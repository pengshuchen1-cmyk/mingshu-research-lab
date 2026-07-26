from __future__ import annotations

import pytest


class ProviderError(Exception):
    def __init__(self, message, *, status_code=None, code=None, error_type=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.type = error_type


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ProviderError("bad key", status_code=401), "invalid_credentials"),
        (
            ProviderError(
                "balance unavailable",
                status_code=403,
                error_type="exceeded_current_quota_error",
            ),
            "insufficient_quota",
        ),
        (ProviderError("forbidden", status_code=403), "invalid_credentials"),
        (ProviderError("slow down", status_code=429), "rate_limited"),
        (TimeoutError("slow"), "timeout"),
        (ConnectionError("offline"), "network_error"),
        (ProviderError("upstream", status_code=503), "service_unavailable"),
    ],
)
def test_shared_error_classifier_is_deterministic(error, expected):
    from services.ai_service_errors import classify_service_error

    assert classify_service_error(error) == expected


def test_service_error_never_exposes_raw_provider_message():
    from services.ai_service_errors import AIServiceError

    error = AIServiceError("invalid_credentials")
    assert str(error) == "invalid_credentials"
    assert error.code == "invalid_credentials"
