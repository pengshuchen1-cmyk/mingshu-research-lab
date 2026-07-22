"""第三轮小程序公开展示 DTO 与隐私投影回归测试。"""

from __future__ import annotations

import copy
import json
import math

import pytest


def _private_identity_card() -> dict:
    return {
        "name": "林小满",
        "day_master": "乙",
        "day_element": "木",
        "strength": "身弱",
        "dominant_elements": ["金"],
        "pattern": "财星格局",
        "summary": "林小满出生于1999-08-11，地点广东汕头；乙木日主身弱。",
        "term_ids": ["day-master", "wealth-star"],
        "profile": {
            "birth_date": "1999-08-11",
            "birth_time": "10:23",
            "birth_place": "广东汕头",
        },
        "source_titles": ["内部典籍"],
    }


def _private_term_view() -> dict:
    return {
        "term_id": "wealth-star",
        "label": "财星",
        "definition": "财星用于观察现实经营与资源交换。",
        "observation_scope": "林小满可观察收入、支出与成果承接。",
        "boundary": "不等于必然有钱。",
        "personalized": {
            "count": 2,
            "positions": ["年柱天干", "月柱藏干"],
            "element_role": "土 · 财星",
            "favorable_relation": "中性观察",
            "interpretation": (
                "广东汕头的林小满（别名隐私别名，1999/08/11，秘密地点），"
                "本盘财星共2处。"
            ),
            "source_ids": ["internal_book"],
            "nested": {"relationship_signature": {"spouse_palace": "午"}},
            "metadata": {
                "user_name": "隐私别名",
                "date_of_birth": "1999/08/11",
                "location": "秘密地点",
            },
        },
        "source_titles": ["内部典籍"],
        "name": "林小满",
    }


def _private_dimension_view() -> dict:
    return {
        "key": "relationship",
        "label": "关系",
        "score": 68,
        "level": "中上",
        "summary": "林小满的关系节奏重在边界与沟通。",
        "detail_label": "证据",
        "evidence": ["夫妻宫五行为木"],
        "strengths": ["愿意经营稳定关系"],
        "risks": ["需要避免替对方做决定"],
        "advice": ["把感受和安排分别说清"],
        "relationship_signature": {"spouse_palace": {"branch": "午"}},
        "audit": {"source_ids": ["internal_book"]},
        "profile": {"name": "林小满", "birth_place": "广东汕头"},
    }


def test_real_public_dto_builders_expose_every_round_three_component_field():
    from core.presentation_models import (
        build_five_dimension_insight_view,
        build_personal_identity_card_view,
        build_term_chip_view,
        build_term_detail_view,
    )

    identity = build_personal_identity_card_view(_private_identity_card())
    chip = build_term_chip_view(_private_term_view())
    detail = build_term_detail_view(_private_term_view())
    dimension = build_five_dimension_insight_view(_private_dimension_view())

    assert set(identity) == {
        "kind",
        "day_master",
        "day_element",
        "strength",
        "dominant_elements",
        "pattern",
        "summary",
        "term_ids",
    }
    assert set(chip) == {
        "kind",
        "term_id",
        "label",
        "group",
        "accessibility_label",
    }
    assert set(detail) == {
        "kind",
        "term_id",
        "label",
        "definition",
        "observation_scope",
        "boundary",
        "personalized",
    }
    assert set(dimension) == {
        "kind",
        "key",
        "label",
        "score",
        "level",
        "summary",
        "detail_label",
        "evidence",
        "strengths",
        "risks",
        "advice",
    }
    assert chip["group"] == "ten_god_group"
    assert chip["accessibility_label"] == "查看命理术语：财星"
    assert dimension["key"] == "relationship"
    assert json.loads(json.dumps([identity, chip, detail, dimension], ensure_ascii=False))


def test_public_chart_projection_recursively_removes_audit_keys_and_raw_pii_values():
    from core.presentation_models import build_chart_public_view

    identity = _private_identity_card()
    term = _private_term_view()
    dimension = _private_dimension_view()
    before = copy.deepcopy((identity, term, dimension))

    public = build_chart_public_view(identity, [term], [dimension])
    serialized = json.dumps(public, ensure_ascii=False)

    for forbidden_key in [
        "source_titles",
        "source_ids",
        "relationship_signature",
        "name",
        "birth_date",
        "birth_time",
        "birth_place",
        "profile",
    ]:
        assert forbidden_key not in serialized
    for forbidden_value in [
        "林小满",
        "隐私别名",
        "1999-08-11",
        "1999/08/11",
        "10:23",
        "广东汕头",
        "秘密地点",
        "内部典籍",
    ]:
        assert forbidden_value not in serialized
    assert public["identity_card"]["day_master"] == "乙"
    assert public["term_details"][0]["personalized"]["count"] == 2
    assert public["five_dimensions"][0]["key"] == "relationship"
    assert (identity, term, dimension) == before
    assert term["source_titles"] == ["内部典籍"]
    assert dimension["relationship_signature"]["spouse_palace"]["branch"] == "午"


def test_public_projection_rejects_unknown_or_missing_stable_dimension_keys():
    import pytest

    from core.presentation_models import build_five_dimension_insight_view

    for invalid_key in [None, "", "romance", "unknown"]:
        dimension = _private_dimension_view()
        dimension["key"] = invalid_key
        with pytest.raises(ValueError, match="五维稳定键"):
            build_five_dimension_insight_view(dimension)


def test_one_character_local_name_is_removed_from_narrative_without_losing_day_master():
    from core.presentation_models import build_personal_identity_card_view

    identity = _private_identity_card()
    identity["name"] = "李"
    identity["summary"] = "李的日主为乙木，适合观察长期节奏。"

    public = build_personal_identity_card_view(identity)

    assert public["day_master"] == "乙"
    assert "李" not in public["summary"]
    assert "乙木" in public["summary"]


@pytest.mark.parametrize(
    ("local_name", "field", "expected"),
    [
        ("乙", "day_master", "乙"),
        ("金", "day_element", "金"),
        ("强", "strength", "身强"),
    ],
)
def test_pii_scrubbing_never_erases_safe_structural_enum_fields(
    local_name, field, expected
):
    from core.presentation_models import build_personal_identity_card_view

    identity = _private_identity_card()
    identity.update(
        {
            "name": local_name,
            "day_master": "乙",
            "day_element": "金",
            "strength": "身强",
            "pattern": "财星格局",
            "summary": f"{local_name}的命盘为乙日主、金偏旺、身强。",
        }
    )

    public = build_personal_identity_card_view(identity)

    assert public[field] == expected
    assert local_name not in public["summary"]


def test_term_disclosure_state_has_stable_aria_relationship_and_focus_return_target():
    from core.presentation_models import (
        build_term_disclosure_semantics,
        transition_term_disclosure,
    )

    closed = build_term_disclosure_semantics("wealth-star", None, label="财星")
    opened = build_term_disclosure_semantics(
        "wealth-star", "wealth-star", label="财星"
    )
    assert closed == {
        "button_id": "term-chip-wealth-star",
        "controls_id": "term-detail-wealth-star",
        "aria_expanded": "false",
        "accessibility_label": "查看命理术语：财星",
    }
    assert opened["aria_expanded"] == "true"

    open_transition = transition_term_disclosure(None, "wealth-star")
    close_transition = transition_term_disclosure("wealth-star", "wealth-star")
    assert open_transition == {
        "active_term_id": "wealth-star",
        "restore_focus_to": None,
    }
    assert close_transition == {
        "active_term_id": None,
        "restore_focus_to": "term-chip-wealth-star",
    }


def test_audit_values_are_removed_by_key_without_corrupting_shared_public_terms():
    from core.presentation_models import build_chart_public_view

    identity = _private_identity_card()
    identity.update(
        {
            "day_element": "火",
            "strength": "身强",
            "pattern": "财星",
            "summary": "火日主身强，财星3处。",
            "sourceTitles": ["火", "财星", "身强", "3"],
            "source_titles": ["火", "财星", "身强", "3"],
            "relationshipSignature": {
                "element": "火",
                "group": "财星",
                "strength": "身强",
                "count": 3,
            },
            "profile": {"computedElement": "火", "computedStrength": "身强"},
            "raw_chart": {"pattern": "财星", "count": 3},
        }
    )
    term = _private_term_view()
    term["sourceIds"] = ["财星", "火"]
    term["source_ids"] = ["财星", "火"]
    dimension = _private_dimension_view()
    dimension["sourceTitles"] = ["身强", "3"]
    dimension["relationship_signature"] = {"strength": "身强", "count": 3}

    public = build_chart_public_view(identity, [term], [dimension])
    serialized = json.dumps(public, ensure_ascii=False)

    assert public["identity_card"]["day_element"] == "火"
    assert public["identity_card"]["strength"] == "身强"
    assert public["identity_card"]["pattern"] == "财星"
    assert public["identity_card"]["summary"] == "火日主身强，财星3处"
    assert public["term_chips"][0]["label"] == "财星"
    for forbidden_key in [
        "sourceTitles",
        "sourceIds",
        "relationshipSignature",
    ]:
        assert forbidden_key not in serialized


def test_camel_case_pii_date_variants_and_deep_personalized_objects_are_not_exposed():
    from core.presentation_models import build_chart_public_view

    identity = _private_identity_card()
    identity["profile"] = {
        "displayName": "林小满",
        "birthDate": "1999-08-11",
        "birthPlace": "广东汕头",
    }
    identity["summary"] = (
        "林小满：1999-08-11、1999/08/11、1999.08.11、1999年08月11日，"
        "出生地点广东汕头。乙木日主身弱。"
    )
    term = _private_term_view()
    term["personalized"].update(
        {
            "positions": ["年柱天干", {"sourceTitles": ["内部典籍"]}, 7],
            "related_elements": ["木", {"relationshipSignature": {"x": 1}}],
            "distribution": {
                "木": 2,
                "火": 1.5,
                "sourceTitles": ["内部典籍"],
                "relationshipSignature": {"strength": "身强"},
                "nested": {"birthDate": "1999/08/11"},
            },
        }
    )

    public = build_chart_public_view(identity, [term], [_private_dimension_view()])
    serialized = json.dumps(public, ensure_ascii=False)
    personalized = public["term_details"][0]["personalized"]

    for forbidden in [
        "林小满",
        "广东汕头",
        "1999-08-11",
        "1999/08/11",
        "1999.08.11",
        "1999年08月11日",
        "sourceTitles",
        "relationshipSignature",
        "birthDate",
        "nested",
    ]:
        assert forbidden not in serialized
    assert personalized["positions"] == ["年柱天干"]
    assert personalized["related_elements"] == ["木"]
    assert personalized["distribution"] == {"木": 2.0, "火": 1.5}


def test_identity_term_aliases_resolve_to_term_chips_without_dangling_ids():
    from core.bazi_term_glossary import build_term_view
    from core.presentation_models import build_chart_public_view

    chart = {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "戊", "zhi": "辰"},
            "month": {"gan": "己", "zhi": "丑"},
            "day": {"gan": "甲", "zhi": "子"},
            "hour": {"gan": "丙", "zhi": "寅"},
        },
        "day_master_strength": {
            "strength": "身强",
            "favorable_elements": ["火", "土"],
            "unfavorable_elements": ["水", "木"],
        },
        "ten_god_counts": {"偏财": 2, "正财": 2, "比肩": 2, "食神": 1},
        "five_elements": {"木": 2, "火": 1, "土": 4, "金": 0, "水": 1},
        "ten_gods": {
            "year": {"gan": "偏财"},
            "month": {"gan": "正财"},
            "day": {"gan": "比肩"},
            "hour": {"gan": "食神"},
        },
        "hidden_stems": {"year": [], "month": [], "day": [], "hour": []},
        "pattern_analysis": {"pattern": "正财格"},
    }
    identity = _private_identity_card()
    identity["term_ids"] = [
        "day-master",
        "day-element-fire",
        "strength",
        "element-fire",
        "element-water",
        "pattern",
    ]
    term_views = [
        build_term_view("day-master", chart),
        build_term_view("day-element-fire", chart),
        build_term_view("strength", chart),
        build_term_view("pattern", chart),
    ]

    public = build_chart_public_view(identity, term_views, [_private_dimension_view()])
    identity_term_ids = public["identity_card"]["term_ids"]
    chip_ids = [chip["term_id"] for chip in public["term_chips"]]

    assert identity_term_ids == [
        "day-master",
        "five-elements",
        "strength-strong",
        "pattern",
    ]
    assert set(identity_term_ids) <= set(chip_ids)


@pytest.mark.parametrize(
    "raw_score",
    [math.inf, -math.inf, math.nan, "not-a-number", None, True],
)
def test_non_finite_or_invalid_dimension_scores_fall_back_to_zero(raw_score):
    from core.presentation_models import build_five_dimension_insight_view

    dimension = _private_dimension_view()
    dimension["score"] = raw_score

    public = build_five_dimension_insight_view(dimension)

    assert public["score"] == 0
    assert isinstance(public["score"], int)
