"""Document-driven admin, points, payment, and permission regression coverage.

All state is isolated in a temporary SQLite database. The running MySQL/Redis
development stack is never mutated by this module.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import services
from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base, PaymentOrder, User


def test_admin_points_payments_and_statistics_matrix(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'function-matrix.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_db():
        async with sessions() as session:
            yield session

    async def promote_admin(phone: str):
        async with sessions() as session:
            admin = (await session.execute(select(User).where(User.phone == phone))).scalar_one()
            admin.role = "admin"
            await session.commit()

    async def seed_paid_orders(user_id: str, package_id: str):
        paid_at = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
        async with sessions() as session:
            session.add_all(
                [
                    PaymentOrder(
                        user_id=user_id,
                        package_id=package_id,
                        provider="wechat",
                        amount_fen=990,
                        status="paid",
                        provider_trade_no="paid-wechat-1",
                        paid_at=paid_at,
                    ),
                    PaymentOrder(
                        user_id=user_id,
                        package_id=package_id,
                        provider="wechat",
                        amount_fen=990,
                        status="paid",
                        provider_trade_no="paid-wechat-2",
                        paid_at=paid_at + timedelta(minutes=1),
                    ),
                    PaymentOrder(
                        user_id=user_id,
                        package_id=package_id,
                        provider="alipay",
                        amount_fen=1990,
                        status="paid",
                        provider_trade_no="paid-alipay-1",
                        paid_at=paid_at,
                    ),
                ]
            )
            await session.commit()
        return paid_at

    asyncio.run(setup())
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            def register(phone: str):
                response = client.post(
                    "/api/v1/auth/password/register",
                    json={"phone": phone, "password": "TestPassword123"},
                )
                assert response.status_code == 201, response.text
                return response.json()

            admin_phone = "+8613900001001"
            user_phone = "+8613900001002"
            other_phone = "+8613900001003"
            admin_tokens = register(admin_phone)
            user_tokens = register(user_phone)
            other_tokens = register(other_phone)
            asyncio.run(promote_admin(admin_phone))

            admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
            user_headers = {"Authorization": f"Bearer {user_tokens['access_token']}"}
            other_headers = {"Authorization": f"Bearer {other_tokens['access_token']}"}

            # Every admin surface rejects missing and ordinary-user credentials.
            permission_requests = [
                ("get", "/api/v1/admin/packages", None),
                ("get", "/api/v1/admin/users", None),
                ("get", "/api/v1/admin/recharge-statistics", None),
                (
                    "post",
                    "/api/v1/admin/packages",
                    {
                        "name": "forbidden",
                        "kind": "one_time",
                        "points": 1,
                        "price_fen": 1,
                    },
                ),
                (
                    "put",
                    "/api/v1/admin/feature-rules/forbidden",
                    {"points_cost": 1},
                ),
                (
                    "patch",
                    "/api/v1/admin/users/missing/active",
                    {"is_active": False},
                ),
            ]
            for method, path, body in permission_requests:
                missing = client.request(method.upper(), path, json=body)
                ordinary = client.request(
                    method.upper(), path, json=body, headers=user_headers
                )
                assert missing.status_code == 401
                assert ordinary.status_code == 403

            active_package = {
                "name": "一次性 100 点",
                "kind": "one_time",
                "points": 100,
                "price_fen": 990,
                "active": True,
            }
            created = client.post(
                "/api/v1/admin/packages", json=active_package, headers=admin_headers
            )
            assert created.status_code == 200, created.text
            package_id = created.json()["id"]
            assert client.post(
                "/api/v1/admin/packages", json=active_package, headers=admin_headers
            ).status_code == 409

            inactive = client.post(
                "/api/v1/admin/packages",
                json={
                    "name": "停用月包",
                    "kind": "monthly",
                    "points": 200,
                    "price_fen": 1990,
                    "active": False,
                },
                headers=admin_headers,
            )
            assert inactive.status_code == 200
            for field, value in [("points", 0), ("points", -1), ("price_fen", 0)]:
                invalid = {**active_package, "name": f"invalid-{field}-{value}", field: value}
                assert client.post(
                    "/api/v1/admin/packages", json=invalid, headers=admin_headers
                ).status_code == 422
            assert client.post(
                "/api/v1/admin/packages",
                json={**active_package, "name": "invalid-kind", "kind": "yearly"},
                headers=admin_headers,
            ).status_code == 422

            all_packages = client.get("/api/v1/admin/packages", headers=admin_headers)
            assert all_packages.status_code == 200
            assert {item["active"] for item in all_packages.json()} == {True, False}
            public_packages = client.get("/api/v1/payments/packages")
            assert public_packages.status_code == 200
            assert [item["id"] for item in public_packages.json()] == [package_id]

            before_points = client.get("/api/v1/me", headers=user_headers).json()["points"]
            for provider in ("wechat", "alipay"):
                order = client.post(
                    "/api/v1/payments/orders",
                    json={"package_id": package_id, "provider": provider},
                    headers=user_headers,
                )
                assert order.status_code == 200
                assert order.json()["status"] == "pending"
                assert order.json()["provider"] == provider
                assert order.json()["payment_payload"] is None
            assert client.post(
                "/api/v1/payments/orders",
                json={"package_id": inactive.json()["id"], "provider": "wechat"},
                headers=user_headers,
            ).status_code == 404
            assert client.get("/api/v1/me", headers=user_headers).json()["points"] == before_points

            # Feature rules create/update, zero-cost, inactive, idempotency, and overdraft.
            report_rule = client.put(
                "/api/v1/admin/feature-rules/report",
                json={"points_cost": 3},
                headers=admin_headers,
            )
            assert report_rule.status_code == 200
            assert report_rule.json()["active"] is True
            first = client.post(
                "/api/v1/points/consume",
                json={"feature_code": "report", "idempotency_key": "matrix-report-001"},
                headers=user_headers,
            )
            assert first.status_code == 200
            assert first.json()["balance"] == 17
            repeated = client.post(
                "/api/v1/points/consume",
                json={"feature_code": "report", "idempotency_key": "matrix-report-001"},
                headers=user_headers,
            )
            assert repeated.json() == first.json()

            assert client.put(
                "/api/v1/admin/feature-rules/other",
                json={"points_cost": 1},
                headers=admin_headers,
            ).status_code == 200
            assert client.post(
                "/api/v1/points/consume",
                json={"feature_code": "other", "idempotency_key": "matrix-report-001"},
                headers=user_headers,
            ).status_code == 409
            other_user_consume = client.post(
                "/api/v1/points/consume",
                json={"feature_code": "report", "idempotency_key": "matrix-report-001"},
                headers=other_headers,
            )
            assert other_user_consume.status_code == 200
            assert other_user_consume.json()["balance"] == 17

            assert client.put(
                "/api/v1/admin/feature-rules/free",
                json={"points_cost": 0},
                headers=admin_headers,
            ).status_code == 200
            free = client.post(
                "/api/v1/points/consume",
                json={"feature_code": "free", "idempotency_key": "matrix-free-001"},
                headers=user_headers,
            )
            assert free.status_code == 200
            assert free.json()["balance"] == 17
            assert client.put(
                "/api/v1/admin/feature-rules/disabled",
                json={"points_cost": 1, "active": False},
                headers=admin_headers,
            ).status_code == 200
            assert client.post(
                "/api/v1/points/consume",
                json={"feature_code": "disabled", "idempotency_key": "matrix-disabled-001"},
                headers=user_headers,
            ).status_code == 404
            assert client.put(
                "/api/v1/admin/feature-rules/expensive",
                json={"points_cost": 100},
                headers=admin_headers,
            ).status_code == 200
            assert client.post(
                "/api/v1/points/consume",
                json={"feature_code": "expensive", "idempotency_key": "matrix-expensive-001"},
                headers=user_headers,
            ).status_code == 409
            assert client.get("/api/v1/me", headers=user_headers).json()["points"] == 17

            users = client.get("/api/v1/admin/users?offset=0&limit=1", headers=admin_headers)
            assert users.status_code == 200
            assert len(users.json()) == 1
            exposed = users.json()[0]
            assert "has_password" in exposed
            for secret in (
                "password_hash",
                "auth_version",
                "password_failed_attempts",
                "password_locked_until",
            ):
                assert secret not in exposed
            filtered = client.get(
                "/api/v1/admin/users?phone=1002", headers=admin_headers
            )
            assert [item["phone"] for item in filtered.json()] == [user_phone]
            for query in ("offset=-1", "limit=0", "limit=101"):
                assert client.get(
                    f"/api/v1/admin/users?{query}", headers=admin_headers
                ).status_code == 422

            user_id = client.get("/api/v1/me", headers=user_headers).json()["id"]
            disabled = client.patch(
                f"/api/v1/admin/users/{user_id}/active",
                json={"is_active": False},
                headers=admin_headers,
            )
            assert disabled.status_code == 200
            assert disabled.json() == {"id": user_id, "is_active": False}
            assert client.get("/api/v1/me", headers=user_headers).status_code == 401
            assert client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": user_tokens["refresh_token"]},
            ).status_code == 401
            assert client.patch(
                f"/api/v1/admin/users/{user_id}/active",
                json={"is_active": True},
                headers=admin_headers,
            ).status_code == 200
            assert client.get("/api/v1/me", headers=user_headers).status_code == 200
            assert client.patch(
                "/api/v1/admin/users/not-a-uuid/active",
                json={"is_active": False},
                headers=admin_headers,
            ).status_code == 404
            assert client.patch(
                f"/api/v1/admin/users/{user_id}/active",
                json={},
                headers=admin_headers,
            ).status_code == 422

            paid_at = asyncio.run(seed_paid_orders(user_id, package_id))
            stats = client.get("/api/v1/admin/recharge-statistics", headers=admin_headers)
            assert stats.status_code == 200
            by_provider = {item["provider"]: item for item in stats.json()}
            assert by_provider["wechat"] == {
                "provider": "wechat",
                "orders": 2,
                "amount_fen": 1980,
            }
            assert by_provider["alipay"] == {
                "provider": "alipay",
                "orders": 1,
                "amount_fen": 1990,
            }
            wechat = client.get(
                "/api/v1/admin/recharge-statistics?provider=wechat",
                headers=admin_headers,
            )
            assert [item["provider"] for item in wechat.json()] == ["wechat"]
            by_package = client.get(
                f"/api/v1/admin/recharge-statistics?package_id={package_id}",
                headers=admin_headers,
            )
            assert sum(item["orders"] for item in by_package.json()) == 3
            boundary = paid_at.isoformat()
            at_boundary = client.get(
                "/api/v1/admin/recharge-statistics",
                params={"start_at": boundary, "end_at": boundary},
                headers=admin_headers,
            )
            assert sum(item["orders"] for item in at_boundary.json()) == 2
            reversed_range = client.get(
                "/api/v1/admin/recharge-statistics",
                params={
                    "start_at": (paid_at + timedelta(days=1)).isoformat(),
                    "end_at": paid_at.isoformat(),
                },
                headers=admin_headers,
            )
            assert reversed_range.status_code == 422
            assert reversed_range.json() == {"detail": "start_at must be before end_at"}
            assert client.get(
                "/api/v1/admin/recharge-statistics?start_at=not-a-date",
                headers=admin_headers,
            ).status_code == 422

            # The current product permits self-deactivation; verify the documented risk
            # only after all other admin assertions have completed.
            admin_id = client.get("/api/v1/me", headers=admin_headers).json()["id"]
            assert client.patch(
                f"/api/v1/admin/users/{admin_id}/active",
                json={"is_active": False},
                headers=admin_headers,
            ).status_code == 200
            assert client.get("/api/v1/admin/users", headers=admin_headers).status_code == 401
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_environment_dependent_placeholder_boundaries(monkeypatch):
    monkeypatch.setattr(services, "sms_provider", None)
    with TestClient(app) as client:
        login_otp = client.post(
            "/api/v1/auth/otp/login/code", json={"phone": "+8613900001091"}
        )
        assert login_otp.status_code == 503
        assert login_otp.json() == {"detail": "SMS provider is not configured"}

        reset_otp = client.post(
            "/api/v1/auth/password/reset/otp", json={"phone": "+8613900001092"}
        )
        assert reset_otp.status_code == 503

        monkeypatch.setattr(settings, "wechat_app_id", "test-placeholder-app")
        configured_placeholder = client.get("/api/v1/auth/wechat/qr")
        assert configured_placeholder.status_code == 200
        assert "message" in configured_placeholder.json()
