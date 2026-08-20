import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base


def test_unconfigured_webhook_never_writes_or_validates_body_provider():
    response = TestClient(app).post(
        "/api/v1/payments/webhooks/wechat",
        json={"event_id": "evt-1", "order_id": "order-1", "provider_trade_no": "trade-1"},
    )
    assert response.status_code == 501


def test_otp_lockout_is_committed_after_bad_requests(tmp_path):
    async def setup():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'otp.db'}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return engine

    engine = asyncio.run(setup())
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            issued = client.post(
                "/api/v1/auth/otp/login/code", json={"phone": "13800138000"}
            )
            assert issued.status_code == 200
            for _ in range(5):
                assert client.post(
                    "/api/v1/auth/otp/login",
                    json={"phone": "13800138000", "code": "000000"},
                ).status_code == 400
            assert client.post(
                "/api/v1/auth/otp/login",
                json={"phone": "13800138000", "code": "000000"},
            ).status_code == 429
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
