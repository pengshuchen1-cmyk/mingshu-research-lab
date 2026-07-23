"""Deterministic presentation helpers for structured Bazi answers."""

from __future__ import annotations

from core.ai_models import BaziAIAnswer


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_structured_answer(answer: BaziAIAnswer) -> dict[str, str]:
    return {
        "分析结论": answer.analysis_conclusion,
        "命盘依据": _bullet_list(answer.chart_evidence),
        "规则依据": _bullet_list(answer.rule_evidence),
        "阶段与触发条件": _bullet_list(answer.timing_conditions),
        "现实建议": _bullet_list(answer.practical_advice),
        "不确定性与限制": _bullet_list(answer.uncertainty_limitations),
    }


def render_structured_markdown(answer: BaziAIAnswer) -> str:
    sections = render_structured_answer(answer)
    return "\n\n".join(f"### {title}\n{content}" for title, content in sections.items())
