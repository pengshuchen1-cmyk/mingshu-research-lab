"""AI Q&A orchestration with one corrective retry and local fallback."""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from core.ai_answer_format import render_structured_answer, render_structured_markdown
from core.ai_answer_guard import validate_ai_answer
from core.ai_context import build_ai_context
from core.ai_models import (
    AIConfig,
    AnswerResult,
    BaziAIAnswer,
    ChatMessage,
    DegradationReason,
)
from core.chart_facts import chart_facts_from_chart
from services.openai_bazi_client import AIServiceError, OpenAIBaziClient


def _answer_result(
    answer: BaziAIAnswer,
    *,
    source: Literal["cloud_validated", "local_rules"],
    degraded_reason: DegradationReason | None = None,
) -> AnswerResult:
    return AnswerResult(
        answer=render_structured_markdown(answer),
        sections=render_structured_answer(answer),
        chart_evidence=tuple(answer.chart_evidence),
        rule_evidence=tuple(answer.rule_evidence),
        timing_conditions=tuple(answer.timing_conditions),
        practical_advice=tuple(answer.practical_advice),
        uncertainty=tuple(answer.uncertainty_limitations),
        source=source,
        degraded_reason=degraded_reason,
    )


def _local_fallback(
    facts,
    question: str,
    category: str,
    degraded_reason: DegradationReason,
) -> AnswerResult:
    if category == "wealth":
        answer = facts.wealth
        evidence = facts.wealth_evidence
    elif category == "relationship":
        if any(word in question for word in ("现在", "是否", "已婚", "结婚了吗")):
            answer = "出生盘不能确认当前是否已婚；只能分析关系倾向、触发条件与时机。" + facts.relationship
        else:
            answer = facts.relationship
        evidence = facts.relationship_evidence
    elif category == "career":
        answer = f"事业结构先看格局与承载：{facts.pattern} {facts.wealth}"
        evidence = facts.pattern_evidence + facts.wealth_evidence
    elif category == "timing":
        answer = f"起运方向为{facts.dayun_direction}；{facts.dayun_start}。具体年份仍需结合流年事实。"
        evidence = (facts.pillar_basis,)
    elif category == "family":
        answer = "命盘可观察家庭互动倾向，但不能代替真实家庭经历。" + facts.relationship
        evidence = facts.relationship_evidence
    else:
        answer = f"日主强弱为{facts.strength}。格局：{facts.pattern}"
        evidence = facts.strength_evidence + facts.pattern_evidence
    structured = BaziAIAnswer(
        analysis_conclusion=answer or "本地规则事实暂不足，请补充更具体的问题。",
        chart_evidence=tuple(evidence) or (facts.pillar_basis,),
        rule_evidence=["回答来自项目本地四柱规则。"],
        timing_conditions=["阶段判断需结合大运、流年事实与现实环境持续验证。"],
        practical_advice=["先把命盘趋势与现实信息逐项核对，再决定行动。"],
        uncertainty_limitations=[
            "命理分析用于趋势观察，现实结果取决于环境与选择；"
            "不替代财务、医疗、法律或其他专业决策。"
        ],
    )
    return _answer_result(
        structured,
        source="local_rules",
        degraded_reason=degraded_reason,
    )


def _degradation_reason(code: str) -> DegradationReason:
    if code == "timeout":
        return "timeout"
    if code == "unparseable_response":
        return "unparseable_response"
    return "service_unavailable"


def answer_question(
    chart: dict,
    question: str,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    config: AIConfig | None = None,
    client: object | None = None,
) -> AnswerResult:
    config = config or AIConfig.from_environment()
    facts = chart_facts_from_chart(chart)
    context = build_ai_context(facts, question, history)
    if not config.enabled:
        return _local_fallback(
            facts,
            question,
            context.category,
            "missing_api_key",
        )
    service = client or OpenAIBaziClient(config)

    last_violations: tuple[str, ...] = ()
    for attempt in range(2):
        request_context = context
        if attempt and last_violations:
            correction = "纠正要求：修正以下校验问题：" + "、".join(last_violations)
            corrected_question = f"{context.question}\n{correction}"[-500:]
            request_context = context.model_copy(update={"question": corrected_question})
        try:
            answer = service.answer(request_context)
        except AIServiceError as exc:
            if exc.code == "unparseable_response" and attempt == 0:
                last_violations = ("malformed_structured_output",)
                continue
            return _local_fallback(
                facts,
                question,
                context.category,
                _degradation_reason(exc.code),
            )
        except Exception:
            return _local_fallback(
                facts,
                question,
                context.category,
                "service_unavailable",
            )
        guard = validate_ai_answer(answer, context)
        if guard.accepted:
            return _answer_result(
                answer,
                source="cloud_validated",
            )
        last_violations = guard.violations
    return _local_fallback(
        facts,
        question,
        context.category,
        "local_validation_failed",
    )
