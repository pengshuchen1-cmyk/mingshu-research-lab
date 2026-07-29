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


def _timing_fact_ids(plan):
    ordered = []
    for claim in plan.claims:
        for fact_id in claim.fact_ids:
            if fact_id.startswith(("dayun.", "year.", "month.", "age.")):
                if fact_id not in ordered:
                    ordered.append(fact_id)
    return ordered


def test_timing_claims_follow_real_dates_and_months_are_numeric():
    from core.ai_analysis_plan import build_analysis_plan

    packet = _fact_packet("明年逐月财运如何")
    shuffled = packet.model_copy(update={"facts": list(reversed(packet.facts))})

    plan = build_analysis_plan(shuffled)

    assert _timing_fact_ids(plan) == [
        "dayun.3",
        "year.2027",
        *(f"month.2027.{month}" for month in range(1, 13)),
    ]


def test_age_fact_is_ordered_by_its_real_date_after_covering_dayun():
    from core.ai_analysis_plan import build_analysis_plan

    packet = _fact_packet("30周岁财运如何")
    shuffled = packet.model_copy(update={"facts": list(reversed(packet.facts))})

    plan = build_analysis_plan(shuffled)
    timing_ids = _timing_fact_ids(plan)

    assert timing_ids[0].startswith("dayun.")
    assert timing_ids[-1] == "age.solar_age.30"


def test_explicit_dayun_topic_keeps_dayun_claims():
    from core.ai_analysis_plan import build_analysis_plan

    plan = build_analysis_plan(_fact_packet("请详细分析大运"))

    assert any(
        claim.topic == "大运阶段"
        and any(fact_id.startswith("dayun.") for fact_id in claim.fact_ids)
        and any(rule_id.startswith("DAYUN-") for rule_id in claim.rule_ids)
        for claim in plan.claims
    )


def test_sixty_year_plan_preserves_all_requested_and_covering_timing_facts():
    from core.ai_analysis_plan import build_analysis_plan

    packet = _fact_packet("2020到2079年财运")
    expected_ids = {
        fact.id
        for fact in packet.facts
        if fact.kind in {"year", "dayun"}
    }

    plan = build_analysis_plan(packet)
    planned_ids = {
        fact_id
        for claim in plan.claims
        for fact_id in claim.fact_ids
    }

    assert expected_ids <= planned_ids
    assert len(plan.claims) <= 60
    assert all(len(claim.fact_ids) <= 24 for claim in plan.claims)


def test_plan_capacity_error_is_stable_instead_of_dropping_facts():
    from core.ai_analysis_plan import AnalysisPlanError, build_analysis_plan
    from core.ai_models import FactItem, FactPacket, ResolvedQuestion

    resolved = ResolvedQuestion(
        safe_question="2020到2079年财运",
        domain="wealth",
        time_scope="year_range",
        target_years=list(range(2020, 2080)),
        requested_depth="long_range",
    )
    facts = [
        FactItem(
            id="chart.wealth",
            kind="chart",
            text="财富领域事实。",
            source="chart",
        ),
        *[
            FactItem(
                id=f"year.{year}",
                kind="year",
                text=f"{year}年" + ("长" * 490),
                source="year",
            )
            for year in range(2020, 2080)
        ],
        *[
            FactItem(
                id=f"dayun.{index}",
                kind="dayun",
                text=f"第{index}步大运" + ("长" * 485),
                source="dayun",
            )
            for index in range(1, 180)
        ],
    ]
    packet = FactPacket(
        resolved=resolved,
        facts=facts,
        rule_evidence=[
            {"id": "WEALTH-CAPACITY", "statement": "财富领域规则。"},
            {"id": "SAFETY-NONDETERMINISTIC", "statement": "安全规则。"},
        ],
    )

    with pytest.raises(AnalysisPlanError) as caught:
        build_analysis_plan(packet)

    assert caught.value.code == "PLAN_CAPACITY_EXCEEDED"
    assert str(caught.value).startswith("PLAN_CAPACITY_EXCEEDED:")


def test_missing_domain_fact_fails_without_cross_domain_fallback():
    from core.ai_analysis_plan import AnalysisPlanError, build_analysis_plan

    packet = _fact_packet("财运如何？")
    missing = packet.model_copy(
        update={"facts": [fact for fact in packet.facts if fact.id != "chart.wealth"]}
    )

    with pytest.raises(AnalysisPlanError) as caught:
        build_analysis_plan(missing)

    assert caught.value.code == "PLAN_DOMAIN_FACTS_MISSING"


def test_missing_domain_rule_fails_without_cross_domain_fallback():
    from core.ai_analysis_plan import AnalysisPlanError, build_analysis_plan

    packet = _fact_packet("财运如何？")
    missing = packet.model_copy(
        update={
            "rule_evidence": [
                rule
                for rule in packet.rule_evidence
                if not rule["id"].startswith("WEALTH-")
            ]
        }
    )

    with pytest.raises(AnalysisPlanError) as caught:
        build_analysis_plan(missing)

    assert caught.value.code == "PLAN_DOMAIN_RULES_MISSING"


def test_missing_requested_year_fact_fails_explicitly():
    from core.ai_analysis_plan import AnalysisPlanError, build_analysis_plan

    packet = _fact_packet("明年财运如何")
    missing = packet.model_copy(
        update={"facts": [fact for fact in packet.facts if fact.id != "year.2027"]}
    )

    with pytest.raises(AnalysisPlanError) as caught:
        build_analysis_plan(missing)

    assert caught.value.code == "PLAN_TIMING_FACTS_MISSING"
