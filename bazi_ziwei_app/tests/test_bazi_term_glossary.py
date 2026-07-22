"""命理术语词典与命盘个性化解释契约。"""

from __future__ import annotations

import json
from copy import deepcopy


TEN_GODS = {
    "正官",
    "七杀",
    "正印",
    "偏印",
    "正财",
    "偏财",
    "食神",
    "伤官",
    "比肩",
    "劫财",
}


def _chart() -> dict:
    return {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "戊", "zhi": "辰"},
            "month": {"gan": "己", "zhi": "丑"},
            "day": {"gan": "甲", "zhi": "子"},
            "hour": {"gan": "丙", "zhi": "寅"},
        },
        "ten_gods": {
            "year": {"gan": "偏财", "hidden_stems": []},
            "month": {"gan": "正财", "hidden_stems": []},
            "day": {"gan": "比肩", "hidden_stems": []},
            "hour": {"gan": "食神", "hidden_stems": []},
        },
        "hidden_stems": {
            "year": [{"gan": "戊", "element": "土", "ten_god": "偏财"}],
            "month": [{"gan": "己", "element": "土", "ten_god": "正财"}],
            "day": [{"gan": "癸", "element": "水", "ten_god": "正印"}],
            "hour": [{"gan": "甲", "element": "木", "ten_god": "比肩"}],
        },
        "ten_god_counts": {"偏财": 2, "正财": 2, "比肩": 2, "食神": 1, "正印": 1},
        "five_elements": {"木": 2, "火": 1, "土": 4, "金": 0, "水": 1},
        "day_master_strength": {
            "strength": "身弱",
            "favorable_elements": ["水", "木"],
            "unfavorable_elements": ["火", "土"],
        },
        "pattern_analysis": {"pattern": "正财格"},
        "seasonal_adjustment": {"primary_useful_stems": ["丙"], "supporting_stems": ["癸"]},
    }


def test_first_batch_has_22_terms_with_required_copy():
    from core.bazi_term_glossary import (
        BASE_TERM_IDS,
        BAZI_TERM_GLOSSARY,
        GROUP_TERM_IDS,
    )
    from core.ten_god_explanations import TEN_GOD_EXPLANATIONS, TEN_GOD_TERM_IDS

    assert len(BASE_TERM_IDS) == 7
    assert len(GROUP_TERM_IDS) == 5
    assert set(TEN_GOD_TERM_IDS) == TEN_GODS
    assert len(BAZI_TERM_GLOSSARY) == 22
    for term in BAZI_TERM_GLOSSARY.values():
        assert term["definition"].strip()
        assert term["observation_scope"].strip()
        assert term["boundary"].strip()

    for ten_god, term_id in TEN_GOD_TERM_IDS.items():
        assert BAZI_TERM_GLOSSARY[term_id]["definition"] == TEN_GOD_EXPLANATIONS[ten_god]["meaning"]


def test_build_term_view_without_chart_returns_only_public_definition():
    from core.bazi_term_glossary import build_term_view

    view = build_term_view("wealth-star")

    assert view["label"] == "财星"
    assert "personalized" not in view
    assert json.loads(json.dumps(view, ensure_ascii=False)) == view


def test_incomplete_dicts_never_trigger_personalized_content():
    from core.bazi_term_glossary import build_term_view

    incomplete_charts = [
        {"profile": {}},
        {"day_master": "甲"},
        {"day_master": "甲", "pillars": {}},
        {"day_master": "甲", "pillars": {"day": {}}},
        {"day_master": "未知", "pillars": {"day": {"gan": "甲", "zhi": "子"}}},
    ]
    for chart in incomplete_charts:
        view = build_term_view("wealth-star", chart)
        assert "personalized" not in view, chart


def test_personalization_requires_all_four_complete_valid_pillars():
    from core.bazi_term_glossary import build_term_view

    only_day = deepcopy(_chart())
    only_day["pillars"] = {"day": only_day["pillars"]["day"]}
    incomplete_charts = [only_day]
    for missing_pillar in ("year", "month", "hour"):
        chart = deepcopy(_chart())
        del chart["pillars"][missing_pillar]
        incomplete_charts.append(chart)
    invalid_pillar = deepcopy(_chart())
    invalid_pillar["pillars"]["hour"]["gan"] = "未知"
    incomplete_charts.append(invalid_pillar)

    for chart in incomplete_charts:
        view = build_term_view("wealth-star", chart)
        assert "personalized" not in view, chart["pillars"]


def test_missing_or_none_derived_data_never_personalizes_or_fabricates_zero():
    from core.bazi_term_glossary import build_term_view

    no_strength = deepcopy(_chart())
    no_strength["day_master_strength"] = None
    strength_view = build_term_view("strength", no_strength)
    assert strength_view["term_id"] == "strength"
    assert "personalized" not in strength_view

    no_counts = deepcopy(_chart())
    del no_counts["ten_god_counts"]
    wealth_view = build_term_view("wealth-star", no_counts)
    assert "personalized" not in wealth_view
    assert "count" not in wealth_view


def test_build_term_view_personalizes_count_positions_element_role_and_relation():
    from core.bazi_term_glossary import build_term_view

    view = build_term_view("wealth-star", _chart())

    assert view["personalized"]["count"] == 4
    assert view["personalized"]["positions"] == [
        "年柱天干",
        "年柱藏干",
        "月柱天干",
        "月柱藏干",
    ]
    assert "财星" in view["personalized"]["element_role"]
    assert view["personalized"]["favorable_relation"] == "忌神相关"
    assert "本盘财星共4处" in view["personalized"]["interpretation"]
    assert json.loads(json.dumps(view, ensure_ascii=False)) == view


def test_ten_god_view_uses_canonical_copy_and_its_actual_chart_positions():
    from core.bazi_term_glossary import build_term_view
    from core.ten_god_explanations import TEN_GOD_EXPLANATIONS

    view = build_term_view("ten-god-direct-wealth", _chart())

    assert view["definition"] == TEN_GOD_EXPLANATIONS["正财"]["meaning"]
    assert view["personalized"]["count"] == 2
    assert view["personalized"]["positions"] == ["月柱天干", "月柱藏干"]


def test_base_terms_use_semantic_facts_instead_of_count_and_positions():
    from core.bazi_term_glossary import build_term_view

    expected = {
        "day-master": ("day_master", "甲"),
        "strength-weak": ("current_judgment", "身弱"),
        "five-elements": ("distribution", {"木": 2, "火": 1, "土": 4, "金": 0, "水": 1}),
        "pattern": ("current_pattern", "正财格"),
        "favorable-elements": ("related_elements", ["水", "木"]),
        "unfavorable-elements": ("related_elements", ["火", "土"]),
    }
    for term_id, (fact_key, fact_value) in expected.items():
        personal = build_term_view(term_id, _chart())["personalized"]
        assert personal[fact_key] == fact_value
        assert "count" not in personal
        assert "positions" not in personal
        assert "共" not in personal["interpretation"]
        assert "位置为" not in personal["interpretation"]


def test_unknown_term_is_explicit_and_never_fabricates_a_view():
    import pytest

    from core.bazi_term_glossary import build_term_view

    with pytest.raises(KeyError, match="unknown-term"):
        build_term_view("unknown-term", _chart())


def test_identity_strength_alias_does_not_mislabel_a_balanced_chart():
    from core.bazi_term_glossary import BAZI_TERM_GLOSSARY, build_term_view, collect_term_ids

    chart = _chart()
    chart["day_master_strength"]["strength"] = "中和"

    view = build_term_view("strength", chart)

    assert len(BAZI_TERM_GLOSSARY) == 22
    assert view["term_id"] == "strength"
    assert view["label"] == "日主强弱"
    assert view["personalized"]["current_judgment"] == "中和"
    assert "count" not in view["personalized"]
    assert "positions" not in view["personalized"]
    assert collect_term_ids(["strength"], [], chart) == ["strength"]
