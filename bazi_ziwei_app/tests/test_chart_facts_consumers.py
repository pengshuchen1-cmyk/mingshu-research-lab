from __future__ import annotations

from copy import deepcopy


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {
            "gender": "女",
            "birth_date": "1996-09-04",
            "birth_hour": 23,
            "birth_minute": 45,
        }
    )


def _poison_legacy_fields(chart: dict) -> dict:
    changed = deepcopy(chart)
    changed["day_master"] = "庚"
    changed["pillars"] = {key: {"pillar": "庚申", "gan": "庚", "zhi": "申"} for key in ("year", "month", "day", "hour")}
    changed["five_elements"] = {"金": 99.0}
    changed["ten_god_counts"] = {"偏财": 99}
    changed["ten_gods"] = {}
    changed["day_master_strength"] = {
        "strength": "从旺",
        "favorable_elements": ["金"],
        "unfavorable_elements": ["木"],
    }
    return changed


def test_report_fingerprint_uses_attached_chart_facts_not_legacy_fields():
    from core.chart_fingerprint import build_chart_fingerprint

    chart = _chart()

    assert build_chart_fingerprint(chart) == build_chart_fingerprint(_poison_legacy_fields(chart))


def test_special_reports_use_attached_chart_facts_not_legacy_fields():
    from report.bazi_report import generate_basic_bazi_report
    from report.career_report import generate_career_report
    from report.love_report import generate_love_report
    from report.wealth_report import generate_wealth_report

    chart = _chart()
    poisoned = _poison_legacy_fields(chart)

    assert generate_basic_bazi_report(chart) == generate_basic_bazi_report(poisoned)
    assert generate_career_report(chart) == generate_career_report(poisoned)
    assert generate_wealth_report(chart) == generate_wealth_report(poisoned)
    assert generate_love_report(chart, {"gender": "女"}) == generate_love_report(
        poisoned, {"gender": "女"}
    )
    assert generate_love_report(chart, {"gender": "男"}) == generate_love_report(
        chart, {"gender": "女"}
    )


def test_reports_reject_charts_without_attached_canonical_facts():
    import pytest
    from report.bazi_report import generate_basic_bazi_report

    with pytest.raises(ValueError, match="missing canonical ChartFacts"):
        generate_basic_bazi_report({"day_master": "甲"})
