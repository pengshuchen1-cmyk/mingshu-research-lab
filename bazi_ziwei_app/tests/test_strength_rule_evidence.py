from __future__ import annotations


def test_strength_returns_auditable_rule_evidence():
    from core.bazi_engine import build_bazi_chart

    strength = build_bazi_chart(
        {
            "gender": "女",
            "birth_date": "1986-08-15",
            "birth_hour": 10,
            "birth_minute": 0,
        }
    )["day_master_strength"]

    assert {item["dimension"] for item in strength["evidence"]} >= {
        "得令", "得地", "得助", "泄耗克制",
    }
    for item in strength["evidence"]:
        assert item["rule_id"].startswith("STRENGTH-")
        assert item["polarity"] in {"support", "pressure", "mixed", "uncertain"}
        assert isinstance(item["weight"], float)
        assert item["fact"]
        assert item["explanation"]
    assert strength["public_evidence"]


def test_unknown_hour_marks_strength_uncertainty():
    from core.bazi_engine import build_bazi_chart

    strength = build_bazi_chart(
        {
            "gender": "男",
            "birth_date": "1994-09-23",
            "birth_hour": None,
            "birth_minute": None,
        }
    )["day_master_strength"]

    assert any(item["polarity"] == "uncertain" for item in strength["evidence"])
    assert strength["uncertainty"]
