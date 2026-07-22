from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest


def _birth(year, month, day, hour, minute, gender="female"):
    from core.bazi_calendar_adapter import BirthInput

    return BirthInput("solar", year, month, day, hour, minute, gender)


def test_lichun_changes_year_and_month_at_exact_second():
    from core.four_pillars_engine import calculate_four_pillars

    before = calculate_four_pillars(_birth(1996, 2, 4, 21, 7))
    at_boundary = calculate_four_pillars(
        _birth(1996, 2, 4, 21, 7),
        civil_datetime_override=datetime(1996, 2, 4, 21, 7, 54),
    )

    assert before.year.text == "乙亥"
    assert before.month.text == "己丑"
    assert at_boundary.year.text == "丙子"
    assert at_boundary.month.text == "庚寅"


def test_month_changes_at_exact_jie_timestamp():
    from core.four_pillars_engine import calculate_four_pillars

    before = calculate_four_pillars(
        _birth(1996, 9, 7, 16, 42),
        civil_datetime_override=datetime(1996, 9, 7, 16, 42, 24),
    )
    at_boundary = calculate_four_pillars(
        _birth(1996, 9, 7, 16, 42),
        civil_datetime_override=datetime(1996, 9, 7, 16, 42, 25),
    )

    assert before.month.text == "丙申"
    assert at_boundary.month.text == "丁酉"


def test_1996_09_04_2345_uses_next_bazi_day():
    from core.four_pillars_engine import calculate_four_pillars

    chart = calculate_four_pillars(_birth(1996, 9, 4, 23, 45))

    assert chart.day.text == "乙巳"
    assert chart.hour is not None
    assert chart.hour.text == "丙子"
    assert "23:00" in chart.evidence.day_basis
    assert "CAL-DAY-ZI23" in chart.evidence.rule_ids


def test_2259_keeps_civil_day_and_uses_hai_hour():
    from core.four_pillars_engine import calculate_four_pillars

    chart = calculate_four_pillars(_birth(1996, 9, 4, 22, 59))

    assert chart.day.text == "甲辰"
    assert chart.hour is not None
    assert chart.hour.text == "乙亥"


@pytest.mark.parametrize(
    ("date_value", "expected_hour"),
    [
        ((1996, 9, 4), "甲子"),
        ((1996, 9, 5), "丙子"),
        ((1996, 9, 6), "戊子"),
        ((1996, 9, 7), "庚子"),
        ((1996, 9, 8), "壬子"),
    ],
)
def test_five_rat_formula_for_each_day_stem_group(date_value, expected_hour):
    from core.four_pillars_engine import calculate_four_pillars

    chart = calculate_four_pillars(_birth(*date_value, 0, 30))

    assert chart.hour is not None
    assert chart.hour.text == expected_hour


def test_unknown_hour_never_guesses_hour_pillar():
    from core.bazi_calendar_adapter import BirthInput
    from core.four_pillars_engine import calculate_four_pillars

    chart = calculate_four_pillars(
        BirthInput("solar", 1994, 9, 23, None, None, "male")
    )

    assert chart.hour is None
    assert "时辰不详" in chart.evidence.hour_basis


@pytest.mark.parametrize(
    ("birth", "expected"),
    [
        (("lunar", 1986, 7, 10, 10, 0, "female"), "丙寅/丙申/辛卯/癸巳"),
        (("lunar", 1977, 9, 29, 19, 30, "male"), "丁巳/辛亥/辛未/戊戌"),
        (("lunar", 1974, 6, 17, 14, 0, "male"), "甲寅/辛未/丁丑/丁未"),
        (("solar", 1994, 9, 23, 18, 0, "male"), "甲戌/癸酉/壬子/己酉"),
        (("solar", 1996, 9, 4, 23, 45, "female"), "丙子/丙申/乙巳/丙子"),
    ],
)
def test_user_five_case_pillar_baselines(birth, expected):
    from core.bazi_calendar_adapter import BirthInput
    from core.four_pillars_engine import calculate_four_pillars

    chart = calculate_four_pillars(BirthInput(*birth))
    actual = "/".join(
        pillar.text for pillar in (chart.year, chart.month, chart.day, chart.hour)
        if pillar is not None
    )

    assert actual == expected


def test_build_bazi_chart_uses_explicit_engine_for_late_zi():
    from core.bazi_engine import build_bazi_chart

    chart = build_bazi_chart(
        {
            "gender": "女",
            "calendar_type": "solar",
            "birth_date": "1996-09-04",
            "birth_hour": 23,
            "birth_minute": 45,
        }
    )

    assert chart["pillars"]["day"]["pillar"] == "乙巳"
    assert chart["pillars"]["hour"]["pillar"] == "丙子"
    assert chart["time_mode"] == "china_standard"
    assert chart["pillar_evidence"]["rule_ids"] == [
        "CAL-YEAR-LICHUN",
        "CAL-MONTH-JIE",
        "CAL-DAY-ZI23",
        "PILLAR-MONTH-FIVETIGER",
        "PILLAR-HOUR-FIVERAT",
    ]


def test_bazi_engine_does_not_import_legacy_eight_char_path():
    source = (Path(__file__).resolve().parents[1] / "core" / "bazi_engine.py").read_text(
        encoding="utf-8"
    )

    assert "get_lunar_eight_char" not in source
    assert "getEightChar" not in source
