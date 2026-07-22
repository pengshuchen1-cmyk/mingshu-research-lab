from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads(
    (ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json").read_text(encoding="utf-8")
)["cases"]
APPROVED_FIELDS = [
    "时间模式", "四柱计算依据", "起运方向", "起运时间",
    "强弱证据", "格局", "财运", "姻缘",
]


def build_case(case: dict):
    from core.bazi_engine import build_bazi_chart
    from core.luck_engine import get_luck_cycles

    hour, minute = (int(item) for item in case["time"].split(":"))
    profile = {
        "gender": "女" if case["gender"] == "female" else "男",
        "calendar_type": case["calendar"],
        "birth_date": case["date"],
        "birth_hour": hour,
        "birth_minute": minute,
        "time_mode": "china_standard",
    }
    if case["calendar"] == "lunar":
        profile["lunar_birth_date"] = case["date"]
    if case.get("time_range_note"):
        profile["time_range_note"] = case["time_range_note"]
    chart = build_bazi_chart(profile)
    luck = get_luck_cycles(profile, chart)
    return chart, luck


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_user_five_charts_pass_full_rule_contract(case):
    chart, luck = build_case(case)

    assert "error" not in chart
    assert chart["profile"]["birth_date"] == case["expected_solar_date"]
    assert [chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")] == case["expected_pillars"]
    assert chart["time_mode"] == "china_standard"
    assert luck["available"] is True
    assert luck["direction_label"] in {"顺排", "逆排"}
    assert luck["start_text"]
    assert chart["day_master_strength"]["evidence"]
    assert chart["pattern_analysis"]["formation_evidence"]
    assert chart["wealth_analysis"]["earning_channels"]
    assert chart["relationship_analysis"]["stability_signals"]
    assert list(chart["public_summary"]) == APPROVED_FIELDS
    assert all(value for value in chart["public_summary"].values())


def test_u03_preserves_range_note_and_u05_enforces_zi23():
    u03, _ = build_case(next(case for case in CASES if case["id"] == "U03"))
    u05, _ = build_case(next(case for case in CASES if case["id"] == "U05"))

    assert u03["profile"]["time_range_note"] == "原始时间为13:00–15:00，按未时验收"
    assert u05["pillars"]["day"]["pillar"] == "乙巳"
    assert "CAL-DAY-ZI23" in u05["pillar_evidence"]["rule_ids"]
    assert "23:00" in u05["pillar_evidence"]["day_basis"]
    assert u05["pillars"]["day"]["pillar"] != "甲辰"


def test_acceptance_renderer_runs_as_importable_production_script():
    from scripts.render_user_five_bazi_acceptance import render

    output = render()

    assert "# 用户五命例·统一四柱规则验收" in output
    assert output.count("## U0") == 5
    assert "算法版本" not in output
    assert "调候依据" not in output
