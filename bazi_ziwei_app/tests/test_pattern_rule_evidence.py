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
