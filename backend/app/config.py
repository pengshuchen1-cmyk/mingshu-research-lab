from pathlib import Path
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio.connection import parse_url as parse_redis_url
from sqlalchemy.engine import make_url


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
    cors_origins: list[str] = []
    redis_url: str
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    alipay_app_id: str = ""
    alipay_private_key: str = ""

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL must not be empty")
        make_url(value)
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise ValueError("REDIS_URL must be a redis:// or rediss:// URL with a host")
        try:
            parsed.port
            if parsed.path not in {"", "/"} and int(parsed.path.removeprefix("/")) < 0:
                raise ValueError
        except ValueError as error:
            raise ValueError("REDIS_URL contains an invalid port or database number") from error
        # Redis' own parser also validates the port, database number and typed
        # query parameters now, instead of failing inside a request dependency.
        parse_redis_url(value)
        return value


settings = Settings()
