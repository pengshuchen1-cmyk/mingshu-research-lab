from pathlib import Path

import pytest

from app.bazi.bazi_rulebook import load_rulebook
from app.chart_engine import generate_chart
from app.config import BACKEND_DIR


def _synthetic_profile() -> dict:
    return {
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


def test_backend_engine_matches_the_migrated_golden_chart():
    result = generate_chart(_synthetic_profile())

    assert result.pillars == ["丙子", "丙申", "甲辰", "己巳"]
    assert result.chart_fingerprint == (
        "d367f0f43e10505dfb7d07ac8b86dc04b3a1cc3fa39f1962a251334230c57ec5"
    )
    assert result.engine_version == "2.0.0"
    assert load_rulebook().version == result.engine_version


@pytest.mark.parametrize(
    ("updates", "expected_pillars", "expected_fingerprint"),
    [
        (
            {
                "calendar_type": "lunar",
                "birth_date": "1999-07-01",
                "time_label": "巳时",
            },
            ["己卯", "壬申", "乙未", "辛巳"],
            "faeea534bf46b1111a0bcf5b43e5ea0dbc58ec2366be1164f6e2229367e71e58",
        ),
        (
            {
                "gender": "女",
                "birth_hour": 23,
                "birth_minute": 30,
                "time_label": "子时（23:00–23:59）",
            },
            ["丙子", "丙申", "乙巳", "丙子"],
            "b1e618f5d9e0c415965ef2a89994d1e51ce250c1fd89e762c218d45d2de9322c",
        ),
        (
            {
                "gender": "女",
                "birth_hour": None,
                "birth_minute": None,
                "time_label": "时辰不详",
            },
            ["丙子", "丙申", "甲辰", "时柱不详"],
            "7f155e66ef1486a776151b11d1ca4128be8d241b2ea563c824954b83597430e9",
        ),
    ],
)
def test_backend_engine_preserves_high_risk_calendar_boundaries(
    updates: dict,
    expected_pillars: list[str],
    expected_fingerprint: str,
):
    profile = _synthetic_profile()
    profile.update(updates)

    result = generate_chart(profile)

    assert result.pillars == expected_pillars
    assert result.chart_fingerprint == expected_fingerprint


def test_backend_engine_rejects_an_unknown_calendar_type():
    profile = _synthetic_profile()
    profile["calendar_type"] = "unknown"

    with pytest.raises(ValueError, match="calendar_type must be"):
        generate_chart(profile)


def test_backend_engine_has_no_legacy_application_import_or_mount():
    forbidden = (
        "bazi_ziwei_app",
        "BAZI_ENGINE_ROOT",
        "from core.",
        "import core.",
        "from utils.",
        "sys.path",
    )
    owned_sources = list((BACKEND_DIR / "app" / "bazi").rglob("*.py"))
    owned_sources.append(BACKEND_DIR / "app" / "chart_engine.py")
    deployment_files = [
        BACKEND_DIR / "Dockerfile",
        BACKEND_DIR / "docker-compose.yml",
        BACKEND_DIR / "docker-compose.dev.yml",
        BACKEND_DIR / "docker-compose.remote-dev.yml",
    ]

    for path in owned_sources + deployment_files:
        source = Path(path).read_text(encoding="utf-8")
        assert not any(marker in source for marker in forbidden), path
