import asyncio

import pytest
from pydantic import ValidationError

from app.config import ENV_FILE, Settings, settings
from app.main import validate_production_settings


def test_runtime_service_urls_are_required_without_env_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.delenv("REDIS_URL")

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing = {item["loc"][0] for item in error.value.errors() if item["type"] == "missing"}
    assert missing == {"database_url", "redis_url"}


def test_env_file_is_backend_absolute_path():
    configured = Settings.model_config["env_file"]
    assert configured == ENV_FILE
    assert ENV_FILE.is_absolute()
    assert ENV_FILE.name == ".env"


def test_profile_edit_cooldown_is_configurable():
    configured = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://127.0.0.1:6379/0",
        profile_edit_cooldown_days=7,
    )

    assert configured.profile_edit_cooldown_days == 7

    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        Settings(
            _env_file=None,
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url="redis://127.0.0.1:6379/0",
            profile_edit_cooldown_days=-1,
        )


def test_app_timezone_is_configurable_and_validated():
    configured = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://127.0.0.1:6379/0",
        app_timezone="Asia/Hong_Kong",
    )

    assert configured.app_timezone == "Asia/Hong_Kong"

    with pytest.raises(ValidationError, match="valid IANA time zone"):
        Settings(
            _env_file=None,
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url="redis://127.0.0.1:6379/0",
            app_timezone="not/a-timezone",
        )


@pytest.mark.parametrize(
    ("redis_url", "expected"),
    [
        ("redis://127.0.0.1:not-a-port/0", "invalid port"),
        ("redis://127.0.0.1:6379/not-a-database-number", "invalid database number"),
        ("redis://127.0.0.1:6379/-1", "must not be negative"),
    ],
)
def test_invalid_redis_url_fails_during_configuration(redis_url, expected):
    with pytest.raises(ValidationError, match=expected):
        Settings(
            _env_file=None,
            database_url="sqlite+aiosqlite:///:memory:",
            redis_url=redis_url,
        )


def test_production_requires_mysql_asyncmy(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "jwt_secret", "a" * 32)
    monkeypatch.setattr(settings, "database_url", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:6379/0")

    with pytest.raises(RuntimeError, match="mysql\\+asyncmy"):
        asyncio.run(validate_production_settings())


def test_production_requires_redis_url(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "jwt_secret", "a" * 32)
    monkeypatch.setattr(
        settings,
        "database_url",
        "mysql+asyncmy://mingshu:test@mysql:3306/mingshu",
    )
    monkeypatch.setattr(settings, "redis_url", "")

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        asyncio.run(validate_production_settings())


@pytest.mark.parametrize(
    ("jwt_secret", "database_url", "redis_url", "expected"),
    [
        (
            "REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS",
            "mysql+asyncmy://mingshu:valid-random-password@mysql:3306/mingshu",
            "redis://:valid-random-password@redis:6379/0",
            "JWT_SECRET",
        ),
        (
            "a" * 32,
            "mysql+asyncmy://mingshu:MYSQL_PASSWORD_64_LOWERCASE_HEX@mysql:3306/mingshu",
            "redis://:valid-random-password@redis:6379/0",
            "DATABASE_URL",
        ),
        (
            "a" * 32,
            "mysql+asyncmy://mingshu:valid-random-password@mysql:3306/mingshu",
            "redis://:REDIS_PASSWORD_64_LOWERCASE_HEX@redis:6379/0",
            "REDIS_URL",
        ),
    ],
)
def test_production_rejects_known_placeholder_secrets(
    monkeypatch, jwt_secret, database_url, redis_url, expected
):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "jwt_secret", jwt_secret)
    monkeypatch.setattr(settings, "database_url", database_url)
    monkeypatch.setattr(settings, "redis_url", redis_url)

    with pytest.raises(RuntimeError, match=expected):
        asyncio.run(validate_production_settings())
