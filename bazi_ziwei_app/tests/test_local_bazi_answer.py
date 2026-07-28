from __future__ import annotations

import pytest


def _context(
    category: str,
    question: str,
    *,
    requires_timing: bool = False,
):
    from core.ai_models import AIRequestContext

    return AIRequestContext(
        question=question,
        category=category,
        requires_timing=requires_timing,
        chart_facts={
            "pillars": ["甲戌", "癸酉", "壬子", "己酉"],
            "gender": "male",
            "day_master": "壬",
            "hidden_stems": {
                "year": ["戊", "辛", "丁"],
                "month": ["辛"],
                "day": ["癸"],
                "hour": ["辛"],
            },
            "ten_gods": {
                "year": {"gan": "食神"},
                "month": {"gan": "劫财"},
                "day": {"gan": "比肩"},
                "hour": {"gan": "正官"},
            },
            "element_counts": {"木": 1.0, "火": 0.3, "土": 2.0, "金": 4.5, "水": 3.0},
            "strength": {
                "classification": "身强",
                "evidence": ["月令主气生日主。"],
                "favorable_elements": ["木", "火", "土"],
                "unfavorable_elements": ["金", "水"],
            },
            "pattern": {
                "classification": "正印格",
                "evidence": ["月令酉以辛为主气，对日主为正印。"],
            },
            "wealth": {
                "summary": "技能与服务输出可作为收入路径，但项目规模需匹配承载能力。",
                "evidence": [
                    "财星可见不等同现实资产数额。",
                    "承接项目规模要与现金流能力匹配。",
                ],
            },
            "relationship": {
                "summary": "关系倾向需要分吸引、建立和稳定阶段观察。",
                "evidence": ["桃花不等同关系已经建立。"],
                "stability_signals": [
                    {
                        "polarity": "mixed",
                        "fact": "夫妻宫稳定条件信号混合。",
                        "explanation": "不能据此认定现实关系状态。",
                    }
                ],
            },
            "dayun": {
                "direction": "测试顺排",
                "start": "测试起运事实",
            },
            "current_context": {
                "year": 2026,
                "year_pillar": "丙午",
                "month_pillar": "乙未",
                "day_pillar": "己亥",
            },
            "target_years": [{"year": 2027, "year_pillar": "丁未"}],
        },
        rule_evidence=[
            {
                "id": "DOMAIN-RULE",
                "statement": f"{category}类别只依据已提供的本地规则判断。",
            },
            {
                "id": "SAFETY-NONDETERMINISTIC",
                "statement": "命理结论表达为结构倾向、触发条件和行动建议，不作结果保证。",
            },
        ],
        history=[],
    )


@pytest.mark.parametrize(
    ("category", "question", "requires_timing"),
    [
        ("overview", "请概括命盘", False),
        ("wealth", "财运如何？", False),
        ("career", "事业如何发展？", False),
        ("relationship", "姻缘如何？", False),
        ("family", "家庭关系如何？", False),
        ("timing", "2027年什么时候需要注意？", True),
    ],
)
def test_local_answer_is_detailed_but_not_a_fixed_six_section_template(
    category,
    question,
    requires_timing,
):
    from core.local_bazi_answer import build_local_answer

    context = _context(category, question, requires_timing=requires_timing)
    answer = build_local_answer(context)

    assert len(answer.analysis_conclusion) > 80
    assert "主要依据" in answer.analysis_conclusion
    assert "现实建议" in answer.analysis_conclusion
    assert "规则依据" not in answer.analysis_conclusion
    assert "不确定性与限制" not in answer.analysis_conclusion
    assert answer.rule_evidence[0] == (
        f"{category}类别只依据已提供的本地规则判断。"
    )


def test_overview_cites_supplied_pillars_day_master_strength_and_pattern():
    from core.local_bazi_answer import build_local_answer

    answer = build_local_answer(_context("overview", "请概括命盘"))
    combined = "。".join([answer.analysis_conclusion, *answer.chart_evidence])

    assert "甲戌、癸酉、壬子、己酉" in combined
    assert "壬日主" in combined
    assert "身强" in combined
    assert "正印格" in combined


def test_wealth_answer_uses_supplied_summary_and_wealth_evidence():
    from core.local_bazi_answer import build_local_answer

    context = _context("wealth", "财运如何？")
    answer = build_local_answer(context)
    wealth = context.chart_facts["wealth"]

    assert wealth["summary"] in answer.analysis_conclusion
    assert set(wealth["evidence"]) <= set(answer.chart_evidence)


def test_relationship_status_answer_does_not_invent_current_marital_status():
    from core.local_bazi_answer import build_local_answer

    context = _context("relationship", "现在是否已经结婚；当前婚姻状态")
    answer = build_local_answer(context)
    relationship_summary = context.chart_facts["relationship"]["summary"]
    timing = "。".join(answer.timing_conditions)
    limitations = "。".join(answer.uncertainty_limitations)

    assert "单凭八字，不能确认现实中的婚姻登记状态。" in answer.analysis_conclusion
    assert "但如果一定要根据命盘作倾向判断：" in answer.analysis_conclusion
    assert "我更偏向" in answer.analysis_conclusion
    assert relationship_summary in answer.analysis_conclusion
    assert "仍需以本人现实情况为准" in answer.analysis_conclusion
    assert "关系状态的倾向判断" in timing
    assert "不代表确定已婚或未婚" in limitations
    assert "一定会" not in answer.analysis_conclusion
    assert "注定" not in answer.analysis_conclusion


@pytest.mark.parametrize(
    ("signals", "summary", "expected_tendency"),
    [
        (
            [
                {
                    "polarity": "support",
                    "fact": "结构化支持信号。",
                    "explanation": "此项明确记录为支持。",
                }
            ],
            "自由文本声称夫妻宫受冲、关系反复。",
            (
                "更偏向已经结婚，或者至少曾有过一段接近婚姻的长期正式关系；"
                "不像是到现在完全没有过稳定姻缘"
            ),
        ),
        (
            [
                {
                    "polarity": "pressure",
                    "fact": "结构化压力信号。",
                    "explanation": "此项明确记录为压力。",
                }
            ],
            "自由文本声称夫妻宫稳定、配偶星有力。",
            "更偏向目前未必处于稳定婚姻中，或曾有关系但经历明显波折",
        ),
        (
            [
                {
                    "polarity": "mixed",
                    "fact": "结构化混合信号。",
                    "explanation": "支持与压力不能单向归类。",
                }
            ],
            "自由文本声称夫妻宫稳定、关系稳定信号明确。",
            (
                "更偏向认为“关系机会存在”不等于“已经形成稳定婚姻”，"
                "现有中性信号不足以让某一现实状态显著更可能"
            ),
        ),
        (
            [],
            "未见明显波折。",
            (
                "更偏向认为“关系机会存在”不等于“已经形成稳定婚姻”，"
                "现有中性信号不足以让某一现实状态显著更可能"
            ),
        ),
        (
            [],
            "配偶星有力不足。",
            (
                "更偏向认为“关系机会存在”不等于“已经形成稳定婚姻”，"
                "现有中性信号不足以让某一现实状态显著更可能"
            ),
        ),
    ],
)
def test_current_marriage_tendency_uses_only_structured_polarity(
    signals,
    summary,
    expected_tendency,
):
    from core.local_bazi_answer import build_local_answer

    context = _context("relationship", "当前婚姻状态")
    facts = dict(context.chart_facts)
    facts["relationship"] = {
        "summary": summary,
        "evidence": ["引用这条已提供的描述性事实。"],
        "stability_signals": signals,
    }
    supplied_context = context.model_copy(update={"chart_facts": facts})

    answer = build_local_answer(supplied_context)

    assert answer.analysis_conclusion.startswith(
        "单凭八字，不能确认现实中的婚姻登记状态。"
    )
    assert expected_tendency in answer.analysis_conclusion
    assert summary in answer.analysis_conclusion
    assert "仍需以本人现实情况为准。" in answer.analysis_conclusion
    for deterministic in ("一定会", "注定", "百分之百", "必然离婚", "保证成功"):
        assert deterministic not in answer.analysis_conclusion


def test_mortgage_answer_gives_cash_flow_and_downside_advice_without_guarantee():
    from core.local_bazi_answer import build_local_answer

    answer = build_local_answer(
        _context("wealth", "想抵押房子借贷创业，现金流要注意什么？")
    )
    advice = "。".join(answer.practical_advice)
    combined = "。".join(
        [
            answer.analysis_conclusion,
            *answer.timing_conditions,
            *answer.practical_advice,
            *answer.uncertainty_limitations,
        ]
    )

    assert "现金流" in advice
    assert any(term in advice for term in ("最坏情景", "下行", "可承受损失"))
    assert any(term in advice for term in ("还款", "退出"))
    assert "一定能" not in combined
    assert "保证成功" not in combined


def test_timing_answer_uses_only_supplied_dayun_current_and_target_year_facts():
    from core.local_bazi_answer import build_local_answer

    answer = build_local_answer(
        _context("timing", "2027年什么时候需要注意？", requires_timing=True)
    )
    timing = "。".join(answer.timing_conditions)

    for supplied in ("测试顺排", "测试起运事实", "2026年", "丙午", "2027年", "丁未"):
        assert supplied in timing
    for not_supplied in ("2028年", "戊申", "具体月份一定"):
        assert not_supplied not in timing


@pytest.mark.parametrize(
    "term",
    ["房贷", "按揭", "借钱", "负债", "融资", "抵押", "借贷", "贷款", "杠杆"],
)
def test_all_borrowing_terms_trigger_complete_downside_advice(term):
    from core.local_bazi_answer import build_local_answer

    answer = build_local_answer(_context("wealth", f"{term}要注意什么？"))
    advice = "。".join(answer.practical_advice)
    combined = "。".join(
        [
            answer.analysis_conclusion,
            *answer.practical_advice,
            *answer.uncertainty_limitations,
        ]
    )

    for required in ("现金流", "最坏情景", "还款", "退出"):
        assert required in advice
    assert "一定能" not in combined
    assert "保证成功" not in combined


@pytest.mark.parametrize(
    ("domain", "field", "category"),
    [
        ("wealth", "summary", "wealth"),
        ("strength", "classification", "overview"),
        ("pattern", "classification", "career"),
        ("relationship", "summary", "relationship"),
    ],
)
def test_long_supplied_fact_still_builds_bounded_complete_answer(
    domain,
    field,
    category,
):
    from core.local_bazi_answer import build_local_answer

    context = _context(category, "请分析")
    facts = dict(context.chart_facts)
    section = dict(facts[domain])
    useful_prefix = f"保留-{domain}-"
    section[field] = useful_prefix + ("长" * 3200)
    facts[domain] = section
    long_context = context.model_copy(update={"chart_facts": facts})

    answer = build_local_answer(long_context)
    strings = [
        answer.analysis_conclusion,
        *answer.chart_evidence,
        *answer.rule_evidence,
        *answer.timing_conditions,
        *answer.practical_advice,
        *answer.uncertainty_limitations,
    ]

    assert useful_prefix in answer.analysis_conclusion
    assert 0 < len(answer.analysis_conclusion) <= 6000
    assert all(0 < len(value) <= 3000 for value in strings[1:])


def test_long_facts_keep_required_advice_and_limitations_in_adaptive_answer():
    from core.local_bazi_answer import build_local_answer

    context = _context("wealth", "想抵押房子借贷创业，现金流要注意什么？")
    facts = dict(context.chart_facts)
    facts["wealth"] = {
        **facts["wealth"],
        "summary": "保留-wealth-" + ("长" * 3200),
    }
    facts["strength"] = {
        **facts["strength"],
        "classification": "保留-strength-" + ("长" * 3200),
    }
    facts["pattern"] = {
        **facts["pattern"],
        "classification": "保留-pattern-" + ("长" * 3200),
    }

    answer = build_local_answer(context.model_copy(update={"chart_facts": facts}))

    assert len(answer.analysis_conclusion) <= 6000
    assert "**现实建议**" in answer.analysis_conclusion
    assert "**需要说明**" in answer.analysis_conclusion
    assert "现金流" in answer.analysis_conclusion
    assert "借贷、抵押、投资或创业结果" in answer.analysis_conclusion


def test_timing_fallback_exposes_supplied_dayun_period_facts():
    from core.local_bazi_answer import build_local_answer

    context = _context(
        "wealth",
        "这个八字在几年后开始走正财大运",
        requires_timing=True,
    )
    context = context.model_copy(
        update={
            "chart_facts": {
                **context.chart_facts,
                "dayun_periods": [
                    {
                        "pillar": "辛未",
                        "start_age": 1,
                        "end_age": 10,
                        "start_year": 2000,
                        "end_year": 2009,
                        "ten_god": "七杀",
                    },
                    {
                        "pillar": "庚午",
                        "start_age": 11,
                        "end_age": 20,
                        "start_year": 2010,
                        "end_year": 2019,
                        "ten_god": "正官",
                    },
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
                    }
                ],
            }
        }
    )

    answer = build_local_answer(context)

    assert "2030—2039年" in answer.analysis_conclusion
    assert "戊辰" in answer.analysis_conclusion
    assert "正财" in answer.analysis_conclusion
    assert "31—40岁" in answer.analysis_conclusion
