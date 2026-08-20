import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base, User
from app.schemas import BirthProfileIn
from app.security import token_for


def _profile_payload(**updates):
    payload = {
        "name": "测试档案",
        "gender": "男",
        "calendar_type": "solar",
        "birth_date": "1996-09-04",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "",
        "is_leap_month": False,
        "time_label": "精确时间",
    }
    payload.update(updates)
    return payload


def _confirmed_payload(client: TestClient, headers: dict, **updates):
    payload = _profile_payload(**updates)
    preview = client.post("/api/v1/chart-profiles/preview", json=payload, headers=headers)
    assert preview.status_code == 200, preview.text
    payload["expected_input_fingerprint"] = preview.json()["input_fingerprint"]
    payload["expected_chart_fingerprint"] = preview.json()["chart_fingerprint"]
    return payload, preview.json()


def test_profile_preview_confirm_store_update_cooldown_and_regenerate(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'profiles.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            user = User(phone="+8613800138001")
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return token_for(user)

    async def override_db():
        async with sessions() as session:
            yield session

    headers = {"Authorization": f"Bearer {asyncio.run(setup())}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            create_payload, preview = _confirmed_payload(client, headers)
            assert len(preview["pillars"]) == 4
            created = client.post(
                "/api/v1/chart-profiles", json=create_payload, headers=headers
            )
            assert created.status_code == 201, created.text
            detail = created.json()
            profile_id = detail["profile"]["id"]
            assert detail["profile"]["name"] == "测试档案"
            assert detail["profile"]["solar_birth_date"] == "1996-09-04"
            assert detail["profile"]["can_edit"] is True
            assert detail["profile"]["last_edited_at"] is None
            assert detail["profile"]["next_edit_at"] is None
            assert "name" not in detail["chart"]["chart"]["profile"]
            assert "birth_place" not in detail["chart"]["chart"]["profile"]

            listed = client.get("/api/v1/chart-profiles", headers=headers)
            assert listed.status_code == 200
            assert [item["id"] for item in listed.json()] == [profile_id]
            stored = client.get(
                f"/api/v1/chart-profiles/{profile_id}/chart", headers=headers
            )
            assert stored.status_code == 200
            assert stored.json()["chart_fingerprint"] == preview["chart_fingerprint"]

            update_payload, _ = _confirmed_payload(
                client,
                headers,
                name="修改后的档案",
                birth_date="1996-09-05",
            )
            updated = client.put(
                f"/api/v1/chart-profiles/{profile_id}",
                json=update_payload,
                headers=headers,
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["profile"]["name"] == "修改后的档案"
            assert updated.json()["profile"]["can_edit"] is False
            assert updated.json()["profile"]["next_edit_at"] is not None

            blocked = client.put(
                f"/api/v1/chart-profiles/{profile_id}",
                json=update_payload,
                headers=headers,
            )
            assert blocked.status_code == 429
            assert "cooldown" in blocked.json()["detail"]

            regenerated = client.post(
                f"/api/v1/chart-profiles/{profile_id}/regenerate", headers=headers
            )
            assert regenerated.status_code == 200
            assert regenerated.json()["profile_id"] == profile_id
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_profile_confirmation_and_ownership_are_enforced(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'ownership.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            first = User(phone="+8613800138002")
            second = User(phone="+8613800138003")
            session.add_all([first, second])
            await session.commit()
            await session.refresh(first)
            await session.refresh(second)
            return token_for(first), token_for(second)

    async def override_db():
        async with sessions() as session:
            yield session

    first_token, second_token = asyncio.run(setup())
    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            invalid = _profile_payload(
                expected_input_fingerprint="0" * 64,
                expected_chart_fingerprint="0" * 64,
            )
            rejected = client.post(
                "/api/v1/chart-profiles", json=invalid, headers=first_headers
            )
            assert rejected.status_code == 409
            assert client.get(
                "/api/v1/chart-profiles", headers=first_headers
            ).json() == []

            create_payload, _ = _confirmed_payload(client, first_headers)
            created = client.post(
                "/api/v1/chart-profiles", json=create_payload, headers=first_headers
            )
            profile_id = created.json()["profile"]["id"]
            hidden = client.get(
                f"/api/v1/chart-profiles/{profile_id}", headers=second_headers
            )
            assert hidden.status_code == 404
            assert hidden.json() == {"detail": "Birth profile not found"}
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_lunar_source_date_schema_does_not_apply_gregorian_calendar_rules():
    value = BirthProfileIn(
        **_profile_payload(calendar_type="lunar", birth_date="1990-02-30")
    )
    assert value.birth_date == "1990-02-30"
