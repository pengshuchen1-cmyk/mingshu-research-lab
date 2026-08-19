"""Isolated API smoke coverage: all persistence uses a temporary SQLite database."""

import asyncio

from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.cache import get_redis
from app.database import get_db
from app.main import app
from app.models import Base, User
from app.security import token_for


def test_readyz_returns_503_when_database_query_fails():
    class UnavailableDatabase:
        async def execute(self, statement):
            raise SQLAlchemyError("database unavailable")

    async def override_db():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.get("/readyz")
            assert response.status_code == 503
            assert response.json() == {"detail": "database is not ready"}
    finally:
        app.dependency_overrides.clear()


def test_readyz_returns_503_when_redis_ping_fails():
    class ReadyResult:
        def scalar_one(self):
            return 1

    class AvailableDatabase:
        async def execute(self, statement):
            return ReadyResult()

    class UnavailableRedis:
        async def ping(self):
            raise RedisError("redis unavailable")

    async def override_db():
        yield AvailableDatabase()

    async def override_redis():
        yield UnavailableRedis()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    try:
        with TestClient(app) as client:
            response = client.get("/readyz")
            assert response.status_code == 503
            assert response.json() == {"detail": "redis is not ready"}
    finally:
        app.dependency_overrides.clear()


def test_readyz_returns_503_when_redis_dependency_is_missing():
    class ReadyResult:
        def scalar_one(self):
            return 1

    class AvailableDatabase:
        async def execute(self, statement):
            return ReadyResult()

    async def override_db():
        yield AvailableDatabase()

    async def override_redis():
        yield None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    try:
        with TestClient(app) as client:
            response = client.get("/readyz")
            assert response.status_code == 503
            assert response.json() == {"detail": "redis is not ready"}
    finally:
        app.dependency_overrides.clear()


def test_api_auth_points_admin_and_openapi(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api-smoke.db'}"
    engine = create_async_engine(database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_db():
        async with sessions() as session:
            yield session

    class AvailableRedis:
        async def ping(self):
            return True

    async def override_redis():
        yield AvailableRedis()

    async def make_admin(phone):
        async with sessions() as session:
            user = (await session.execute(select(User).where(User.phone == phone))).scalar_one()
            user.role = "admin"
            await session.commit()
            return token_for(user)

    asyncio.run(setup())
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    try:
        with TestClient(app) as client:
            assert client.get("/healthz").json() == {"status": "ok"}
            # /readyz executes a real query through the FastAPI DB dependency;
            # this test database intentionally has no application data yet.
            ready = client.get("/readyz")
            assert ready.status_code == 200
            assert ready.json() == {"status": "ready"}
            openapi = client.get("/openapi.json")
            assert openapi.status_code == 200
            assert "/api/v1/auth/otp" in openapi.json()["paths"]

            phone = "+8613800138000"
            otp = client.post("/api/v1/auth/otp", json={"phone": phone})
            assert otp.status_code == 200
            login = client.post(
                "/api/v1/auth/verify", json={"phone": phone, "code": otp.json()["development_code"]}
            )
            assert login.status_code == 200
            assert login.json()["new_user"] is True
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            assert client.get("/api/v1/me", headers=headers).json()["points"] == 20

            admin_token = asyncio.run(make_admin(phone))
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            package = {
                "name": "API smoke package",
                "kind": "one_time",
                "points": 100,
                "price_fen": 990,
                "active": True,
            }
            created_package = client.post(
                "/api/v1/admin/packages", json=package, headers=admin_headers
            )
            assert created_package.status_code == 200
            duplicate_package = client.post(
                "/api/v1/admin/packages", json=package, headers=admin_headers
            )
            assert duplicate_package.status_code == 409
            assert duplicate_package.json() == {"detail": "Package name already exists"}

            assert client.put(
                "/api/v1/admin/feature-rules/report",
                json={"points_cost": 3, "active": True},
                headers=admin_headers,
            ).status_code == 200
            consumed = client.post(
                "/api/v1/points/consume",
                json={"feature_code": "report", "idempotency_key": "api-smoke-use-1"},
                headers=headers,
            )
            assert consumed.status_code == 200
            assert consumed.json()["balance"] == 17
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
