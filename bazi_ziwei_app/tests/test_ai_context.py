from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "text",
    ("那后面呢", "继续说", "刚才第二点再详细说说", "那婚后呢"),
)
def test_privacy_projection_preserves_follow_up_semantics(text):
    from core.ai_context import redact_customer_text

    assert redact_customer_text(text) == text


def test_privacy_projection_removes_identity_but_keeps_question():
    from core.ai_context import redact_customer_text

    value = redact_customer_text(
        "姓名张三，生日1999年8月11日，电话13800138000；明年财运如何"
    )

    assert "张三" not in value
    assert "1999" not in value
    assert "13800138000" not in value
    assert "明年财运如何" in value


@pytest.mark.parametrize("identity", ("张三", "110101199001011234"))
def test_privacy_projection_masks_unlabelled_identity_tokens(identity):
    from core.ai_context import REDACTION_MARKER, redact_customer_text

    assert redact_customer_text(identity) == REDACTION_MARKER

    value = redact_customer_text(f"{identity}；明年财运如何")
    assert identity not in value
    assert "明年财运如何" in value


@pytest.mark.parametrize(
    ("question", "category", "timing"),
    [
        ("这个八字财运怎么样？", "wealth", False),
        ("现金流要注意什么？", "wealth", False),
        ("2027年什么时候适合赚钱？", "wealth", True),
        ("这个八字在几年后开始走财运", "wealth", True),
        ("这个八字在几年后开始走正财大运", "wealth", True),
        ("几岁开始行大运", "timing", True),
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


def test_dayun_finance_question_survives_privacy_projection():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {
                "gender": "男",
                "birth_date": "1999-08-11",
                "birth_hour": 10,
                "birth_minute": 0,
            }
        )
    )
    question = "这个八字在几年后开始走正财大运"

    context = build_ai_context(facts, question, [])

    assert context.question == question
    assert context.category == "wealth"
    assert context.requires_timing is True


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


def test_relationship_context_preserves_canonical_structured_stability_signal():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    chart = build_bazi_chart(
        {
            "gender": "女",
            "birth_date": "1996-09-04",
            "birth_hour": 23,
            "birth_minute": 45,
        }
    )
    context = build_ai_context(
        build_chart_facts(chart),
        "她是否已婚？",
        [],
    )
    expected = [
        {
            "polarity": item["polarity"],
            "fact": item["fact"],
            "explanation": item["explanation"],
        }
        for item in chart["relationship_analysis"]["stability_signals"]
    ]

    assert context.chart_facts["relationship"]["stability_signals"] == expected
    assert "current_context" not in context.chart_facts
    assert "target_years" not in context.chart_facts


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


@pytest.mark.parametrize(
    ("question", "category", "required_phrases"),
    [
        (
            "请分析软件工程师转管理岗后团队冲突和薪资谈判策略",
            "career",
            ("软件工程师", "管理岗", "团队冲突", "薪资谈判策略"),
        ),
        (
            "我打算卖掉基金给孩子付学费，怎样控制风险",
            "wealth",
            ("卖掉基金", "给孩子付学费", "怎样控制风险"),
        ),
    ],
)
def test_unlisted_safe_customer_semantics_are_preserved_and_routed(
    question,
    category,
    required_phrases,
):
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

    assert context.category == category
    for phrase in required_phrases:
        assert phrase in context.question


def test_unlisted_follow_up_semantics_survive_history_projection():
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
        "那这一步为什么要先和主管谈？",
        [
            {
                "role": "user",
                "content": "软件工程师转管理岗后，团队冲突和薪资谈判怎么安排？",
            },
            {
                "role": "assistant",
                "content": "先确认职责范围，再讨论团队授权和薪资结构。",
            },
        ],
    )

    assert "为什么要先和主管谈" in context.question
    assert "软件工程师转管理岗" in context.history[0].content
    assert "团队授权和薪资结构" in context.history[1].content


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
    "question",
    [
        "她是否已婚？",
        "她已婚了吗？",
        "现在是未婚还是已婚？",
    ],
)
def test_additional_current_marriage_variants_project_to_safe_status_intent(question):
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

    assert "当前婚姻状态" in context.question
    assert context.category == "relationship"


@pytest.mark.parametrize(
    "question",
    [
        "我目前的婚姻状况如何？",
        "现在婚姻登记状态是什么？",
        "我如今有配偶吗？",
        "现阶段是否属于已婚人士？",
    ],
)
def test_current_marriage_natural_language_variants_share_canonical_intent(
    question,
):
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

    assert context.category == "relationship"
    assert "当前婚姻状态" in context.question


@pytest.mark.parametrize(
    "term",
    ["房贷", "按揭", "借钱", "负债", "融资"],
)
def test_borrowing_synonyms_survive_projection_and_route_to_wealth(term):
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
    context = build_ai_context(facts, f"{term}要注意什么？", [])

    assert term in context.question
    assert context.category == "wealth"


@pytest.mark.parametrize(
    ("question", "safe_phrase"),
    [
        ("她目前结婚了吗？", "目前结婚了吗"),
        ("现在已婚吗？", "现在已婚吗"),
        ("当前未婚，想问姻缘", "当前未婚"),
        ("目前是否结婚？", "目前是否结婚"),
        ("现在有没有结婚？", "现在有没有结婚"),
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


def test_target_year_facts_delegate_to_canonical_yearly_rule(monkeypatch):
    import core.yearly_engine as yearly_engine
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    calls = []

    def canonical_year_pillar(year):
        calls.append(year)
        return f"规则{year}"

    monkeypatch.setattr(yearly_engine, "get_year_pillar", canonical_year_pillar)
    context = build_ai_context(
        build_chart_facts(
            build_bazi_chart(
                {
                    "gender": "女",
                    "birth_date": "1996-09-04",
                    "birth_hour": 23,
                    "birth_minute": 45,
                }
            )
        ),
        "想看2026年和2027年的财运",
        [],
    )

    assert calls == [2026, 2027]
    assert context.chart_facts["target_years"] == [
        {"year": 2026, "year_pillar": "规则2026"},
        {"year": 2027, "year_pillar": "规则2027"},
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
