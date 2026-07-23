from __future__ import annotations

from datetime import date
from pathlib import Path


def test_lunar_birth_is_normalized_to_solar_with_source_evidence():
    from core.bazi_calendar_adapter import BirthInput, normalize_birth_input

    evidence = normalize_birth_input(
        BirthInput("lunar", 1986, 7, 10, 10, 0, "female")
    )

    assert evidence.converted_solar_date == date(1986, 8, 15)
    assert evidence.source_calendar == "lunar"
    assert evidence.time_mode_label == "中国标准时间（北京时间）"
    assert evidence.civil_datetime.hour == 10


def test_leap_lunar_month_uses_negative_library_month():
    from core.bazi_calendar_adapter import BirthInput, normalize_birth_input

    evidence = normalize_birth_input(
        BirthInput("lunar", 2023, 2, 15, 10, 0, "male", is_leap_month=True)
    )

    assert evidence.converted_solar_date == date(2023, 4, 5)
    assert evidence.is_leap_month is True


def test_unknown_hour_is_preserved_instead_of_guessed():
    from core.bazi_calendar_adapter import BirthInput, normalize_birth_input

    evidence = normalize_birth_input(
        BirthInput("solar", 1994, 9, 23, None, None, "male")
    )

    assert evidence.civil_datetime is None
    assert evidence.converted_solar_date == date(1994, 9, 23)


def test_calendar_adapter_returns_exact_twelve_month_changing_jie():
    from core.bazi_calendar_adapter import jie_boundaries

    boundaries = jie_boundaries(1996)

    assert len(boundaries) == 12
    assert [item.name for item in boundaries] == [
        "小寒", "立春", "惊蛰", "清明", "立夏", "芒种",
        "小暑", "立秋", "白露", "寒露", "立冬", "大雪",
    ]
    assert all(left.at < right.at for left, right in zip(boundaries, boundaries[1:]))


def test_day_pillar_seed_is_date_only():
    from core.bazi_calendar_adapter import day_pillar_seed

    assert day_pillar_seed(date(1996, 9, 4)) == ("甲", "辰")
    assert day_pillar_seed(date(1996, 9, 5)) == ("乙", "巳")


def test_profile_payload_preserves_leap_month_and_unknown_time():
    from ui.profile_form import _build_profile_payload

    profile = _build_profile_payload(
        name="Test",
        gender="女",
        calendar_label="农历",
        birth_date=date(2023, 2, 15),
        birth_hour=None,
        birth_minute=None,
        birth_place="",
        use_solar_time=False,
        birth_longitude=None,
        is_leap_month=True,
        time_known=False,
    )

    assert profile["is_leap_month"] is True
    assert profile["birth_hour"] is None
    assert profile["birth_minute"] is None
    assert profile["time_mode"] == "china_standard"


def test_profile_form_uses_single_standard_time_mode():
    source = (Path(__file__).resolve().parents[1] / "ui" / "profile_form.py").read_text(
        encoding="utf-8"
    )

    assert "使用真太阳时校正" not in source
    assert '"出生时间精度"' in source
    assert '["精确时间", "传统时辰", "时辰不详"]' in source
    assert "是否闰月" in source
