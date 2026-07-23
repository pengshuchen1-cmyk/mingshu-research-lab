from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.ai_answer_format import render_structured_answer, render_structured_markdown
from core.ai_models import AnswerResult, BaziAIAnswer


def _valid_answer_data() -> dict[str, object]:
    return {
        "analysis_conclusion": "财务发展应先看承载能力。",
        "chart_evidence": ["日主为乙，强弱结论为身弱。"],
        "rule_evidence": ["承财能力需结合日主强弱。"],
        "timing_conditions": ["遇到支持日主的阶段再观察机会。"],
        "practical_advice": ["先验证现金流，避免高杠杆。"],
        "uncertainty_limitations": ["命理趋势不能保证现实收益。"],
    }


def _answer() -> BaziAIAnswer:
    return BaziAIAnswer.model_validate(_valid_answer_data())


def test_structured_answer_always_renders_six_sections_in_fixed_order():
    rendered = render_structured_answer(_answer())

    assert list(rendered) == [
        "分析结论",
        "命盘依据",
        "规则依据",
        "阶段与触发条件",
        "现实建议",
        "不确定性与限制",
    ]
    assert rendered == {
        "分析结论": "财务发展应先看承载能力。",
        "命盘依据": "- 日主为乙，强弱结论为身弱。",
        "规则依据": "- 承财能力需结合日主强弱。",
        "阶段与触发条件": "- 遇到支持日主的阶段再观察机会。",
        "现实建议": "- 先验证现金流，避免高杠杆。",
        "不确定性与限制": "- 命理趋势不能保证现实收益。",
    }
    assert all(rendered.values())


def test_structured_markdown_uses_the_same_six_titles_and_content():
    assert render_structured_markdown(_answer()) == (
        "### 分析结论\n财务发展应先看承载能力。\n\n"
        "### 命盘依据\n- 日主为乙，强弱结论为身弱。\n\n"
        "### 规则依据\n- 承财能力需结合日主强弱。\n\n"
        "### 阶段与触发条件\n- 遇到支持日主的阶段再观察机会。\n\n"
        "### 现实建议\n- 先验证现金流，避免高杠杆。\n\n"
        "### 不确定性与限制\n- 命理趋势不能保证现实收益。"
    )


@pytest.mark.parametrize(
    ("field", "empty_value"),
    [
        ("analysis_conclusion", "  "),
        ("chart_evidence", []),
        ("rule_evidence", []),
        ("timing_conditions", []),
        ("practical_advice", []),
        ("uncertainty_limitations", []),
    ],
)
def test_cloud_answer_requires_all_six_non_empty_sections(field, empty_value):
    data = _valid_answer_data()
    data[field] = empty_value

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate(data)


def test_cloud_answer_rejects_the_legacy_answer_shape():
    legacy = {
        "answer": "旧回答",
        "chart_evidence": ["日主为乙"],
        "rule_evidence": ["先看日主强弱"],
        "uncertainty": ["结果取决于现实选择"],
        "cautions": ["避免高杠杆"],
    }

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate(legacy)


def test_answer_result_carries_the_same_sections_and_degradation_metadata():
    sections = render_structured_answer(_answer())

    result = AnswerResult(
        answer=render_structured_markdown(_answer()),
        sections=sections,
        chart_evidence=("日主为乙，强弱结论为身弱。",),
        rule_evidence=("承财能力需结合日主强弱。",),
        timing_conditions=("遇到支持日主的阶段再观察机会。",),
        practical_advice=("先验证现金流，避免高杠杆。",),
        uncertainty=("命理趋势不能保证现实收益。",),
        source="local_rules",
        degraded_reason="missing_api_key",
    )

    assert result.sections == sections
    assert result.timing_conditions
    assert result.practical_advice
    assert result.degraded_reason == "missing_api_key"
