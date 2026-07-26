from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.ai_answer_format import render_structured_answer, render_structured_markdown
from core.ai_models import AnswerResult, BaziAIAnswer


def _adaptive_answer_data() -> dict[str, object]:
    return {
        "analysis_conclusion": (
            "这个命盘的财务重点是先确认承载能力。\n\n"
            "建议先验证现金流，再决定投入规模。"
        ),
        "chart_evidence": ["日主为乙，强弱结论为身弱。"],
        "rule_evidence": ["承财能力需结合日主强弱。"],
        "timing_conditions": [],
        "practical_advice": ["先验证现金流。"],
        "uncertainty_limitations": [],
    }


def _answer() -> BaziAIAnswer:
    return BaziAIAnswer.model_validate(_adaptive_answer_data())


def test_answer_keeps_one_natural_main_response_without_fixed_six_titles():
    from core.ai_answer_format import render_adaptive_markdown

    answer = _answer()
    rendered = render_adaptive_markdown(answer)

    assert rendered == answer.analysis_conclusion
    for title in (
        "### 分析结论",
        "### 命盘依据",
        "### 规则依据",
        "### 阶段与触发条件",
        "### 现实建议",
        "### 不确定性与限制",
    ):
        assert title not in rendered


def test_machine_support_lists_may_be_empty_but_main_answer_may_not():
    answer = _answer()
    assert answer.timing_conditions == []
    assert answer.uncertainty_limitations == []

    with pytest.raises(ValidationError):
        BaziAIAnswer.model_validate(
            {**_adaptive_answer_data(), "analysis_conclusion": "  "}
        )


def test_structured_rendering_is_an_empty_compatibility_hook():
    answer = _answer()

    assert render_structured_answer(answer) == {}
    assert render_structured_markdown(answer) == answer.analysis_conclusion


def test_answer_result_carries_machine_support_and_degradation_metadata():
    answer = _answer()
    result = AnswerResult(
        answer=answer.analysis_conclusion,
        sections={},
        chart_evidence=tuple(answer.chart_evidence),
        rule_evidence=tuple(answer.rule_evidence),
        timing_conditions=tuple(answer.timing_conditions),
        practical_advice=tuple(answer.practical_advice),
        uncertainty=tuple(answer.uncertainty_limitations),
        source="local_rules",
        degraded_reason="missing_api_key",
    )

    assert result.sections == {}
    assert result.practical_advice
    assert result.degraded_reason == "missing_api_key"
