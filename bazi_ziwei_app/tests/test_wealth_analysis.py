from __future__ import annotations


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {
            "gender": "男",
            "birth_date": "1994-09-23",
            "birth_hour": 18,
            "birth_minute": 0,
        }
    )


def test_wealth_analysis_separates_earning_and_retention():
    from core.wealth_analysis import analyze_wealth

    result = analyze_wealth(_chart())

    assert result.earning_channels
    assert result.retention_factors
    assert result.risk_factors
    assert "赚钱路径" in result.public_text
    assert "留财条件" in result.public_text
    assert result.rule_ids == (
        "WEALTH-STAR-VISIBILITY",
        "WEALTH-CAPACITY",
        "WEALTH-REVENUE-RETENTION",
        "WEALTH-RISK-ADVICE",
    )


def test_wealth_analysis_never_guarantees_leveraged_result():
    from core.wealth_analysis import analyze_wealth

    text = analyze_wealth(_chart()).public_text

    for phrase in ("一定发财", "保证成功", "抵押房子一定能成"):
        assert phrase not in text
    assert "杠杆" in text or "现金流" in text
