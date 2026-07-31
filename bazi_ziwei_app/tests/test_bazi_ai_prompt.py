from __future__ import annotations

import json

import pytest


def _context(requested_depth):
    from core.ai_models import (
        AIRequestContext,
        AnalysisPlan,
        ChatMessage,
        ClaimPlan,
        FactItem,
        FactPacket,
        ResolvedQuestion,
    )

    resolved = ResolvedQuestion(
        safe_question="请依据本地材料分析财运。",
        domain="wealth",
        requested_depth=requested_depth,
    )
    fact_packet = FactPacket(
        resolved=resolved,
        facts=[
            FactItem(
                id="chart.wealth",
                kind="chart",
                text="财务判断要结合承载能力。",
                source="chart",
            )
        ],
        rule_evidence=[
            {"id": "WEALTH-CAPACITY", "statement": "承财看日主能力。"}
        ],
    )
    analysis_plan = AnalysisPlan(
        resolved=resolved,
        claims=[
            ClaimPlan(
                id="wealth.core",
                topic="财务承载",
                allowed_conclusion="财务主题应同时观察机会与承载能力。",
                local_text="财务主题应同时观察机会与承载能力。",
                fact_ids=["chart.wealth"],
                rule_ids=["WEALTH-CAPACITY"],
                conditions=["结合现实现金流核对。"],
                uncertainty=["不保证具体财务结果。"],
                prohibited_expansion=["不得保证结果"],
            )
        ],
    )
    return AIRequestContext(
        question="LEGACY-QUESTION-SENTINEL",
        category="wealth",
        requires_timing=False,
        chart_facts={"legacy": "LEGACY-CHART-SENTINEL"},
        rule_evidence=[
            {"id": "LEGACY-RULE", "statement": "LEGACY-RULE-SENTINEL"}
        ],
        history=[
            ChatMessage(role="user", content="LEGACY-HISTORY-SENTINEL")
        ],
        resolved_question=resolved,
        fact_packet=fact_packet,
        analysis_plan=analysis_plan,
    )


@pytest.mark.parametrize(
    ("requested_depth", "target"),
    [
        ("direct", "300—700"),
        ("single_year", "700—1200"),
        ("topic", "1200—2200"),
        ("long_range", "2200—4000"),
        ("monthly", "2200—4000"),
    ],
)
def test_prompt_uses_requested_depth_target(requested_depth, target):
    from services.bazi_ai_prompt import build_messages

    system_prompt = build_messages(_context(requested_depth))[0]["content"]

    assert requested_depth in system_prompt
    assert target in system_prompt
    assert "800—1500" not in system_prompt
    assert "单点至少 800 字" not in system_prompt
    assert "只返回 analysis_conclusion" not in system_prompt


def test_prompt_allows_only_fact_packet_and_analysis_plan():
    from services.bazi_ai_prompt import build_messages

    messages = build_messages(_context("direct"))
    system_prompt = messages[0]["content"]
    payload = json.loads(messages[1]["content"])

    assert set(payload) == {
        "allowed_claim_ids",
        "fact_packet",
        "analysis_plan",
    }
    assert payload["allowed_claim_ids"] == ["wealth.core"]
    assert payload["fact_packet"]["resolved"]["safe_question"] == (
        "请依据本地材料分析财运。"
    )
    assert payload["analysis_plan"]["claims"][0]["id"] == "wealth.core"
    serialized = messages[1]["content"]
    for forbidden in (
        "LEGACY-QUESTION-SENTINEL",
        "LEGACY-CHART-SENTINEL",
        "LEGACY-RULE-SENTINEL",
        "LEGACY-HISTORY-SENTINEL",
    ):
        assert forbidden not in serialized

    assert "每个段落" in system_prompt
    assert "claim_id" in system_prompt
    assert "必须从 allowed_claim_ids 中原样复制" in system_prompt
    assert "不得翻译、缩写、拼接、改写或创造新编号" in system_prompt
    assert "不得写入 claim 之外" in system_prompt
    assert "不得重新计算四柱" in system_prompt
    assert "不得固定套用六个栏目" in system_prompt


def test_current_marriage_prompt_requires_grounded_disclaimer_first():
    from core.ai_intent import CURRENT_MARRIAGE_DISCLAIMER
    from services.bazi_ai_prompt import build_messages

    base = _context("direct")
    resolved = base.analysis_plan.resolved.model_copy(
        update={
            "safe_question": "她目前的婚姻登记状态如何？",
            "domain": "relationship",
            "current_marriage_status_requested": True,
        }
    )
    claim = base.analysis_plan.claims[0].model_copy(
        update={
            "id": "relationship.core",
            "topic": "关系条件",
            "allowed_conclusion": "只能分析关系倾向，不能确认现实登记状态。",
            "uncertainty": ["现实婚姻登记状态未知。"],
        }
    )
    context = base.model_copy(
        update={
            "category": "relationship",
            "resolved_question": resolved,
            "fact_packet": base.fact_packet.model_copy(
                update={"resolved": resolved}
            ),
            "analysis_plan": base.analysis_plan.model_copy(
                update={"resolved": resolved, "claims": [claim]}
            ),
        }
    )

    system_prompt = build_messages(context)[0]["content"]

    assert CURRENT_MARRIAGE_DISCLAIMER in system_prompt
    assert "必须先以" in system_prompt
    assert "relationship claim" in system_prompt
    payload = json.loads(build_messages(context)[1]["content"])
    assert (
        payload["fact_packet"]["resolved"][
            "current_marriage_status_requested"
        ]
        is True
    )
    assert (
        payload["analysis_plan"]["resolved"][
            "current_marriage_status_requested"
        ]
        is True
    )
    assert CURRENT_MARRIAGE_DISCLAIMER not in (
        build_messages(_context("direct"))[0]["content"]
    )


@pytest.mark.parametrize("missing", ["fact_packet", "analysis_plan"])
def test_prompt_rejects_missing_grounded_context(missing):
    from services.bazi_ai_prompt import build_messages

    context = _context("direct").model_copy(update={missing: None})

    with pytest.raises(ValueError, match="grounded_context_required"):
        build_messages(context)
