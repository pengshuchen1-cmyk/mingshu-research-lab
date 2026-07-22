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


def test_timing_context_contains_concrete_current_and_dayun_facts():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    context = build_ai_context(
        build_chart_facts(
            build_bazi_chart(
                {"gender": "女", "birth_date": "1996-09-04", "birth_hour": 23, "birth_minute": 45}
            )
        ),
        "2026年需要注意什么？",
        [],
    )

    assert context.chart_facts["dayun"]["direction"] in {"forward", "reverse", "顺排", "逆排"}
    assert context.chart_facts["dayun"]["start"] != "待计算"
    assert context.chart_facts["current_context"]["year_pillar"]
    assert context.chart_facts["target_years"] == [
        {"year": 2026, "year_pillar": "丙午"}
    ]


def test_timing_context_ignores_birth_year_and_caps_target_years():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    context = build_ai_context(
        build_chart_facts(
            build_bazi_chart(
                {"gender": "女", "birth_date": "1996-09-04", "birth_hour": 23, "birth_minute": 45}
            )
        ),
        "我是1996年出生，想看2026年、2027年、2028年、2029年和2030年的财运",
        [],
    )

    assert [item["year"] for item in context.chart_facts["target_years"]] == [
        2026, 2027, 2028, 2029
    ]
