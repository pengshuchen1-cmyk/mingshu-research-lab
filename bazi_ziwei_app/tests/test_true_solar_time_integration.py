"""统一中国标准时间模式的集成测试。"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _profile(**overrides):
    value = {
        "name": "Test",
        "gender": "男",
        "birth_date": "1990-06-15",
        "birth_hour": 8,
        "birth_minute": 0,
        "birth_place": "Beijing",
    }
    value.update(overrides)
    return value


def test_default_uses_china_standard_time():
    from core.bazi_engine import build_bazi_chart

    chart = build_bazi_chart(_profile())

    assert chart["time_mode"] == "china_standard"
    assert chart["time_mode_label"] == "中国标准时间（北京时间）"
    assert chart["true_solar_time_applied"] is False


def test_legacy_true_solar_request_cannot_change_new_chart():
    from core.bazi_engine import build_bazi_chart

    baseline = build_bazi_chart(_profile())
    requested = build_bazi_chart(
        _profile(use_true_solar_time=True, birth_longitude="invalid")
    )

    assert requested["time_mode"] == "china_standard"
    assert requested["birth_longitude"] is None
    assert requested["pillars"] == baseline["pillars"]


def test_known_cases_follow_explicit_cst_and_zi23_policy():
    from core.bazi_engine import build_bazi_chart

    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "known_bazi_cases.json").read_text(encoding="utf-8")
    )["cases"]
    for case in cases:
        date_text, time_text = case["birth_datetime"].split(" ")
        hour, minute = (int(item) for item in time_text.split(":"))
        chart = build_bazi_chart(
            _profile(
                gender=case["gender"],
                birth_date=date_text,
                birth_hour=hour,
                birth_minute=minute,
            )
        )
        actual = {key: item["pillar"] for key, item in chart["pillars"].items()}
        assert actual == case["expected_pillars"], case["case_id"]


def test_chart_keeps_compatibility_time_fields_without_adjustment():
    from core.bazi_engine import build_bazi_chart

    chart = build_bazi_chart(_profile())

    assert chart["adjusted_birth_datetime"] == chart["original_birth_datetime"]
    assert chart["calendar_evidence"]["time_mode"] == "china_standard"
    assert chart["true_solar_time_warning"] == ""


def test_profile_form_does_not_offer_true_solar_controls():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")

    assert "使用真太阳时校正" not in source
    assert "出生地经度（东经）" not in source
    assert "中国标准时间（北京时间）" in source
