from __future__ import annotations

from datetime import datetime

import pytest


NOW = datetime(2026, 7, 28)


def _fact_packet(question: str = "明年财运如何"):
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    return compile_fact_packet(
        synthetic_chart(),
        resolve_question(question, now=NOW),
    )


def test_analysis_plan_claims_are_fully_grounded():
    from core.ai_analysis_plan import build_analysis_plan

    fact_packet = _fact_packet()
    plan = build_analysis_plan(fact_packet)
    fact_ids = {item.id for item in fact_packet.facts}
    rule_ids = {item["id"] for item in fact_packet.rule_evidence}

    assert plan.claims
    for claim in plan.claims:
        assert set(claim.fact_ids) <= fact_ids
        assert set(claim.rule_ids) <= rule_ids
        assert claim.local_text


@pytest.mark.parametrize(
    ("question", "expected_depth", "minimum_claims"),
    [
        ("事业如何？", "direct", 1),
        ("明年财运如何", "single_year", 2),
        (
            "请详细分析事业发展路径、现实条件、行动建议、风险边界和长期规划",
            "topic",
            3,
        ),
        ("未来五年财运如何", "long_range", 5),
        ("明年逐月财运如何", "monthly", 12),
    ],
)
def test_requested_depth_controls_plan_detail(
    question,
    expected_depth,
    minimum_claims,
):
    from core.ai_analysis_plan import build_analysis_plan

    plan = build_analysis_plan(_fact_packet(question))

    assert plan.resolved.requested_depth == expected_depth
    assert len(plan.claims) >= minimum_claims


def test_deeper_request_produces_more_claims_and_local_text():
    from core.ai_analysis_plan import build_analysis_plan

    direct = build_analysis_plan(_fact_packet("事业如何？"))
    topic = build_analysis_plan(
        _fact_packet(
            "请详细分析事业发展路径、现实条件、行动建议、风险边界和长期规划"
        )
    )

    assert len(topic.claims) > len(direct.claims)
    assert sum(len(claim.local_text) for claim in topic.claims) > sum(
        len(claim.local_text) for claim in direct.claims
    )


def test_relationship_plan_uses_relationship_rules():
    from core.ai_analysis_plan import build_analysis_plan

    plan = build_analysis_plan(_fact_packet("婚姻如何？"))

    assert all(
        any(rule_id.startswith("REL-") for rule_id in claim.rule_ids)
        for claim in plan.claims
    )


@pytest.mark.parametrize(
    ("question", "domain"),
    [
        ("事业如何发展？", "career"),
        ("家庭关系如何？", "family"),
        ("健康如何？", "health_advisory"),
        ("子女如何？", "children"),
        ("学业如何？", "education"),
        ("是否适合搬家？", "relocation"),
        ("买房置业如何？", "property"),
        ("有贵人吗？", "benefactor"),
    ],
)
def test_extended_domain_claims_use_domain_facts_rules_and_limits(
    question,
    domain,
):
    from core.ai_analysis_plan import build_analysis_plan

    packet = _fact_packet(question)
    plan = build_analysis_plan(packet)
    domain_fact_ids = {
        fact.id for fact in packet.facts if fact.id.startswith(f"domain.{domain}.")
    }
    general_rule_ids = {
        "SAFETY-NONDETERMINISTIC",
        "SAFETY-STATUS-UNKNOWN",
    }
    domain_rule_ids = {
        rule["id"] for rule in packet.rule_evidence
    } - general_rule_ids

    assert domain_fact_ids
    assert any(set(claim.fact_ids) & domain_fact_ids for claim in plan.claims)
    assert any(set(claim.rule_ids) & domain_rule_ids for claim in plan.claims)
    assert all(claim.conditions for claim in plan.claims)
    assert all(claim.uncertainty for claim in plan.claims)
    assert all("不得保证结果" in claim.prohibited_expansion for claim in plan.claims)
