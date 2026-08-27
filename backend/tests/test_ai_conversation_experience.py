from app.ai.ai_analysis_plan import build_analysis_plan
from app.ai.ai_models import (
    AIConfig,
    AIRequestContext,
    AnalysisPlan,
    ClaimPlan,
    FactItem,
    FactPacket,
    ResolvedQuestion,
)
from app.ai.ai_request_control import AIRequestController
from app.ai.local_bazi_answer import render_local_plan
from app.ai.providers.bazi_ai_prompt import build_messages


def _prompt_context() -> AIRequestContext:
    resolved = ResolvedQuestion(
        safe_question="命盘整体特点是什么？",
        domain="overview",
    )
    fact = FactItem(
        id="chart.day_master",
        kind="day_master",
        text="日主为甲木",
        source="chart",
    )
    packet = FactPacket(
        resolved=resolved,
        facts=[fact],
        rule_evidence=[{"id": "rule.overview", "statement": "依据日主分析"}],
    )
    plan = AnalysisPlan(
        resolved=resolved,
        claims=[
            ClaimPlan(
                id="claim.overview",
                topic="整体特点",
                allowed_conclusion="结合甲木说明整体特点",
                local_text="本地规则回答",
                fact_ids=[fact.id],
                rule_ids=["rule.overview"],
            )
        ],
    )
    return AIRequestContext(
        question=resolved.safe_question,
        category="overview",
        requires_timing=False,
        chart_facts={"day_master": "甲"},
        rule_evidence=packet.rule_evidence,
        resolved_question=resolved,
        fact_packet=packet,
        analysis_plan=plan,
    )


def test_default_ai_limit_allows_a_normal_ten_question_burst():
    controller = AIRequestController()

    for index in range(10):
        request_id = f"request-{index}"
        decision = controller.preflight("same-user", request_id)
        assert decision.allowed is True
        controller.release(request_id)

    blocked = controller.preflight("same-user", "request-10")
    assert blocked.allowed is False
    assert blocked.reason == "rate_limited"
    assert AIConfig(api_key="", enabled=False).per_session_per_minute == 10


def test_cloud_prompt_requests_plain_spoken_chinese_and_shorter_answers():
    system_prompt = build_messages(_prompt_context())[0]["content"]

    assert "像一位懂八字的朋友当面解释" in system_prompt
    assert "优先使用短句和日常用词" in system_prompt
    assert "不要直接复述 FactPacket" in system_prompt
    assert "150—350" in system_prompt


def test_local_wealth_fallback_uses_plain_language_in_ai_chat():
    resolved = ResolvedQuestion(
        safe_question="我的财运怎么样？",
        domain="wealth",
    )
    packet = FactPacket(
        resolved=resolved,
        facts=[
            FactItem(
                id="domain.wealth.summary",
                kind="wealth",
                text="财星有出现，但仍要结合收入和支出判断。",
                source="domain",
            )
        ],
        rule_evidence=[
            {
                "id": "WEALTH-REVENUE-RETENTION",
                "statement": "财运需同时观察机会和留存。",
            },
            {"id": "SAFETY-NONDETERMINISTIC", "statement": "不得保证结果。"},
        ],
    )

    plan = build_analysis_plan(packet)
    answer = plan.claims[0].local_text

    assert "赚到的钱能不能留下来" in answer
    assert "具体看这点" in answer
    assert "财务承载" not in answer
    assert "命盘事实：" not in answer

    rendered = render_local_plan(plan)
    assert "本地规则依据" not in rendered.analysis_conclusion
    assert "为什么这么说" not in rendered.analysis_conclusion
    assert rendered.rule_evidence
