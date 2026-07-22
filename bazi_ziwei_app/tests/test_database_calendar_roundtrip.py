from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "profile",
    [
        {
            "name": "U01",
            "gender": "女",
            "calendar_type": "lunar",
            "lunar_birth_date": "1986-07-10",
            "birth_date": "1986-07-10",
            "birth_hour": 10,
            "birth_minute": 0,
            "is_leap_month": False,
            "time_mode": "china_standard",
        },
        {
            "name": "闰月样例",
            "gender": "男",
            "calendar_type": "lunar",
            "lunar_birth_date": "2023-02-01",
            "birth_date": "2023-02-01",
            "birth_hour": 8,
            "birth_minute": 0,
            "is_leap_month": True,
            "time_mode": "china_standard",
        },
        {
            "name": "公历样例",
            "gender": "男",
            "calendar_type": "solar",
            "birth_date": "1994-09-23",
            "birth_hour": 18,
            "birth_minute": 0,
            "is_leap_month": False,
            "time_mode": "china_standard",
        },
    ],
)
def test_profile_calendar_semantics_survive_database_roundtrip(monkeypatch, tmp_path, profile):
    from core.bazi_engine import build_bazi_chart
    from utils import database

    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "profiles.db"))
    original = build_bazi_chart(profile)
    profile_id = database.save_profile(profile, original, {})
    loaded = database.get_profile(profile_id)
    rebuilt = build_bazi_chart(loaded)

    assert loaded["calendar_type"] == profile["calendar_type"]
    assert bool(loaded["is_leap_month"]) is bool(profile["is_leap_month"])
    assert loaded["time_mode"] == "china_standard"
    if profile["calendar_type"] == "lunar":
        assert loaded["lunar_birth_date"] == profile["lunar_birth_date"]
    keys = ("year", "month", "day", "hour")
    assert [rebuilt["pillars"][key]["pillar"] for key in keys] == [
        original["pillars"][key]["pillar"] for key in keys
    ]
