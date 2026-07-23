from __future__ import annotations

import pytest


SIX_SECTION_TITLES = [
    "分析结论",
    "命盘依据",
    "规则依据",
    "阶段与触发条件",
    "现实建议",
    "不确定性与限制",
]


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
def test_local_answer_has_six_non_empty_sections(
    category,
    question,
    requires_timing,
):
    from core.ai_answer_format import render_structured_answer
    from core.local_bazi_answer import build_local_answer

    answer = build_local_answer(
        _context(category, question, requires_timing=requires_timing)
    )
    sections = render_structured_answer(answer)

    assert list(sections) == SIX_SECTION_TITLES
    assert all(value.strip() for value in sections.values())
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

    assert "不能确认当前是否已婚" in answer.analysis_conclusion
    assert "倾向" in answer.analysis_conclusion
    assert relationship_summary in answer.analysis_conclusion
    assert "仍需以本人现实情况为准" in answer.analysis_conclusion
    assert "关系状态的倾向判断" in timing
    assert "不代表确定已婚或未婚" in limitations
    assert "已婚" not in answer.analysis_conclusion.replace("不能确认当前是否已婚", "")
    assert "未婚" not in answer.analysis_conclusion


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
    from core.ai_answer_format import render_structured_answer
    from core.local_bazi_answer import build_local_answer

    context = _context(category, "请分析")
    facts = dict(context.chart_facts)
    section = dict(facts[domain])
    useful_prefix = f"保留-{domain}-"
    section[field] = useful_prefix + ("长" * 3200)
    facts[domain] = section
    long_context = context.model_copy(update={"chart_facts": facts})

    answer = build_local_answer(long_context)
    sections = render_structured_answer(answer)
    strings = [
        answer.analysis_conclusion,
        *answer.chart_evidence,
        *answer.rule_evidence,
        *answer.timing_conditions,
        *answer.practical_advice,
        *answer.uncertainty_limitations,
    ]

    assert list(sections) == SIX_SECTION_TITLES
    assert all(sections.values())
    assert useful_prefix in answer.analysis_conclusion
    assert all(0 < len(value) <= 3000 for value in strings)
