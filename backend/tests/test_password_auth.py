import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import Base, OTPChallenge, User
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


def test_direct_password_registration_without_otp(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'register.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_db():
        async with sessions() as session:
            yield session

    async def registration_state():
        async with sessions() as session:
            user = (
                await session.execute(
                    select(User).where(User.phone == "+8613800138006")
                )
            ).scalar_one()
            otp_count = await session.scalar(
                select(func.count()).select_from(OTPChallenge)
            )
            return user.password_hash, otp_count

    asyncio.run(setup())
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            registered = client.post(
                "/api/v1/auth/password/register",
                json={
                    "phone": "13800138006",
                    "password": "Initial-Passphrase",
                },
            )
            assert registered.status_code == 201, registered.text
            tokens = registered.json()
            assert tokens["new_user"] is True
            assert tokens["token_type"] == "bearer"

            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            me = client.get("/api/v1/me", headers=headers)
            assert me.status_code == 200
            assert me.json()["phone"] == "+8613800138006"
            assert me.json()["has_password"] is True
            assert me.json()["points"] == 20

            password_login = client.post(
                "/api/v1/auth/password/login",
                json={
                    "phone": "+8613800138006",
                    "password": "Initial-Passphrase",
                },
            )
            assert password_login.status_code == 200
            assert password_login.json()["new_user"] is False

            duplicate = client.post(
                "/api/v1/auth/password/register",
                json={
                    "phone": "+8613800138006",
                    "password": "Different-Passphrase",
                },
            )
            assert duplicate.status_code == 409
            assert duplicate.json() == {"detail": "Account already registered"}

            short_password = client.post(
                "/api/v1/auth/password/register",
                json={"phone": "13800138007", "password": "short"},
            )
            assert short_password.status_code == 422

            invalid_phone = client.post(
                "/api/v1/auth/password/register",
                json={"phone": "not-a-phone", "password": "Valid-Passphrase"},
            )
            assert invalid_phone.status_code == 422

            stored_hash, otp_count = asyncio.run(registration_state())
            assert stored_hash.startswith("scrypt$")
            assert "Initial-Passphrase" not in stored_hash
            assert otp_count == 0
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


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
