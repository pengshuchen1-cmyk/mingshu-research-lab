import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base, User
from app.passwords import hash_password, password_needs_rehash, verify_password
from app.security import token_for


def test_scrypt_hashes_are_salted_and_self_describing():
    first = hash_password("一个足够长的测试密码")
    second = hash_password("一个足够长的测试密码")

    assert first.startswith("scrypt$")
    assert first != second
    assert verify_password("一个足够长的测试密码", first) is True
    assert verify_password("错误密码", first) is False
    assert verify_password("任意密码", "malformed") is False
    assert password_needs_rehash(first) is False


def test_sms_registration_password_lifecycle_lockout_and_token_revocation(
    tmp_path, monkeypatch
):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'password.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(settings, "otp_resend_seconds", 0)
    monkeypatch.setattr(settings, "password_max_attempts", 2)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_db():
        async with sessions() as session:
            yield session

    async def make_admin(phone: str):
        async with sessions() as session:
            user = (
                await session.execute(select(User).where(User.phone == phone))
            ).scalar_one()
            user.role = "admin"
            await session.commit()
            return token_for(user)

    async def password_state(phone: str):
        async with sessions() as session:
            user = (
                await session.execute(select(User).where(User.phone == phone))
            ).scalar_one()
            return (
                user.password_hash,
                user.auth_version,
                user.password_failed_attempts,
            )

    asyncio.run(setup())
    app.dependency_overrides[get_db] = override_db
    phone = "13800138005"
    try:
        with TestClient(app) as client:
            otp = client.post(
                "/api/v1/auth/otp/login/code", json={"phone": phone}
            ).json()
            sms_login = client.post(
                "/api/v1/auth/otp/login",
                json={"phone": phone, "code": otp["development_code"]},
            )
            assert sms_login.status_code == 200
            first_access = sms_login.json()["access_token"]
            first_headers = {"Authorization": f"Bearer {first_access}"}
            assert client.get("/api/v1/me", headers=first_headers).json()[
                "has_password"
            ] is False

            unset_login = client.post(
                "/api/v1/auth/password/login",
                json={"phone": phone, "password": "Initial-Passphrase"},
            )
            assert unset_login.status_code == 401
            assert unset_login.json() == {"detail": "Invalid phone number or password"}

            password_set = client.put(
                "/api/v1/auth/password",
                json={"new_password": "Initial-Passphrase"},
                headers=first_headers,
            )
            assert password_set.status_code == 200, password_set.text
            set_tokens = password_set.json()
            assert client.get("/api/v1/me", headers=first_headers).status_code == 401
            set_headers = {
                "Authorization": f"Bearer {set_tokens['access_token']}"
            }
            assert client.get("/api/v1/me", headers=set_headers).json()[
                "has_password"
            ] is True

            for expected_status in (401, 429):
                failed = client.post(
                    "/api/v1/auth/password/login",
                    json={"phone": phone, "password": "Wrong-Passphrase"},
                )
                assert failed.status_code == expected_status
            locked = client.post(
                "/api/v1/auth/password/login",
                json={"phone": phone, "password": "Initial-Passphrase"},
            )
            assert locked.status_code == 429

            login_otp = client.post(
                "/api/v1/auth/otp/login/code", json={"phone": phone}
            ).json()
            reset_otp = client.post(
                "/api/v1/auth/password/reset/otp", json={"phone": phone}
            ).json()
            wrong_purpose = client.post(
                "/api/v1/auth/password/reset",
                json={
                    "phone": phone,
                    "code": login_otp["development_code"],
                    "new_password": "Reset-Passphrase",
                },
            )
            assert wrong_purpose.status_code == 400

            reset = client.post(
                "/api/v1/auth/password/reset",
                json={
                    "phone": phone,
                    "code": reset_otp["development_code"],
                    "new_password": "Reset-Passphrase",
                },
            )
            assert reset.status_code == 200, reset.text
            assert client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": set_tokens["refresh_token"]},
            ).status_code == 401

            reset_login = client.post(
                "/api/v1/auth/password/login",
                json={"phone": phone, "password": "Reset-Passphrase"},
            )
            assert reset_login.status_code == 200
            reset_headers = {
                "Authorization": f"Bearer {reset_login.json()['access_token']}"
            }
            missing_current = client.put(
                "/api/v1/auth/password",
                json={"new_password": "Final-Passphrase"},
                headers=reset_headers,
            )
            assert missing_current.status_code == 400
            wrong_current = client.put(
                "/api/v1/auth/password",
                json={
                    "current_password": "Wrong-Passphrase",
                    "new_password": "Final-Passphrase",
                },
                headers=reset_headers,
            )
            assert wrong_current.status_code == 401
            assert asyncio.run(password_state("+8613800138005"))[2] == 1
            unchanged = client.put(
                "/api/v1/auth/password",
                json={
                    "current_password": "Reset-Passphrase",
                    "new_password": "Reset-Passphrase",
                },
                headers=reset_headers,
            )
            assert unchanged.status_code == 409
            changed = client.put(
                "/api/v1/auth/password",
                json={
                    "current_password": "Reset-Passphrase",
                    "new_password": "Final-Passphrase",
                },
                headers=reset_headers,
            )
            assert changed.status_code == 200, changed.text
            assert client.get("/api/v1/me", headers=reset_headers).status_code == 401
            assert client.post(
                "/api/v1/auth/password/login",
                json={"phone": phone, "password": "Final-Passphrase"},
            ).status_code == 200

            admin_token = asyncio.run(make_admin("+8613800138005"))
            admin_users = client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert admin_users.status_code == 200
            exposed = admin_users.json()[0]
            assert exposed["has_password"] is True
            assert "password_hash" not in exposed
            assert "auth_version" not in exposed

            stored_hash, auth_version, failed_attempts = asyncio.run(
                password_state("+8613800138005")
            )
            assert stored_hash.startswith("scrypt$")
            assert "Final-Passphrase" not in stored_hash
            assert auth_version == 3
            assert failed_attempts == 0
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_deactivated_user_cannot_authenticate_and_old_tokens_stay_revoked(
    tmp_path, monkeypatch
):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'deactivated.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(settings, "otp_resend_seconds", 0)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            admin = User(phone="+8613800138010", role="admin")
            target = User(
                phone="+8613800138011",
                password_hash=hash_password("Target-Passphrase"),
            )
            session.add_all([admin, target])
            await session.commit()
            await session.refresh(admin)
            await session.refresh(target)
            return target.id, token_for(admin), token_for(target, "refresh"), token_for(target)

    async def override_db():
        async with sessions() as session:
            yield session

    target_id, admin_token, target_refresh, target_access = asyncio.run(setup())
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    target_headers = {"Authorization": f"Bearer {target_access}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            issued_before_disable = client.post(
                "/api/v1/auth/otp/login/code",
                json={"phone": "13800138011"},
            )
            assert issued_before_disable.status_code == 200, issued_before_disable.text

            disabled = client.patch(
                f"/api/v1/admin/users/{target_id}/active",
                json={"is_active": False},
                headers=admin_headers,
            )
            assert disabled.status_code == 200, disabled.text
            assert disabled.json()["is_active"] is False

            assert client.get("/api/v1/me", headers=target_headers).status_code == 401
            assert client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": target_refresh},
            ).status_code == 401
            assert client.post(
                "/api/v1/auth/password/login",
                json={"phone": "13800138011", "password": "Target-Passphrase"},
            ).status_code == 401
            assert client.post(
                "/api/v1/auth/otp/login",
                json={
                    "phone": "13800138011",
                    "code": issued_before_disable.json()["development_code"],
                },
            ).status_code == 401
            assert client.post(
                "/api/v1/auth/otp/login/code",
                json={"phone": "13800138011"},
            ).status_code == 401
            assert client.post(
                "/api/v1/auth/password/reset/otp",
                json={"phone": "13800138011"},
            ).status_code == 401

            enabled = client.patch(
                f"/api/v1/admin/users/{target_id}/active",
                json={"is_active": True},
                headers=admin_headers,
            )
            assert enabled.status_code == 200, enabled.text
            assert enabled.json()["is_active"] is True

            # Reactivation must not revive tokens issued before deactivation.
            assert client.get("/api/v1/me", headers=target_headers).status_code == 401
            assert client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": target_refresh},
            ).status_code == 401

            otp = client.post(
                "/api/v1/auth/otp/login/code",
                json={"phone": "13800138011"},
            )
            assert otp.status_code == 200, otp.text
            login = client.post(
                "/api/v1/auth/password/login",
                json={"phone": "13800138011", "password": "Target-Passphrase"},
            )
            assert login.status_code == 200, login.text
            assert login.json()["new_user"] is False
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
