from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


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


def test_chart_facts_are_frozen_and_canonical():
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(_chart())

    assert facts.pillars == ("丙子", "丙申", "乙巳", "丙子")
    assert facts.gender == "female"
    assert facts.internal_rule_version == "2.0.0"
    with pytest.raises(FrozenInstanceError):
        facts.gender = "male"


def test_chart_facts_serialization_returns_new_plain_values():
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(_chart())
    first = facts.to_dict()
    second = facts.to_dict()
    first["pillars"][0] = "篡改"

    assert second["pillars"][0] == "丙子"
    assert facts.pillars[0] == "丙子"


def test_public_summary_has_exact_approved_fields():
    from core.chart_facts import build_chart_facts

    summary = build_chart_facts(_chart()).public_summary()

    assert list(summary) == [
        "时间模式",
        "四柱计算依据",
        "起运方向",
        "起运时间",
        "强弱证据",
        "格局",
        "财运",
        "姻缘",
    ]
    rendered = str(summary)
    assert "算法版本" not in rendered
    assert "调候依据" not in rendered


def test_chart_fingerprint_is_stable_and_ignores_current_context():
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(_chart())
    changed = facts.with_current_context({"year": 2030, "pillar": "庚戌"})

    assert facts.fingerprint() == changed.fingerprint()


def test_build_bazi_chart_attaches_single_facts_projection():
    chart = _chart()

    assert chart["facts"]["pillars"] == ["丙子", "丙申", "乙巳", "丙子"]
    assert list(chart["public_summary"]) == [
        "时间模式", "四柱计算依据", "起运方向", "起运时间",
        "强弱证据", "格局", "财运", "姻缘",
    ]
    assert chart["chart_fingerprint_v2"]
    assert chart["wealth_analysis"]["earning_channels"]
    assert chart["relationship_analysis"]["formation_signals"]
    assert chart["public_summary"]["财运"] != "待分析"
    assert chart["public_summary"]["姻缘"] != "待分析"
    assert chart["public_summary"]["起运方向"] in {"顺排", "逆排"}
    assert chart["public_summary"]["起运时间"] != "待计算"
    assert chart["facts"]["current_context"]["year"]
    assert chart["facts"]["current_context"]["year_pillar"]
