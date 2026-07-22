from __future__ import annotations


def test_pattern_reports_month_command_success_and_risk_evidence():
    from core.bazi_engine import build_bazi_chart

    pattern = build_bazi_chart(
        {
            "gender": "男",
            "birth_date": "1994-09-23",
            "birth_hour": 18,
            "birth_minute": 0,
        }
    )["pattern_analysis"]

    assert pattern["month_command_gan"]
    assert pattern["pattern_source"]
    assert pattern["formation_evidence"]
    assert "special_pattern_review" in pattern
    assert pattern["rule_ids"] == [
        "PATTERN-MONTH-QI",
        "PATTERN-SUCCESS-FAILURE",
        "PATTERN-SPECIAL-STRICT",
    ]
    assert pattern["public_text"] == pattern["plain_text"]


def test_accepted_special_pattern_is_the_single_public_pattern_conclusion():
    from core.pattern_engine import analyze_pattern
    from core.strength_engine import analyze_day_master_strength

    chart = {
        "day_master": "甲",
        "pillars": {
            key: {"gan": "甲", "zhi": "寅", "pillar": "甲寅"}
            for key in ("year", "month", "day", "hour")
        },
    }
    chart["day_master_strength"] = analyze_day_master_strength(chart)
    pattern = analyze_pattern(chart)

    assert chart["day_master_strength"]["strength"] == "从旺"
    assert pattern["special_pattern_review"]["accepted"] is True
    assert pattern["pattern"] == "从旺格"
    assert "从旺格" in pattern["plain_text"]
