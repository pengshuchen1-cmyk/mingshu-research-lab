from __future__ import annotations

import pytest


def _context():
    from core.ai_models import AIRequestContext

    return AIRequestContext(
        question="财运如何？",
        category="wealth",
        requires_timing=False,
        chart_facts={
            "pillars": ["甲戌", "癸酉", "壬子", "己酉"],
            "gender": "male",
            "day_master": "壬",
            "strength": {
                "classification": "身强",
                "evidence": ["月令生扶"],
                "favorable_elements": ["木", "火", "土"],
                "unfavorable_elements": ["金", "水"],
            },
            "pattern": {"classification": "正印格", "evidence": ["月令主气"]},
            "wealth": {"summary": "重视现金流", "evidence": ["财星可见"]},
            "element_counts": {"木": 1.0, "火": 0.3, "土": 2.0, "金": 4.5, "水": 3.0},
            "ten_gods": {
                "year": {"gan": "食神", "hidden_stems": [{"gan": "戊", "ten_god": "七杀"}]},
                "month": {"gan": "劫财", "hidden_stems": [{"gan": "辛", "ten_god": "正印"}]},
                "day": {"gan": "比肩", "hidden_stems": [{"gan": "癸", "ten_god": "劫财"}]},
                "hour": {"gan": "正官", "hidden_stems": [{"gan": "辛", "ten_god": "正印"}]},
            },
            "dayun": {"direction": "顺排", "start": "约5年0个月12天起运"},
            "dayun_periods": [
                {
                    "pillar": "己巳",
                    "start_age": 21,
                    "end_age": 30,
                    "start_year": 2020,
                    "end_year": 2029,
                    "ten_god": "偏财",
                },
                {
                    "pillar": "戊辰",
                    "start_age": 31,
                    "end_age": 40,
                    "start_year": 2030,
                    "end_year": 2039,
                    "ten_god": "正财",
                },
            ],
            "relationship": {
                "summary": "桃花只是互动机会，不等于关系成立。",
                "evidence": ["配偶星与夫妻宫共同观察"],
                "stability_signals": [
                    {"polarity": "mixed", "fact": "日支子；合为无；冲为无", "explanation": "中性观察"}
                ],
            },
            "current_context": {
                "year": 2026,
                "year_pillar": "丙午",
                "month_pillar": "乙未",
                "day_pillar": "辛丑",
            },
        },
        rule_evidence=[
            {"id": "WEALTH-CAPACITY", "statement": "承财能力要结合日主强弱"}
        ],
        history=[],
    )


def _answer(text, chart_evidence=None, **overrides):
    from core.ai_models import BaziAIAnswer

    values = {
        "analysis_conclusion": text,
        "chart_evidence": chart_evidence or ["壬日主，命局身强"],
        "rule_evidence": ["承财能力要结合日主强弱"],
        "timing_conditions": ["后续阶段仍需结合现实条件观察"],
        "practical_advice": ["控制现金流风险"],
        "uncertainty_limitations": ["现实收入仍取决于选择"],
    }
    values.update(overrides)
    return BaziAIAnswer(**values)


def test_guard_accepts_consistent_evidence():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(_answer("壬日主身强，财务宜控制现金流。"), _context())

    assert result.accepted is True
    assert result.violations == ()


def test_guard_rejects_wrong_pillar_and_guarantee_language():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("乙巳日主一定会肯定发财。", ["日柱乙巳"]),
        _context(),
    )

    assert result.accepted is False
    assert "chart_fact_contradiction" in result.violations
    assert "deterministic_claim" in result.violations


def test_guard_checks_the_natural_main_answer_even_when_optional_lists_are_empty():
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion="乙巳日主一定会发财。",
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())
    assert result.accepted is False
    assert "deterministic_claim" in result.violations


@pytest.mark.parametrize(
    ("claim", "violation"),
    [
        ("这个命局的喜用五行为金。", "favorable_element_contradiction"),
        ("此命忌神为木火。", "unfavorable_element_contradiction"),
        ("五行中木的数量为9。", "element_count_contradiction"),
        ("年干十神为正官。", "ten_god_contradiction"),
        ("甲的十神为正官。", "ten_god_contradiction"),
        ("藏干戊为正官。", "ten_god_contradiction"),
        ("正印共有9个。", "ten_god_count_contradiction"),
        ("大运方向为逆排。", "dayun_contradiction"),
        ("此命99岁起运。", "dayun_contradiction"),
        ("2026年流年柱为甲子。", "timing_fact_contradiction"),
        ("当前月柱为甲寅。", "timing_fact_contradiction"),
        ("当前大运为甲寅。", "dayun_contradiction"),
        ("夫妻宫为午。", "relationship_fact_contradiction"),
        ("命盘存在子午冲。", "relationship_fact_contradiction"),
        ("命盘存在子丑合。", "relationship_fact_contradiction"),
        ("命盘桃花共有9个。", "relationship_fact_contradiction"),
    ],
)
def test_guard_rejects_explicit_canonical_fact_contradictions_with_empty_lists(
    claim,
    violation,
):
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion=claim,
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())

    assert result.accepted is False
    assert violation in result.violations


@pytest.mark.parametrize(
    "claim",
    (
        "你必定发财。",
        "这段婚姻绝对成功。",
        "这个项目毫无疑问会赚钱。",
        "她铁定已经结婚。",
        "抵押房子创业必成。",
    ),
)
def test_guard_rejects_broader_absolute_claims_in_natural_answer(claim):
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(_answer(claim, chart_evidence=[]), _context())

    assert "deterministic_claim" in result.violations


def test_guard_accepts_matching_explicit_canonical_facts():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer(
            "此命喜用五行为木火，忌神为金水；五行中木的数量为1。"
            "年干十神为食神，正印共有2个。大运方向为顺排，约5岁起运。"
            "偏财共有0个。2026年流年柱为丙午，当前月柱为乙未，"
            "夫妻宫为子，命盘无冲。"
        ),
        _context(),
    )

    assert result.accepted is True


def test_guard_accepts_locally_supplied_dayun_start_mapping():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("2030年开始进入戊辰正财大运，约31岁起。"),
        _context(),
    )

    assert result.accepted is True


@pytest.mark.parametrize(
    "claim",
    (
        "2028年开始进入戊辰正财大运。",
        "2030年开始进入己巳偏财大运。",
        "戊辰属于偏财大运。",
    ),
)
def test_guard_rejects_wrong_dayun_start_mapping(claim):
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(_answer(claim), _context())

    assert result.accepted is False
    assert "dayun_contradiction" in result.violations


@pytest.mark.parametrize(
    "claim",
    (
        "此命喜金忌木。",
        "命局喜用金水，忌木。",
        "此局以金为喜，以木为忌。",
    ),
)
def test_guard_rejects_bare_and_paired_favorable_element_contradictions(
    claim,
):
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion=claim,
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())

    assert result.accepted is False
    assert {
        "favorable_element_contradiction",
        "unfavorable_element_contradiction",
    } & set(result.violations)


def test_guard_accepts_matching_bare_favorable_elements_and_ordinary_like_word():
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion="此命喜木火土，忌金水；平时喜欢稳健推进。",
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())

    assert result.accepted is True


@pytest.mark.parametrize(
    "claim",
    (
        "此命不喜金水。",
        "命局并不喜金水。",
        "此命不太喜金水。",
        "此命不忌木火土。",
        "命局并不忌木火土。",
        "此命不 喜金水。",
        "命局并不 喜金水。",
        "此命不 忌木火土。",
    ),
)
def test_guard_accepts_matching_negated_favorable_dispositions(claim):
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion=claim,
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    assert validate_ai_answer(answer, _context()).accepted is True


@pytest.mark.parametrize(
    "claim",
    (
        "此命不喜木火土。",
        "命局并不喜木。",
        "此命不太喜火。",
        "此命不忌金水。",
        "命局并不忌金。",
        "此命不 喜木火土。",
        "命局并不 喜木。",
        "此命不 忌金水。",
    ),
)
def test_guard_rejects_inverse_wrong_negated_favorable_dispositions(claim):
    from core.ai_answer_guard import validate_ai_answer
    from core.ai_models import BaziAIAnswer

    answer = BaziAIAnswer(
        analysis_conclusion=claim,
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )

    result = validate_ai_answer(answer, _context())

    assert result.accepted is False
    assert {
        "favorable_element_contradiction",
        "unfavorable_element_contradiction",
    } & set(result.violations)


def test_guard_does_not_treat_uncertain_not_necessarily_successful_as_absolute():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer(
            "即使条件较好，现实执行仍未必成功，不一定会发财，"
            "也不能保证成功，结果并非铁定。"
        ),
        _context(),
    )

    assert "deterministic_claim" not in result.violations


@pytest.mark.parametrize(
    "claim",
    (
        "不存在绝对成功，仍需结合现实。",
        "不存在所谓绝对成功，仍需结合现实。",
        "谈不上绝对成功，仍需结合现实。",
    ),
)
def test_guard_accepts_clause_aware_negation_of_absolute_claim(claim):
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(_answer(claim), _context())

    assert "deterministic_claim" not in result.violations


def test_guard_does_not_allow_negation_in_prior_clause_to_hide_absolute_claim():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("不存在绝对失败，但这个项目绝对成功。"),
        _context(),
    )

    assert "deterministic_claim" in result.violations


def test_guard_distinguishes_natal_and_current_month_day_pillar_claims():
    from core.ai_answer_guard import validate_ai_answer

    context = _context()
    correct = validate_ai_answer(
        _answer(
            "本命月柱为癸酉，日柱为壬子；"
            "当前月柱为乙未，今日柱为辛丑。"
        ),
        context,
    )
    wrong_natal = validate_ai_answer(
        _answer("本命月柱为乙未，日柱为辛丑。"),
        context,
    )

    assert "timing_fact_contradiction" not in correct.violations
    assert "natal_pillar_contradiction" not in correct.violations
    assert "natal_pillar_contradiction" in wrong_natal.violations


def test_natal_pillars_validate_without_current_context_and_current_claim_rejects():
    from core.ai_answer_guard import validate_ai_answer

    context = _context().model_copy(
        update={
            "chart_facts": {
                key: value
                for key, value in _context().chart_facts.items()
                if key != "current_context"
            }
        }
    )
    natal = validate_ai_answer(
        _answer("月柱为癸酉，日柱为壬子。"),
        context,
    )
    current = validate_ai_answer(
        _answer("当前月柱为乙未，今日柱为辛丑。"),
        context,
    )

    assert natal.accepted is True
    assert "timing_fact_contradiction" in current.violations


def test_guard_does_not_treat_generic_relationship_rule_as_actual_clash_or_combine():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("有合重在边界与承诺落实，有冲重在变化和沟通管理。"),
        _context(),
    )

    assert "relationship_fact_contradiction" not in result.violations


def test_guard_rejects_gender_pattern_wealth_and_spouse_star_contradictions():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer(
            "这是女命、七杀格，财星为金，配偶星为印星。",
            ["壬日主"],
        ),
        _context(),
    )

    assert result.accepted is False
    assert "gender_contradiction" in result.violations
    assert "pattern_contradiction" in result.violations
    assert "wealth_element_contradiction" in result.violations
    assert "spouse_star_contradiction" in result.violations


def test_guard_requires_exactly_mappable_evidence_not_two_character_overlap():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("财务建议需谨慎。", ["命局财务需谨慎"]),
        _context(),
    )

    assert result.accepted is False
    assert "unmapped_chart_evidence" in result.violations


def test_guard_rejects_mixed_correct_and_incorrect_claims():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer(
            "男命也是女命，正印格也是七杀格，财星为火也为金，"
            "配偶星为财星也为印星，身强也是身弱。"
        ),
        _context(),
    )

    assert result.accepted is False
    assert {
        "gender_contradiction", "pattern_contradiction", "wealth_element_contradiction",
        "spouse_star_contradiction", "strength_contradiction",
    } <= set(result.violations)


def test_structured_answer_rejects_blank_evidence_items():
    import pytest
    from pydantic import ValidationError
    from core.ai_models import BaziAIAnswer

    with pytest.raises(ValidationError):
        BaziAIAnswer(
            analysis_conclusion="回答",
            chart_evidence=[""],
            rule_evidence=[""],
            timing_conditions=["阶段条件"],
            practical_advice=["现实建议"],
            uncertainty_limitations=["不确定性"],
        )


def test_guard_rejects_common_wealth_and_spouse_synonym_claims():
    from core.ai_answer_guard import validate_ai_answer

    for text in (
        "此命财星是金，妻星为印星。",
        "此命以印星为妻星，属于男命。",
        "此命财星五行为金，配偶星属印星。",
    ):
        result = validate_ai_answer(_answer(text), _context())
        assert result.accepted is False
        assert {"wealth_element_contradiction", "spouse_star_contradiction"} & set(
            result.violations
        )


def test_guard_examines_main_answer_and_machine_support_fields():
    from core.ai_answer_guard import validate_ai_answer

    cases = [
        ("analysis_conclusion", "一定会成功"),
        ("chart_evidence", ["壬日主，命局身强，一定会成功"]),
        ("rule_evidence", ["承财能力要结合日主强弱，一定会成功"]),
        ("timing_conditions", ["这个阶段一定会成功"]),
        ("practical_advice", ["采取行动一定会成功"]),
        ("uncertainty_limitations", ["即使有限制也一定会成功"]),
    ]

    for field, value in cases:
        answer = _answer("壬日主身强，财务宜控制现金流。", **{field: value})
        result = validate_ai_answer(answer, _context())
        assert "deterministic_claim" in result.violations, field


def test_current_marriage_guard_rejects_unqualified_real_world_status_claim():
    from core.ai_answer_guard import validate_ai_answer

    context = _context().model_copy(
        update={
            "question": "当前婚姻状态",
            "category": "relationship",
        }
    )
    result = validate_ai_answer(
        _answer("你现在已经结婚，配偶关系稳定。"),
        context,
    )

    assert result.accepted is False
    assert "current_marriage_status_claim" in result.violations


def test_current_marriage_guard_requires_disclaimer_before_qualified_tendency():
    from core.ai_answer_guard import validate_ai_answer

    context = _context().model_copy(
        update={
            "question": "当前婚姻状态",
            "category": "relationship",
        }
    )
    accepted = validate_ai_answer(
        _answer(
            "单凭八字，不能确认现实中的婚姻登记状态。"
            "但如果一定要根据命盘作倾向判断：更偏向已经结婚，"
            "或者至少曾有过一段接近婚姻的长期正式关系。"
        ),
        context,
    )
    wrong_order = validate_ai_answer(
        _answer(
            "你现在已经结婚。"
            "但单凭八字，不能确认现实中的婚姻登记状态。"
        ),
        context,
    )

    assert accepted.accepted is True
    assert wrong_order.accepted is False
    assert "current_marriage_status_claim" in wrong_order.violations


@pytest.mark.parametrize(
    "claim",
    [
        "你的婚姻状态为已婚。",
        "你属于已婚人士。",
        "你现在有配偶。",
        "你仍处于婚姻关系中。",
        "可能需要核验，但你现在已经结婚。",
    ],
)
def test_current_marriage_guard_rejects_synonym_and_distant_hedge_bypasses(
    claim,
):
    from core.ai_answer_guard import validate_ai_answer

    context = _context().model_copy(
        update={
            "question": "我目前的婚姻状况如何？",
            "category": "relationship",
        }
    )
    result = validate_ai_answer(
        _answer(
            "单凭八字，不能确认现实中的婚姻登记状态。" + claim
        ),
        context,
    )

    assert result.accepted is False
    assert "current_marriage_status_claim" in result.violations


@pytest.mark.parametrize(
    "claim",
    [
        "虽然不能确认但你属于已婚人士。",
        "无法判断，不过你的婚姻状态为已婚。",
        "不能认定，却可以确定你现在有配偶。",
    ],
)
def test_current_marriage_guard_rejects_limitation_and_fact_in_same_clause(
    claim,
):
    from core.ai_answer_guard import validate_ai_answer

    context = _context().model_copy(
        update={
            "question": "我目前的婚姻状况如何？",
            "category": "relationship",
        }
    )
    result = validate_ai_answer(
        _answer(
            "单凭八字，不能确认现实中的婚姻登记状态。" + claim
        ),
        context,
    )

    assert result.accepted is False
    assert "current_marriage_status_claim" in result.violations


def test_validate_ai_text_reuses_fact_checks_for_a_single_natural_segment():
    from core.ai_answer_guard import validate_ai_text

    result = validate_ai_text(
        "命局身弱，2026年流年柱为甲子，年干十神为正官。",
        _context(),
    )

    assert result.accepted is False
    assert {
        "strength_contradiction",
        "timing_fact_contradiction",
        "ten_god_contradiction",
    } <= set(result.violations)


def test_validate_ai_answer_keeps_structured_evidence_checks_after_extraction():
    from core.ai_answer_guard import validate_ai_answer

    result = validate_ai_answer(
        _answer("财务建议需谨慎。", ["命局财务需谨慎"]),
        _context(),
    )

    assert result.accepted is False
    assert "unmapped_chart_evidence" in result.violations
