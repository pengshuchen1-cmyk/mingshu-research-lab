"""关系维度事实签名、规则优先级与可见文案回归测试。"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest


POSITIONS = ("year", "month", "day", "hour")
ROOT = Path(__file__).resolve().parents[1]
NO_RELATION_COUNTS = {
    "正财": 0,
    "偏财": 0,
    "正官": 0,
    "七杀": 0,
    "食神": 0,
    "伤官": 0,
    "比肩": 0,
    "劫财": 0,
    "正印": 0,
    "偏印": 0,
}


def _chart(
    pillars: tuple[str, str, str, str],
    *,
    gender: str = "男",
    counts: dict[str, int] | None = None,
    strength: str = "中和",
    favorable: list[str] | None = None,
    unfavorable: list[str] | None = None,
    name: str = "签名不应包含此姓名",
) -> dict:
    base_counts = {
        "正财": 1,
        "偏财": 0,
        "正官": 1,
        "七杀": 0,
        "食神": 1,
        "伤官": 0,
        "比肩": 1,
        "劫财": 0,
        "正印": 1,
        "偏印": 0,
    }
    if counts:
        base_counts.update(counts)
    return {
        "day_master": pillars[2][0],
        "pillars": {
            position: {"gan": pillar[0], "zhi": pillar[1], "pillar": pillar}
            for position, pillar in zip(POSITIONS, pillars)
        },
        "ten_god_counts": base_counts,
        "five_elements": {"木": 2, "火": 2, "土": 2, "金": 2, "水": 2},
        "day_master_strength": {
            "strength": strength,
            "net_score": 0,
            "favorable_elements": favorable or [],
            "unfavorable_elements": unfavorable or [],
        },
        "profile": {"name": name, "gender": gender},
    }


RELATIONSHIP_CASES = [
    _chart(("甲子", "丙寅", "甲午", "戊辰")),  # 夫妻宫午、子午冲
    _chart(("乙丑", "丁巳", "乙卯", "己未")),  # 夫妻宫卯
    _chart(("丙寅", "戊辰", "丙申", "庚戌"), counts={"正财": 0, "偏财": 3}),
    _chart(("丁卯", "己巳", "丁午", "辛酉")),  # 午日见卯桃花
    _chart(("戊辰", "庚丑", "戊子", "壬申")),  # 子丑合
    _chart(("己巳", "辛未", "己酉", "癸亥"), favorable=["金"]),  # 夫妻宫喜用
    _chart(("庚午", "壬申", "庚戌", "甲子"), counts={"食神": 2, "伤官": 2}),
    _chart(("辛未", "癸酉", "辛亥", "乙丑"), counts={"比肩": 2, "劫财": 2}),
    _chart(("壬申", "甲戌", "壬寅", "丙辰"), counts={"正印": 2, "偏印": 2}),
    _chart(
        ("癸酉", "乙子", "癸巳", "丁未"),
        gender="女",
        counts={"正官": 0, "七杀": 3},
        strength="身弱",
        unfavorable=["火"],
    ),
]


@pytest.fixture(scope="module")
def relationship_results() -> list[dict]:
    from core.life_overview_engine import analyze_life_overview

    return [analyze_life_overview(deepcopy(chart))["romance_overview"] for chart in RELATIONSHIP_CASES]


def _romance(chart: dict) -> dict:
    from core.life_overview_engine import analyze_life_overview

    return analyze_life_overview(deepcopy(chart))["romance_overview"]


def test_ten_different_pillar_samples_expose_checkable_relationship_signatures(relationship_results):
    assert len({tuple(chart["pillars"][p]["pillar"] for p in POSITIONS) for chart in RELATIONSHIP_CASES}) >= 10

    for result in relationship_results:
        signature = result["relationship_signature"]
        assert set(signature) == {
            "spouse_palace",
            "spouse_relations",
            "spouse_star",
            "ten_god_support",
            "peach_blossom",
            "strength_preference",
        }
        assert set(signature["spouse_palace"]) == {"branch", "element", "role"}
        assert set(signature["spouse_relations"]) == {"clashes", "combinations"}
        assert set(signature["spouse_star"]) == {"basis", "total", "proper", "indirect"}
        assert set(signature["ten_god_support"]) == {"output", "peer", "resource"}
        assert set(signature["peach_blossom"]) == {"count", "positions"}
        assert set(signature["strength_preference"]) == {"strength"}
        assert "签名不应包含此姓名" not in str(signature)
        assert "random" not in str(signature).lower()


def test_signature_uses_gender_conditioned_spouse_star_and_proper_indirect_distribution(relationship_results):
    male = relationship_results[2]["relationship_signature"]["spouse_star"]
    female = relationship_results[9]["relationship_signature"]["spouse_star"]

    assert male == {"basis": "财星", "total": 3, "proper": 0, "indirect": 3}
    assert female == {"basis": "官杀", "total": 3, "proper": 0, "indirect": 3}


def test_signature_records_spouse_palace_clash_combination_peach_and_preferences(relationship_results):
    clash = relationship_results[0]["relationship_signature"]
    combination = relationship_results[4]["relationship_signature"]
    peach = relationship_results[3]["relationship_signature"]
    favorable = relationship_results[5]["relationship_signature"]

    assert clash["spouse_palace"] == {"branch": "午", "element": "火", "role": "中性"}
    assert clash["spouse_relations"]["clashes"] == ["年支子午冲"]
    assert combination["spouse_relations"]["combinations"] == ["月支子丑合"]
    assert peach["peach_blossom"] == {"count": 1, "positions": ["year"]}
    assert favorable["spouse_palace"] == {"branch": "酉", "element": "金", "role": "喜用"}


def test_strength_change_alone_alters_primary_relationship_focus():
    neutral = _chart(
        ("甲寅", "丙寅", "甲酉", "戊寅"),
        counts=NO_RELATION_COUNTS,
        strength="中和",
    )
    strong = deepcopy(neutral)
    strong["day_master_strength"]["strength"] = "身强"
    left = _romance(neutral)
    right = _romance(strong)

    assert left["relationship_signature"] != right["relationship_signature"]
    assert left["core_portrait"] == right["core_portrait"] == "关系信号待观察"
    assert left["primary_relationship_focus"] != right["primary_relationship_focus"]
    assert "身强" in right["primary_relationship_focus"]


def test_unrelated_favorable_lists_do_not_enter_signature_or_change_output():
    left_chart = _chart(
        ("甲寅", "丙寅", "甲酉", "戊寅"),
        counts=NO_RELATION_COUNTS,
        favorable=["水"],
        unfavorable=["火"],
    )
    right_chart = deepcopy(left_chart)
    right_chart["day_master_strength"]["favorable_elements"] = ["木"]
    right_chart["day_master_strength"]["unfavorable_elements"] = ["土"]

    left = _romance(left_chart)
    right = _romance(right_chart)
    assert left["relationship_signature"] == right["relationship_signature"]
    assert left == right


@pytest.mark.parametrize("gender", ["女", ""])
def test_same_relationship_signature_produces_identical_relationship_output(gender):
    left_chart = _chart(
        ("甲寅", "丙寅", "甲酉", "戊寅"),
        gender=gender,
        counts={**NO_RELATION_COUNTS, "食神": 3},
    )
    right_chart = deepcopy(left_chart)
    right_chart["ten_god_counts"]["正财"] = 3
    right_chart["ten_god_counts"]["偏财"] = 2

    left = _romance(left_chart)
    right = _romance(right_chart)
    assert left["relationship_signature"] == right["relationship_signature"]
    assert left == right


def test_complete_chart_without_effective_relationship_rule_uses_neutral_empty_state():
    result = _romance(
        _chart(
            ("甲寅", "丙寅", "甲酉", "戊寅"),
            counts=NO_RELATION_COUNTS,
            strength="中和",
        )
    )

    assert result["relationship_signature"]["spouse_palace"]["branch"] == "酉"
    assert result["core_portrait"] == "关系信号待观察"
    assert result["primary_relationship_focus"] == "当前关系信号不集中，结合现实互动继续观察"
    assert result["attraction_points"] == []
    assert result["relationship_strengths"] == []
    assert result["relationship_risks"] == []
    assert result["suitable_partner_type"] == []
    assert "信息不完整" not in result["romance_summary"]


def test_single_relationship_fact_changes_alter_portrait_or_focus():
    neutral = _chart(
        ("甲寅", "丙寅", "甲酉", "戊寅"),
        counts=NO_RELATION_COUNTS,
        strength="中和",
    )
    pairs = {}

    palace_left = _chart(
        ("甲寅", "丙寅", "甲午", "戊寅"),
        counts=NO_RELATION_COUNTS,
        favorable=["金"],
    )
    palace_right = deepcopy(palace_left)
    palace_right["pillars"]["day"] = {"gan": "甲", "zhi": "酉", "pillar": "甲酉"}
    pairs["夫妻宫支五行"] = (palace_left, palace_right)

    spouse_star = deepcopy(neutral)
    spouse_star["ten_god_counts"]["偏财"] = 3
    pairs["配偶星"] = (neutral, spouse_star)

    peach_left = _chart(
        ("甲寅", "丙寅", "甲午", "戊寅"),
        counts=NO_RELATION_COUNTS,
    )
    peach = deepcopy(peach_left)
    peach["pillars"]["year"] = {"gan": "甲", "zhi": "卯", "pillar": "甲卯"}
    pairs["桃花"] = (peach_left, peach)

    clash = deepcopy(peach_left)
    clash["pillars"]["year"] = {"gan": "甲", "zhi": "子", "pillar": "甲子"}
    pairs["冲合"] = (peach_left, clash)

    strong = deepcopy(neutral)
    strong["day_master_strength"]["strength"] = "身强"
    pairs["强弱"] = (neutral, strong)

    favorable = deepcopy(neutral)
    favorable["day_master_strength"]["favorable_elements"] = ["金"]
    pairs["夫妻宫喜忌"] = (neutral, favorable)

    for label, (left_chart, right_chart) in pairs.items():
        left = _romance(left_chart)
        right = _romance(right_chart)
        assert left["relationship_signature"] != right["relationship_signature"], label
        assert (
            left["core_portrait"], left["primary_relationship_focus"]
        ) != (
            right["core_portrait"], right["primary_relationship_focus"]
        ), label


def test_different_effective_signatures_change_core_portrait_or_primary_focus(relationship_results):
    # 每一对只改变一类关键事实，结论必须在核心画像或主要经营点上可辨认。
    pairs = [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 9)]
    for left_index, right_index in pairs:
        left = relationship_results[left_index]
        right = relationship_results[right_index]
        assert left["relationship_signature"] != right["relationship_signature"]
        assert (
            left["core_portrait"],
            left["primary_relationship_focus"],
        ) != (
            right["core_portrait"],
            right["primary_relationship_focus"],
        )
        assert left["core_portrait"] in left["romance_summary"]
        assert left["primary_relationship_focus"] in left["romance_summary"]


def test_specific_relationship_signals_outrank_generic_planning_and_companionship(relationship_results):
    clashed = relationship_results[0]
    peach = relationship_results[3]
    expressive = relationship_results[6]
    peer_boundaries = relationship_results[7]

    assert clashed["core_portrait"] == "边界修复型"
    assert peach["core_portrait"] == "社交互动型"
    assert expressive["core_portrait"] == "表达协商型"
    assert peer_boundaries["core_portrait"] == "独立边界型"
    for result in (clashed, peach, expressive, peer_boundaries):
        assert result["core_portrait"] not in {"婚姻规划型", "稳定陪伴型"}


def test_relationship_copy_has_two_to_four_truthful_evidence_items(relationship_results):
    for chart, result in zip(RELATIONSHIP_CASES, relationship_results):
        evidence = result["evidence"]
        signature = result["relationship_signature"]
        assert 2 <= len(evidence) <= 4
        assert f"夫妻宫：{signature['spouse_palace']['branch']}（{signature['spouse_palace']['element']}，{signature['spouse_palace']['role']}）" in evidence
        assert f"{signature['spouse_star']['basis']}：正星{signature['spouse_star']['proper']}/偏星{signature['spouse_star']['indirect']}" in evidence
        assert all("待确认" not in item for item in evidence)
        assert chart["profile"]["name"] not in str(evidence)


@pytest.mark.parametrize(
    ("chart", "driver_text"),
    [
        (_chart(("甲子", "丙寅", "甲午", "戊辰")), "冲合："),
        (_chart(("甲卯", "丙寅", "甲午", "戊辰")), "桃花："),
        (
            _chart(
                ("甲寅", "丙寅", "甲酉", "戊寅"),
                counts={**NO_RELATION_COUNTS, "食神": 3},
            ),
            "十神辅助：食伤3",
        ),
        (
            _chart(
                ("甲寅", "丙寅", "甲酉", "戊寅"),
                counts=NO_RELATION_COUNTS,
                strength="身强",
            ),
            "日主强弱：身强",
        ),
        (
            _chart(
                ("甲寅", "丙寅", "甲酉", "戊寅"),
                counts=NO_RELATION_COUNTS,
                favorable=["金"],
            ),
            "喜用",
        ),
    ],
)
def test_evidence_contains_the_fact_that_drives_portrait_or_focus(chart, driver_text):
    result = _romance(chart)
    assert 2 <= len(result["evidence"]) <= 4
    assert any(driver_text in item for item in result["evidence"])


def test_evidence_keeps_both_core_rule_and_strength_focus_drivers_with_multiple_signals():
    chart = _chart(
        ("甲卯", "丙子", "甲午", "戊寅"),
        strength="身强",
    )
    result = _romance(chart)

    assert result["core_portrait"] == "边界修复型"
    assert "身强" in result["primary_relationship_focus"]
    assert any("冲合：" in item for item in result["evidence"])
    assert any("日主强弱：身强" in item for item in result["evidence"])
    assert 2 <= len(result["evidence"]) <= 4


def test_unmatched_relationship_rules_return_neutral_empty_state():
    from core.life_overview_engine import analyze_life_overview

    result = analyze_life_overview(
        {
            "profile": {},
            "pillars": {},
            "ten_god_counts": {},
            "five_elements": {},
            "day_master_strength": {},
        }
    )["romance_overview"]

    assert result["core_portrait"] == "关系信号待观察"
    assert result["primary_relationship_focus"] == "先补充出生信息，再结合现实互动观察"
    assert result["relationship_strengths"] == []
    assert result["relationship_risks"] == []
    assert result["evidence"] == ["夫妻宫与配偶星信息暂不完整", "当前不据空缺信息推断关系类型"]
    assert "家庭介入" not in result["romance_summary"]
    assert "稳定陪伴" not in result["romance_summary"]


def test_missing_gender_does_not_default_to_the_male_spouse_star_scope():
    from core.life_overview_engine import analyze_life_overview

    chart = _chart(
        ("甲子", "丙寅", "甲酉", "戊未"),
        gender="",
        counts={"正财": 3, "偏财": 2, "正官": 0, "七杀": 0},
    )
    result = analyze_life_overview(chart)
    signature = result["romance_overview"]["relationship_signature"]

    assert signature["spouse_star"] == {
        "basis": "配偶星口径未设定",
        "total": 0,
        "proper": 0,
        "indirect": 0,
    }
    assert result["score_details"]["romance"]["sub_scores"]["spouse_star_visibility"] == 0


def test_relationship_copy_avoids_deterministic_discriminatory_or_professional_substitution_language(relationship_results):
    forbidden = [
        "必定",
        "绝对",
        "注定",
        "一定离婚",
        "克夫",
        "克妻",
        "不守妇道",
        "低人一等",
        "替代医生",
        "替代律师",
    ]
    text = str(relationship_results)
    for phrase in forbidden:
        assert phrase not in text


def test_python_is_the_single_runtime_source_for_priority_and_fallback():
    payload = json.loads((ROOT / "rules" / "romance_overview_rules.json").read_text(encoding="utf-8"))
    assert all("priority" not in rule for rule in payload["rules"])
    assert "fallback" not in payload
