from __future__ import annotations


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
            "strength": {"classification": "身强", "evidence": ["月令生扶"]},
            "pattern": {"classification": "正印格", "evidence": ["月令主气"]},
            "wealth": {"summary": "重视现金流", "evidence": ["财星可见"]},
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


def test_guard_examines_all_six_answer_sections():
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
