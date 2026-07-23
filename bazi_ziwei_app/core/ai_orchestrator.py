"""AI Q&A orchestration with one corrective retry and local fallback."""

from __future__ import annotations

from typing import Literal, Mapping, Sequence, cast

from core.ai_answer_format import render_structured_answer, render_structured_markdown
from core.ai_answer_guard import validate_ai_answer
from core.ai_context import build_ai_context
from core.ai_models import (
    AIConfig,
    AIRequestContext,
    AnswerResult,
    BaziAIAnswer,
    ChatMessage,
    DegradationReason,
)
from core.chart_facts import chart_facts_from_chart
from core.local_bazi_answer import build_local_answer
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


def _local_result(
    context: AIRequestContext,
    degraded_reason: DegradationReason,
) -> AnswerResult:
    return _answer_result(
        build_local_answer(context),
        source="local_rules",
        degraded_reason=degraded_reason,
    )


_SERVICE_DEGRADATION_REASONS = frozenset(
    {
        "insufficient_quota",
        "invalid_credentials",
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
        "unparseable_response",
    }
)


def _degradation_reason(code: str) -> DegradationReason:
    if code in _SERVICE_DEGRADATION_REASONS:
        return cast(DegradationReason, code)
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
        return _local_result(context, "missing_api_key")
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
            return _local_result(context, _degradation_reason(exc.code))
        except Exception:
            return _local_result(context, "service_unavailable")
        guard = validate_ai_answer(answer, context)
        if guard.accepted:
            return _answer_result(
                answer,
                source="cloud_validated",
            )
        last_violations = guard.violations
    return _local_result(context, "local_validation_failed")
