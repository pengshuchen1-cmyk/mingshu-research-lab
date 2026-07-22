from __future__ import annotations


def _chart():
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(
        {
            "gender": "女",
            "birth_date": "1986-08-15",
            "birth_hour": 10,
            "birth_minute": 0,
        }
    )


def test_relationship_analysis_separates_attraction_formation_stability():
    from core.relationship_analysis import analyze_relationship

    result = analyze_relationship(_chart())

    assert result.attraction_signals
    assert result.formation_signals
    assert result.stability_signals
    assert "吸引" in result.public_text
    assert "关系建立" in result.public_text
    assert "稳定" in result.public_text


def test_relationship_analysis_does_not_claim_current_marital_status():
    from core.relationship_analysis import analyze_relationship

    result = analyze_relationship(_chart())

    assert result.current_status == "unknown"
    assert any("不能确认当前是否已婚" in item for item in result.uncertainty)
    assert "现在已经结婚" not in result.public_text
