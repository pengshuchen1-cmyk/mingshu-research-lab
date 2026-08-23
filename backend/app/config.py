from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio.connection import parse_url as parse_redis_url
from sqlalchemy.engine import make_url

from .errors import SystemErrorMessages

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    environment: str = "development"
    database_url: str
    jwt_secret: str = "development-secret-change-me-please"
    jwt_issuer: str = "mingshu-api"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    registration_bonus_points: int = 20
    otp_ttl_seconds: int = 300
    otp_resend_seconds: int = 60
    otp_daily_limit: int = 10
    otp_max_attempts: int = 5
    password_max_attempts: int = Field(default=5, ge=1, le=20)
    password_lock_minutes: int = Field(default=15, ge=1, le=1440)
    profile_edit_cooldown_days: int = Field(default=30, ge=0)
    cors_origins: list[str] = []
    redis_url: str
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    ai_provider: str = "local"
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    ai_base_url: str = ""
    ai_reasoning_effort: str = "low"
    ai_timeout_seconds: int = Field(default=30, ge=5, le=90)
    ai_per_user_per_minute: int = Field(default=3, ge=1, le=60)
    ai_per_user_daily_requests: int = Field(default=30, ge=1, le=1000)
    ai_daily_token_budget: int = Field(default=500_000, ge=1000)
    ai_max_concurrent_requests: int = Field(default=4, ge=1, le=100)

    @field_validator("ai_provider")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"local", "kimi", "openai"}:
            raise ValueError("AI_PROVIDER must be local, kimi, or openai")
        return normalized

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(SystemErrorMessages.DATABASE_URL_EMPTY)
        make_url(value)
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise ValueError(SystemErrorMessages.REDIS_URL_INVALID)

        try:
            port = parsed.port
        except ValueError as error:
            raise ValueError(SystemErrorMessages.REDIS_PORT_INVALID) from error

        if port is not None and not 1 <= port <= 65535:
            raise ValueError(SystemErrorMessages.REDIS_PORT_OUT_OF_RANGE)

        database_text = parsed.path.removeprefix("/")
        try:
            database_number = int(database_text) if database_text else 0
        except ValueError as error:
            raise ValueError(SystemErrorMessages.REDIS_DATABASE_INVALID) from error

        if database_number < 0:
            raise ValueError(SystemErrorMessages.REDIS_DATABASE_NEGATIVE)

        # Redis' own parser also validates the port, database number and typed
        # query parameters now, instead of failing inside a request dependency.
        parse_redis_url(value)
        return value


# BaseSettings supplies required values from process environment variables or
# backend/.env at runtime; Pylance cannot infer those dynamic settings sources.
settings = Settings()  # pyright: ignore[reportCallIssue]
