"""Contract tests for authenticated personal fortune analysis."""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.chart_engine import generate_chart
from app.database import get_db
from app.fortune.evidence_display import build_display_trigger_factors
from app.main import app
from app.models import Base, User
from app.personal_fortune import FortuneProfileInput, build_personal_fortune
from app.schemas import PersonalFortuneOut
from app.security import token_for


def _profile_payload():
    return {
        "name": "个人运势测试",
        "gender": "男",
        "calendar_type": "solar",
        "birth_date": "1996-09-04",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "测试地点",
        "is_leap_month": False,
        "time_label": "精确时间",
    }


def _create_profile(client: TestClient, headers: dict[str, str]) -> str:
    payload = _profile_payload()
    preview = client.post("/api/v1/chart-profiles/preview", json=payload, headers=headers)
    assert preview.status_code == 200, preview.text
    payload.update(
        expected_input_fingerprint=preview.json()["input_fingerprint"],
        expected_chart_fingerprint=preview.json()["chart_fingerprint"],
    )
    created = client.post("/api/v1/chart-profiles", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    return created.json()["profile"]["id"]


def test_personal_fortune_requires_owner_and_returns_full_year(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'fortune.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            owner = User(phone="+8613800138101")
            stranger = User(phone="+8613800138102")
            session.add_all([owner, stranger])
            await session.commit()
            await session.refresh(owner)
            await session.refresh(stranger)
            return token_for(owner), token_for(stranger)

    async def override_db():
        async with sessions() as session:
            yield session

    owner_token, stranger_token = asyncio.run(setup())
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            profile_id = _create_profile(client, owner_headers)

            anonymous = client.get(f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=2026")
            assert anonymous.status_code == 401

            hidden = client.get(
                f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=2026",
                headers=stranger_headers,
            )
            assert hidden.status_code == 404

            response = client.get(
                f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=2026",
                headers=owner_headers,
            )
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["kind"] == "personal_fortune"
            assert data["is_personal"] is True
            assert data["profile_id"] == profile_id
            assert data["target_year"] == 2026
            assert data["yearly"]["pillar"] == "丙午"
            assert len(data["monthly"]) == 12
            assert [item["month"] for item in data["monthly"]] == list(range(1, 13))
            assert all(item["top_events"] for item in data["monthly"])
            assert all(
                isinstance(event["display_trigger_factors"], list)
                for month in data["monthly"]
                for event in month["top_events"]
            )
            assert data["luck_context"]["available"] is True

            serialized = str(data)
            assert "+8613800138101" not in serialized
            assert "个人运势测试" not in serialized
            assert "测试地点" not in serialized
            assert "birth_date" not in serialized
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_personal_fortune_validates_year_and_is_deterministic(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'stable.db'}")
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            user = User(phone="+8613800138103")
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
            profile_id = _create_profile(client, headers)
            url = f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=2027"
            first = client.get(url, headers=headers)
            second = client.get(url, headers=headers)
            assert first.status_code == second.status_code == 200
            first_data = first.json()
            second_data = second.json()
            first_data.pop("generated_at")
            second_data.pop("generated_at")
            assert first_data == second_data

            too_old = client.get(
                f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=1899",
                headers=headers,
            )
            too_new = client.get(
                f"/api/v1/chart-profiles/{profile_id}/fortune?target_year=2101",
                headers=headers,
            )
            assert too_old.status_code == 422
            assert too_new.status_code == 422
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_personal_fortune_module_has_no_legacy_app_dependency():
    from app import personal_fortune

    source = personal_fortune.__loader__.get_source(personal_fortune.__name__)
    assert "bazi_ziwei_app" not in source
    assert "from core" not in source

    fortune_dir = Path(personal_fortune.__file__).parent / "fortune"
    for path in fortune_dir.glob("*.py"):
        migrated_source = path.read_text(encoding="utf-8")
        assert "bazi_ziwei_app" not in migrated_source, path
        assert "from core" not in migrated_source, path
        assert "import core" not in migrated_source, path
        assert "from report" not in migrated_source, path


def test_event_evidence_is_translated_to_legacy_display_trigger_factors():
    event = {
        "evidence": [
            {"type": "is_wealth_month", "detail": "内部条件一"},
            {"type": "element", "value": ["土"]},
            {"type": "element_in", "value": ["火"]},
            {"type": "group_count_at_least", "value": [{"group": "peer", "min": 2}]},
        ]
    }

    assert build_display_trigger_factors(event) == [
        "相关命盘主题被流月引动",
        "流月五行关系被引动",
        "原局结构提供相关线索",
    ]


LEGACY_CONTRACT_CASES = (
    (
        "A",
        "男",
        "solar",
        "1996-09-04",
        10,
        0,
        2024,
        "5e70ab0e3631670ddf271b44153fa92e070d987ce96c251b6f39c6ff8bb7be38",
    ),
    (
        "A",
        "男",
        "solar",
        "1996-09-04",
        10,
        0,
        2026,
        "070a2e7b1b048970c4190e206fc948fecb5bd9ad28b496e32ba002e5b190ea72",
    ),
    (
        "A",
        "男",
        "solar",
        "1996-09-04",
        10,
        0,
        2030,
        "24980ab8508a2e9bd4e6ff222cfca1c25a5093eebdb7d5e93c5a1170dce13693",
    ),
    (
        "B",
        "女",
        "solar",
        "1988-02-17",
        23,
        30,
        2024,
        "cd8e55a755ead92da6c954e4f5d259bfbf080c4629a2310cc8b568207ab42279",
    ),
    (
        "B",
        "女",
        "solar",
        "1988-02-17",
        23,
        30,
        2026,
        "c91dd1dca5d06f4f45971cf1c263eb39578956f0bb2bbfd2dedb3ab95246959b",
    ),
    (
        "B",
        "女",
        "solar",
        "1988-02-17",
        23,
        30,
        2030,
        "6ce4b9075d7b4d5bd882438acd0bb9972fcc7bd61c0ccf0b17850e69c9e30651",
    ),
    (
        "C",
        "男",
        "solar",
        "1975-12-22",
        None,
        None,
        2024,
        "e8dc84891a55f97e9fe7d866c6344fa4e6cf273c9bbd310f78f7c29f867cd774",
    ),
    (
        "C",
        "男",
        "solar",
        "1975-12-22",
        None,
        None,
        2026,
        "caa33b1dae32e1583ceda6dbe23349c624d6ead57ae85eb6eef10f88e3418a20",
    ),
    (
        "C",
        "男",
        "solar",
        "1975-12-22",
        None,
        None,
        2030,
        "f9379ddfb352f0827d57f5be55bc824aa0c84cee634dd9e1a8dd1199468c6ec6",
    ),
    (
        "D",
        "女",
        "lunar",
        "1990-02-15",
        6,
        20,
        2024,
        "dac3d96ec1889ad3d1d4f83cc6bd248dbe4263d89dcab0f1d4f45dd5a3ec652f",
    ),
    (
        "D",
        "女",
        "lunar",
        "1990-02-15",
        6,
        20,
        2026,
        "530dc25c04810277fac892759ca2e10c7784cf7cd14d5e51e6ea4b7836c7e773",
    ),
    (
        "D",
        "女",
        "lunar",
        "1990-02-15",
        6,
        20,
        2030,
        "5503ba7fab44b0a691fa8d636f7ffda5ff9773fb280b40f10820eab08ace1e56",
    ),
)


@pytest.mark.parametrize(
    ("name", "gender", "calendar_type", "birth_date", "hour", "minute", "year", "expected_digest"),
    LEGACY_CONTRACT_CASES,
)
def test_personal_fortune_matches_migration_baseline(
    name,
    gender,
    calendar_type,
    birth_date,
    hour,
    minute,
    year,
    expected_digest,
):
    """Protect the complete legacy yearly, monthly, event and luck contract."""
    source = {
        "name": name,
        "gender": gender,
        "calendar_type": calendar_type,
        "birth_date": birth_date,
        "birth_hour": hour,
        "birth_minute": minute,
        "birth_place": "",
        "is_leap_month": False,
        "time_label": "时辰不详" if hour is None else "精确时间",
    }
    generated = generate_chart(source)
    result = build_personal_fortune(
        "contract-profile",
        generated.chart_fingerprint,
        FortuneProfileInput(
            calendar_type,
            birth_date,
            hour,
            minute,
            gender,
            False,
        ),
        generated.chart,
        year,
    )
    PersonalFortuneOut.model_validate(result)
    yearly = {
        key: value
        for key, value in result["yearly"].items()
        if key not in {"relationship_good_months", "relationship_bad_months"}
    }
    contract = {
        "yearly": yearly,
        "monthly": result["monthly"],
        "luck_context": result["luck_context"],
    }

    def normalize(value, key=None):
        if isinstance(value, dict):
            return {
                item_key: normalize(item, item_key)
                for item_key, item in value.items()
                if item_key != "display_trigger_factors"
            }
        if isinstance(value, list):
            items = [normalize(item) for item in value]
            # Legacy source registries are sets semantically. Their order can
            # vary with PYTHONHASHSEED without changing any event conclusion.
            return sorted(items) if key in {"source_ids", "source_titles"} else items
        return value

    encoded = json.dumps(
        normalize(contract),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == expected_digest
