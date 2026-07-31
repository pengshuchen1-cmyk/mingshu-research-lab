from __future__ import annotations

import inspect

import pytest


def _context(*, question: str = "财运如何？", category: str = "wealth"):
    from core.ai_intent import is_current_marriage_question
    from core.ai_models import AIRequestContext

    return AIRequestContext(
        question=question,
        category=category,
        requires_timing=True,
        chart_facts={
            "pillars": ["甲戌", "癸酉", "壬子", "己酉"],
            "gender": "male",
            "day_master": "壬",
            "strength": {
                "classification": "身强",
                "favorable_elements": ["木", "火", "土"],
                "unfavorable_elements": ["金", "水"],
            },
            "pattern": {"classification": "正印格"},
            "element_counts": {
                "木": 1.0,
                "火": 0.3,
                "土": 2.0,
                "金": 4.5,
                "水": 3.0,
            },
            "ten_gods": {
                "year": {
                    "gan": "食神",
                    "hidden_stems": [{"gan": "戊", "ten_god": "七杀"}],
                },
                "month": {
                    "gan": "劫财",
                    "hidden_stems": [{"gan": "辛", "ten_god": "正印"}],
                },
                "day": {
                    "gan": "比肩",
                    "hidden_stems": [{"gan": "癸", "ten_god": "劫财"}],
                },
                "hour": {
                    "gan": "正官",
                    "hidden_stems": [{"gan": "辛", "ten_god": "正印"}],
                },
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
            "current_context": {
                "year": 2026,
                "year_pillar": "丙午",
            },
        },
        rule_evidence=[
            {
                "id": "SAFETY-NONDETERMINISTIC",
                "statement": "命理倾向不保证现实结果",
            }
        ],
        history=[],
        current_marriage_status_requested=is_current_marriage_question(question),
    )


def _plan(
    claim_ids: tuple[str, ...] = (
        "wealth.core",
        "wealth.timing",
        "wealth.action",
    ),
    *,
    domain: str = "wealth",
):
    from core.ai_models import AnalysisPlan, ClaimPlan, ResolvedQuestion

    resolved = ResolvedQuestion(
        safe_question="当前问题",
        domain=domain,
        requested_depth="topic",
    )
    claims = [
        ClaimPlan(
            id=claim_id,
            topic=f"主题{index}",
            allowed_conclusion=f"允许结论{index}",
            local_text=f"本地结论{index}（{claim_id}）",
            fact_ids=["chart.pillars"],
            rule_ids=["SAFETY-NONDETERMINISTIC"],
        )
        for index, claim_id in enumerate(claim_ids)
    ]
    return AnalysisPlan(resolved=resolved, claims=claims)


def _generation(segments):
    from core.ai_models import CloudBaziAnalysis, CloudGeneration

    return CloudGeneration(
        analysis=CloudBaziAnalysis(segments=segments),
        input_tokens=17,
        output_tokens=23,
    )


def test_one_bad_segment_is_replaced_without_losing_good_segment():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core", "wealth.timing"))
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[0].id],
                "text": "壬日主身强，财务宜控制现金流。",
            },
            {
                "claim_ids": [plan.claims[1].id],
                "text": "壬日主身强，你必定发财。",
            },
        ]
    )

    result = validate_and_repair_segments(generation, plan, _context())

    assert result.full_fallback is False
    assert "壬日主身强，财务宜控制现金流。" in result.answer_text
    assert plan.claims[1].local_text in result.answer_text
    assert "你必定发财" not in result.answer_text
    assert result.violation_codes == ("GUARD_SCOPE_EXPANSION",)
    assert result.replaced_claim_ids == (plan.claims[1].id,)
    assert generation.input_tokens == 17
    assert generation.output_tokens == 23


def test_unknown_claim_id_forces_full_fallback_without_partial_text():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core",))
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[0].id, "unknown.claim"],
                "text": "这段原本可以保留。",
            }
        ]
    )

    result = validate_and_repair_segments(generation, plan, _context())

    assert result.full_fallback is True
    assert result.answer_text == ""
    assert result.violation_codes == ("CLOUD_STRUCTURE_INVALID",)
    assert result.replaced_claim_ids == ()


def test_duplicate_claims_are_deduplicated_and_omissions_use_plan_order():
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan()
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[1].id],
                "text": "云端第二项事实正确。",
            },
            {
                "claim_ids": [plan.claims[1].id],
                "text": "不应重复出现的云端第二项。",
            },
            {
                "claim_ids": [plan.claims[0].id],
                "text": "这项必定成功。",
            },
        ]
    )

    result = validate_and_repair_segments(generation, plan, _context())

    paragraphs = result.answer_text.split("\n\n")
    assert paragraphs == [
        plan.claims[0].local_text,
        "云端第二项事实正确。",
        plan.claims[2].local_text,
    ]
    assert "不应重复出现" not in result.answer_text
    assert result.replaced_claim_ids == (
        plan.claims[0].id,
        plan.claims[2].id,
    )


def test_current_marriage_second_segment_does_not_repeat_disclaimer():
    from core.ai_intent import CURRENT_MARRIAGE_DISCLAIMER
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(
        ("relationship.core", "relationship.action"),
        domain="relationship",
    )
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[0].id],
                "text": (
                    CURRENT_MARRIAGE_DISCLAIMER
                    + "这里只说明关系判断必须回到现实核验。"
                ),
            },
            {
                "claim_ids": [plan.claims[1].id],
                "text": "第二段只讨论互动质量、边界和承诺落实。",
            },
        ]
    )
    context = _context(
        question="我目前的婚姻状况如何？",
        category="relationship",
    )

    result = validate_and_repair_segments(generation, plan, context)

    assert result.full_fallback is False
    assert result.replaced_claim_ids == ()
    assert "第二段只讨论互动质量、边界和承诺落实。" in result.answer_text


def test_current_marriage_disclaimer_follows_plan_order_not_cloud_order():
    from core.ai_intent import CURRENT_MARRIAGE_DISCLAIMER
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(
        ("relationship.core", "relationship.action"),
        domain="relationship",
    )
    generation = _generation(
        [
            {
                "claim_ids": [plan.claims[1].id],
                "text": "行动段只讨论互动质量和现实边界。",
            },
            {
                "claim_ids": [plan.claims[0].id],
                "text": "核心段只讨论关系倾向和核验条件。",
            },
        ]
    )
    context = _context(
        question="我目前的婚姻状况如何？",
        category="relationship",
    )

    result = validate_and_repair_segments(generation, plan, context)

    assert result.answer_text.startswith(CURRENT_MARRIAGE_DISCLAIMER)
    assert result.answer_text.count(CURRENT_MARRIAGE_DISCLAIMER) == 1
    assert result.replaced_claim_ids == ()
    assert result.answer_text.index("核心段") < result.answer_text.index("行动段")


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("2026年流年柱为甲子。", "GUARD_YEAR_CONFLICT"),
        ("大运方向为逆排。", "GUARD_DAYUN_CONFLICT"),
        ("命局身弱。", "GUARD_STRENGTH_CONFLICT"),
        ("命局为七杀格。", "GUARD_PATTERN_CONFLICT"),
        ("年干十神为正官。", "GUARD_TEN_GOD_CONFLICT"),
    ],
)
def test_fact_conflicts_have_stable_codes(text, expected_code):
    from core.ai_segment_guard import validate_and_repair_segments

    plan = _plan(("wealth.core",))
    result = validate_and_repair_segments(
        _generation([{"claim_ids": [plan.claims[0].id], "text": text}]),
        plan,
        _context(),
    )

    assert result.full_fallback is False
    assert expected_code in result.violation_codes
    assert result.answer_text == plan.claims[0].local_text


def test_segment_guard_has_no_provider_or_retry_callback():
    from core.ai_segment_guard import validate_and_repair_segments

    parameters = inspect.signature(validate_and_repair_segments).parameters

    assert "provider" not in parameters
    assert "retry" not in parameters
