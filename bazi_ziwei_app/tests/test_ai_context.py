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


def test_context_always_includes_full_normative_chart_domains():
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

    expected = {
        "pillars",
        "gender",
        "day_master",
        "hidden_stems",
        "ten_gods",
        "element_counts",
        "strength",
        "pattern",
        "wealth",
        "relationship",
        "dayun",
    }
    assert expected <= wealth.chart_facts.keys()
    assert expected <= relationship.chart_facts.keys()
    assert "internal_rule_version" not in wealth.chart_facts
    assert "internal_rule_version" not in relationship.chart_facts


def test_specific_question_survives_privacy_redaction():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1996-09-04",
                "birth_hour": 23,
                "birth_minute": 45,
            }
        )
    )
    context = build_ai_context(
        facts,
        "姓名：金丝雀，生日1996-09-04 23:45，我想在2026年抵押房子做AI创业，现金流要注意什么？",
        [],
    )

    assert "金丝雀" not in context.question
    assert "1996-09-04" not in context.question
    assert "23:45" not in context.question
    for useful in ("2026年", "抵押房子", "AI创业", "现金流"):
        assert useful in context.question


def test_recent_follow_up_keeps_deidentified_semantics():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1996-09-04",
                "birth_hour": 23,
                "birth_minute": 45,
            }
        )
    )
    context = build_ai_context(
        facts,
        "那姻缘方面呢？",
        [
            {"role": "user", "content": "我更关心2027年的事业转换"},
            {"role": "assistant", "content": "前一轮讨论了事业转换的条件和现金流。"},
        ],
    )

    assert "2027年的事业转换" in context.history[0].content
    assert "现金流" in context.history[1].content


def test_current_marriage_status_wording_survives_safe_projection():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1996-09-04",
                "birth_hour": 23,
                "birth_minute": 45,
            }
        )
    )
    context = build_ai_context(facts, "请判断她现在是否已经结婚。", [])

    assert "现在是否已经结婚" in context.question
    assert "当前婚姻状态" in context.question


@pytest.mark.parametrize(
    ("question", "safe_phrase"),
    [
        ("她目前结婚了吗？", "目前结婚了吗"),
        ("现在已婚吗？", "现在已婚吗"),
        ("当前未婚，想问姻缘", "当前未婚"),
    ],
)
def test_current_marriage_status_variants_keep_safe_intent(question, safe_phrase):
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1996-09-04",
                "birth_hour": 23,
                "birth_minute": 45,
            }
        )
    )
    context = build_ai_context(facts, question, [])

    assert "她" not in context.question
    assert safe_phrase in context.question
    assert "当前婚姻状态" in context.question
    assert context.category == "relationship"


@pytest.mark.parametrize(
    ("question", "normalized"),
    [
        ("想看2026年 3月的AI创业现金流", "2026年3月"),
        ("想看2026年三月的AI创业现金流", "2026年3月"),
        ("想看明年三月的AI创业现金流", "明年3月"),
    ],
)
def test_forecast_month_variants_are_normalized(question, normalized):
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "女",
                "birth_date": "1996-09-04",
                "birth_hour": 23,
                "birth_minute": 45,
            }
        )
    )
    context = build_ai_context(facts, question, [])

    assert normalized in context.question
    if normalized.startswith("2026年"):
        assert context.chart_facts["target_years"] == [
            {"year": 2026, "year_pillar": "丙午"}
        ]


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
