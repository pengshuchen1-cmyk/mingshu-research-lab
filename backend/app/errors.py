"""Central definitions for business-facing API errors.

Keep HTTP status codes and client-visible messages here so routers, services,
and dependencies do not duplicate them.  ``APIError`` intentionally preserves
FastAPI's existing ``{"detail": "..."}`` response shape for compatibility.
"""

from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Stable internal code, HTTP status, and client-visible message."""

    code: str
    status_code: int
    message: str


class Errors:
    """Single source of truth for API business errors."""

    INVALID_PHONE = ErrorDefinition(
        "AUTH_INVALID_PHONE", status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid phone number"
    )
    INVALID_REFRESH_TOKEN = ErrorDefinition(
        "AUTH_INVALID_REFRESH_TOKEN", status.HTTP_401_UNAUTHORIZED, "Invalid refresh token"
    )
    REFRESH_TOKEN_REQUIRED = ErrorDefinition(
        "AUTH_REFRESH_TOKEN_REQUIRED", status.HTTP_401_UNAUTHORIZED, "Refresh token required"
    )
    INVALID_OR_EXPIRED_TOKEN = ErrorDefinition(
        "AUTH_INVALID_OR_EXPIRED_TOKEN",
        status.HTTP_401_UNAUTHORIZED,
        "Invalid or expired token",
    )
    ACCESS_TOKEN_REQUIRED = ErrorDefinition(
        "AUTH_ACCESS_TOKEN_REQUIRED", status.HTTP_401_UNAUTHORIZED, "Access token required"
    )
    USER_UNAVAILABLE = ErrorDefinition(
        "AUTH_USER_UNAVAILABLE", status.HTTP_401_UNAUTHORIZED, "User unavailable"
    )
    ADMINISTRATOR_REQUIRED = ErrorDefinition(
        "AUTH_ADMINISTRATOR_REQUIRED",
        status.HTTP_403_FORBIDDEN,
        "Administrator role required",
    )
    SMS_PROVIDER_NOT_CONFIGURED = ErrorDefinition(
        "AUTH_SMS_PROVIDER_NOT_CONFIGURED",
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "SMS provider is not configured",
    )
    OTP_DAILY_LIMIT_REACHED = ErrorDefinition(
        "AUTH_OTP_DAILY_LIMIT_REACHED",
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Daily OTP limit reached",
    )
    OTP_RESEND_TOO_SOON = ErrorDefinition(
        "AUTH_OTP_RESEND_TOO_SOON",
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Please wait before requesting another OTP",
    )
    OTP_ATTEMPT_LIMIT_REACHED = ErrorDefinition(
        "AUTH_OTP_ATTEMPT_LIMIT_REACHED",
        status.HTTP_429_TOO_MANY_REQUESTS,
        "OTP attempt limit reached",
    )
    OTP_INVALID_OR_EXPIRED = ErrorDefinition(
        "AUTH_OTP_INVALID_OR_EXPIRED",
        status.HTTP_400_BAD_REQUEST,
        "Invalid or expired OTP",
    )
    INVALID_PASSWORD_CREDENTIALS = ErrorDefinition(
        "AUTH_INVALID_PASSWORD_CREDENTIALS",
        status.HTTP_401_UNAUTHORIZED,
        "Invalid phone number or password",
    )
    CURRENT_PASSWORD_REQUIRED = ErrorDefinition(
        "AUTH_CURRENT_PASSWORD_REQUIRED",
        status.HTTP_400_BAD_REQUEST,
        "Current password is required",
    )
    PASSWORD_UNCHANGED = ErrorDefinition(
        "AUTH_PASSWORD_UNCHANGED",
        status.HTTP_409_CONFLICT,
        "New password must be different from the current password",
    )
    PASSWORD_LOGIN_LOCKED = ErrorDefinition(
        "AUTH_PASSWORD_LOGIN_LOCKED",
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Password login is temporarily locked; reset the password or try again later",
    )
    WECHAT_QR_NOT_CONFIGURED = ErrorDefinition(
        "AUTH_WECHAT_QR_NOT_CONFIGURED",
        status.HTTP_501_NOT_IMPLEMENTED,
        "WeChat QR login is not configured",
    )

    PACKAGE_NAME_ALREADY_EXISTS = ErrorDefinition(
        "PACKAGE_NAME_ALREADY_EXISTS", status.HTTP_409_CONFLICT, "Package name already exists"
    )
    PACKAGE_UNAVAILABLE = ErrorDefinition(
        "PACKAGE_UNAVAILABLE", status.HTTP_404_NOT_FOUND, "Package unavailable"
    )
    USER_NOT_FOUND = ErrorDefinition(
        "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND, "User not found"
    )
    INVALID_STATISTICS_TIME_RANGE = ErrorDefinition(
        "STATISTICS_INVALID_TIME_RANGE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "start_at must be before end_at",
    )

    IDEMPOTENCY_KEY_CONFLICT = ErrorDefinition(
        "POINTS_IDEMPOTENCY_KEY_CONFLICT",
        status.HTTP_409_CONFLICT,
        "Idempotency key was reused for a different operation",
    )
    INSUFFICIENT_POINTS = ErrorDefinition(
        "POINTS_INSUFFICIENT", status.HTTP_409_CONFLICT, "Insufficient points"
    )
    FEATURE_RULE_NOT_FOUND = ErrorDefinition(
        "POINTS_FEATURE_RULE_NOT_FOUND", status.HTTP_404_NOT_FOUND, "Feature rule not found"
    )

    BIRTH_PROFILE_NOT_FOUND = ErrorDefinition(
        "CHART_BIRTH_PROFILE_NOT_FOUND", status.HTTP_404_NOT_FOUND, "Birth profile not found"
    )
    BIRTH_PROFILE_EDIT_COOLDOWN = ErrorDefinition(
        "CHART_BIRTH_PROFILE_EDIT_COOLDOWN",
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Birth profile cannot be edited again during the configured cooldown period",
    )
    BIRTH_PROFILE_INVALID = ErrorDefinition(
        "CHART_BIRTH_PROFILE_INVALID",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Birth information could not be converted into a chart",
    )
    CHART_CONFIRMATION_MISMATCH = ErrorDefinition(
        "CHART_CONFIRMATION_MISMATCH",
        status.HTTP_409_CONFLICT,
        "Chart result changed; preview and confirm the birth information again",
    )
    CHART_NOT_FOUND = ErrorDefinition(
        "CHART_NOT_FOUND", status.HTTP_404_NOT_FOUND, "Chart has not been generated"
    )
    PERSONAL_FORTUNE_UNAVAILABLE = ErrorDefinition(
        "FORTUNE_PERSONAL_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Personal fortune could not be generated from this chart",
    )
    CHART_ANALYSIS_UNAVAILABLE = ErrorDefinition(
        "CHART_ANALYSIS_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Chart interpretation could not be generated",
    )
    LUCK_CYCLES_UNAVAILABLE = ErrorDefinition(
        "FORTUNE_LUCK_CYCLES_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Luck cycles could not be generated from this profile",
    )
    SIXTY_JIAZI_QUERY_CONFLICT = ErrorDefinition(
        "KNOWLEDGE_SIXTY_JIAZI_QUERY_CONFLICT",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Use either year or pillar, not both",
    )
    SIXTY_JIAZI_NOT_FOUND = ErrorDefinition(
        "KNOWLEDGE_SIXTY_JIAZI_NOT_FOUND",
        status.HTTP_404_NOT_FOUND,
        "Sixty Jiazi entry not found",
    )
    REPORT_EXPORT_UNAVAILABLE = ErrorDefinition(
        "REPORT_EXPORT_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Report could not be exported",
    )
    COMPATIBILITY_UNAVAILABLE = ErrorDefinition(
        "COMPATIBILITY_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Compatibility analysis could not be generated",
    )
    ZIWEI_UNAVAILABLE = ErrorDefinition(
        "ZIWEI_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Ziwei analysis could not be generated from this profile",
    )
    AI_QUESTION_UNAVAILABLE = ErrorDefinition(
        "AI_QUESTION_UNAVAILABLE",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The question could not be analyzed safely",
    )
    AI_CONVERSATION_NOT_FOUND = ErrorDefinition(
        "AI_CONVERSATION_NOT_FOUND",
        status.HTTP_404_NOT_FOUND,
        "AI conversation not found",
    )
    AI_CONVERSATION_NOT_ACTIVE = ErrorDefinition(
        "AI_CONVERSATION_NOT_ACTIVE",
        status.HTTP_409_CONFLICT,
        "AI conversation is not active",
    )
    AI_CONVERSATION_BUSY = ErrorDefinition(
        "AI_CONVERSATION_BUSY",
        status.HTTP_409_CONFLICT,
        "Another question is already being processed for this conversation",
    )
    AI_IDEMPOTENCY_KEY_CONFLICT = ErrorDefinition(
        "AI_IDEMPOTENCY_KEY_CONFLICT",
        status.HTTP_409_CONFLICT,
        "Idempotency key was reused for a different question",
    )
    AI_REQUEST_PREVIOUSLY_FAILED = ErrorDefinition(
        "AI_REQUEST_PREVIOUSLY_FAILED",
        status.HTTP_409_CONFLICT,
        "The previous request with this idempotency key failed; retry with a new key",
    )
    AI_CURSOR_INVALID = ErrorDefinition(
        "AI_CURSOR_INVALID",
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Invalid AI conversation cursor",
    )

    UNKNOWN_PAYMENT_PROVIDER = ErrorDefinition(
        "PAYMENT_PROVIDER_UNKNOWN", status.HTTP_404_NOT_FOUND, "Unknown payment provider"
    )
    PAYMENT_SIGNATURE_NOT_CONFIGURED = ErrorDefinition(
        "PAYMENT_SIGNATURE_NOT_CONFIGURED",
        status.HTTP_501_NOT_IMPLEMENTED,
        "Payment provider signature verification is not configured",
    )

    DATABASE_NOT_READY = ErrorDefinition(
        "OPERATIONS_DATABASE_NOT_READY",
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "database is not ready",
    )
    REDIS_NOT_READY = ErrorDefinition(
        "OPERATIONS_REDIS_NOT_READY",
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "redis is not ready",
    )


class SystemErrorMessages:
    """Configuration and startup failures that are not returned by the API."""

    DATABASE_URL_EMPTY = "DATABASE_URL must not be empty"
    REDIS_URL_INVALID = "REDIS_URL must be a redis:// or rediss:// URL with a host"
    REDIS_PORT_INVALID = "REDIS_URL contains an invalid port"
    REDIS_PORT_OUT_OF_RANGE = "REDIS_URL port must be between 1 and 65535"
    REDIS_DATABASE_INVALID = "REDIS_URL contains an invalid database number"
    REDIS_DATABASE_NEGATIVE = "REDIS_URL database number must not be negative"
    APP_TIMEZONE_INVALID = "APP_TIMEZONE must be a valid IANA time zone"

    JWT_SECRET_INSECURE = (
        "JWT_SECRET must be replaced with a random value of at least 32 characters"
    )
    PRODUCTION_DATABASE_DRIVER_INVALID = "production DATABASE_URL must use mysql+asyncmy"
    PRODUCTION_DATABASE_PASSWORD_INVALID = (
        "production DATABASE_URL must contain a non-placeholder password"
    )
    PRODUCTION_REDIS_REQUIRED = "production REDIS_URL is required"
    PRODUCTION_REDIS_PASSWORD_INVALID = (
        "production REDIS_URL must contain a non-placeholder password"
    )
    DATABASE_READINESS_UNEXPECTED = "unexpected database readiness result"
    REDIS_READINESS_UNEXPECTED = "unexpected Redis readiness result"
    ALEMBIC_URL_NOT_CONFIGURED = "Alembic sqlalchemy.url is not configured"


class APIError(HTTPException):
    """Raise one catalogued API error while retaining the legacy response body."""

    def __init__(self, error: ErrorDefinition):
        self.error_code = error.code
        super().__init__(status_code=error.status_code, detail=error.message)
