from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(
    ("year", "gender", "expected"),
    [
        (1994, "male", "forward"),
        (1994, "female", "reverse"),
        (1995, "male", "reverse"),
        (1995, "female", "forward"),
    ],
)
def test_dayun_direction_uses_gender_and_year_stem_yinyang(year, gender, expected):
    from core.bazi_calendar_adapter import BirthInput
    from core.dayun_rule_engine import calculate_dayun

    basis = calculate_dayun(BirthInput("solar", year, 9, 23, 10, 0, gender))

    assert basis.direction == expected
    assert "DAYUN-DIRECTION" in basis.rule_ids


def test_dayun_uses_next_jie_for_forward_and_previous_for_reverse():
    from core.bazi_calendar_adapter import BirthInput
    from core.dayun_rule_engine import calculate_dayun

    forward = calculate_dayun(BirthInput("solar", 1994, 9, 23, 10, 0, "male"))
    reverse = calculate_dayun(BirthInput("solar", 1994, 9, 23, 10, 0, "female"))

    assert forward.boundary_name == "寒露"
    assert reverse.boundary_name == "白露"
    assert forward.interval_seconds > 0
    assert reverse.interval_seconds > 0


def test_three_days_convert_to_one_start_age_year():
    from core.dayun_rule_engine import interval_to_start_age

    assert interval_to_start_age(3 * 24 * 60 * 60) == (1, 0, 0)
    assert interval_to_start_age(24 * 60 * 60) == (0, 4, 0)


def test_get_luck_cycles_is_an_adapter_without_eight_char_dependency():
    source = (Path(__file__).resolve().parents[1] / "core" / "luck_engine.py").read_text(
        encoding="utf-8"
    )

    assert "getEightChar" not in source
    assert "getYun" not in source


def test_luck_cycles_expose_direction_start_and_ten_year_periods():
    from core.bazi_engine import build_bazi_chart
    from core.luck_engine import get_luck_cycles

    profile = {
        "gender": "男",
        "calendar_type": "solar",
        "birth_date": "1994-09-23",
        "birth_hour": 18,
        "birth_minute": 0,
    }
    chart = build_bazi_chart(profile)
    luck = get_luck_cycles(profile, chart)

    assert luck["available"] is True
    assert luck["direction"] == "forward"
    assert luck["direction_label"] == "顺排"
    assert luck["start_text"]
    assert len(luck["dayun_list"]) == 10
    assert all(item["end_age"] - item["start_age"] == 9 for item in luck["dayun_list"])


def test_luck_cycles_yearly_prebuild_is_default_on_and_can_be_disabled():
    from core.bazi_engine import build_bazi_chart
    from core.luck_engine import get_luck_cycles

    profile = {
        "gender": "男",
        "calendar_type": "solar",
        "birth_date": "1994-09-23",
        "birth_hour": 18,
        "birth_minute": 0,
    }
    chart = build_bazi_chart(profile)
    sentinel = [{"year": 2026, "pillar": "丙午"}]

    with patch("core.luck_engine._build_yearly_list", return_value=sentinel) as build:
        default = get_luck_cycles(profile, chart)
        lazy = get_luck_cycles(profile, chart, include_yearly_list=False)

    assert default["yearly_list"] == sentinel
    assert lazy["yearly_list"] == []
    build.assert_called_once_with(chart, 10)


def test_period_calendar_year_starts_from_actual_start_datetime_for_u05():
    from core.bazi_calendar_adapter import BirthInput
    from core.dayun_rule_engine import build_dayun_periods, calculate_dayun
    from core.four_pillars_engine import calculate_four_pillars

    birth = BirthInput("solar", 1996, 9, 4, 23, 45, "female")
    pillars = calculate_four_pillars(birth)
    basis = calculate_dayun(birth, pillars)
    periods = build_dayun_periods(pillars.month.text, basis, 1996)

    assert basis.start_datetime.date().isoformat() == "2006-02-24"
    assert periods[0]["start_year"] == 2006
    assert periods[0]["start_date"] == "2006-02-24"
    assert periods[1]["start_date"] == "2016-02-24"


def test_unknown_time_marks_dayun_start_as_estimate():
    from core.bazi_calendar_adapter import BirthInput
    from core.dayun_rule_engine import calculate_dayun

    basis = calculate_dayun(BirthInput("solar", 1994, 9, 23, None, None, "male"))

    assert basis.time_is_estimated is True
    assert "时辰不详" in basis.start_text


def test_current_dayun_matching_respects_exact_change_date():
    from datetime import date
    from ui.luck_page import _current_luck_item

    periods = [
        {"pillar": "甲子", "start_date": "2006-02-24", "end_date": "2016-02-24"},
        {"pillar": "乙丑", "start_date": "2016-02-24", "end_date": "2026-02-24"},
    ]

    assert _current_luck_item(periods, date(2016, 2, 23))["pillar"] == "甲子"
    assert _current_luck_item(periods, date(2016, 2, 24))["pillar"] == "乙丑"


def test_yearly_note_discloses_midyear_dayun_boundary():
    from core.yearly_engine import _current_luck_note

    note = _current_luck_note(
        {"available": True, "dayun_list": [
            {
                "pillar": "乙丑", "start_year": 2016, "end_year": 2025,
                "start_date": "2016-02-24", "end_date": "2026-02-24",
            }
        ]},
        2016,
    )

    assert "2月24日换入此运" in note
    assert "年初仍属上一运" in note
