from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("question", "category", "timing"),
    [
        ("这个八字财运怎么样？", "wealth", False),
        ("2027年什么时候适合赚钱？", "wealth", True),
        ("事业适合做AI吗？", "career", False),
        ("今年桃花姻缘如何？", "relationship", True),
        ("原生家庭和父母关系怎么样？", "family", False),
        ("请概括整个命盘", "overview", False),
        ("请解释一下", "other", False),
    ],
)
def test_question_router_is_deterministic(question, category, timing):
    from core.ai_context import classify_question

    routed = classify_question(question)

    assert routed.category == category
    assert routed.requires_timing is timing


def test_domain_context_only_includes_relevant_analysis():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1986-08-15",
                "birth_hour": 10,
                "birth_minute": 0,
            }
        )
    )
    wealth = build_ai_context(facts, "财运怎么发展？", [])
    relationship = build_ai_context(facts, "姻缘怎么样？", [])

    assert "wealth" in wealth.chart_facts
    assert "relationship" not in wealth.chart_facts
    assert "relationship" in relationship.chart_facts
    assert "wealth" not in relationship.chart_facts
