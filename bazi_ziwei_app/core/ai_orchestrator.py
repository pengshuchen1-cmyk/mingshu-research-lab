"""AI Q&A orchestration with one corrective retry and local fallback."""

from __future__ import annotations

from typing import Literal, Mapping, Sequence, cast

from core.ai_answer_format import render_adaptive_markdown
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
from services.ai_client_factory import build_ai_client
from services.ai_service_errors import AIServiceError


def _answer_result(
    answer: BaziAIAnswer,
    *,
    source: Literal["cloud_validated", "local_rules"],
    degraded_reason: DegradationReason | None = None,
    provider: Literal["kimi", "openai"] | None = None,
) -> AnswerResult:
    return AnswerResult(
        answer=render_adaptive_markdown(answer),
        sections={},
        chart_evidence=tuple(answer.chart_evidence),
        rule_evidence=tuple(answer.rule_evidence),
        timing_conditions=tuple(answer.timing_conditions),
        practical_advice=tuple(answer.practical_advice),
        uncertainty=tuple(answer.uncertainty_limitations),
        source=source,
        degraded_reason=degraded_reason,
        provider=provider,
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


def _cloud_prose_candidate(answer: BaziAIAnswer) -> BaziAIAnswer:
    """Keep only cloud prose; machine evidence is never trusted from cloud."""
    return BaziAIAnswer(
        analysis_conclusion=answer.analysis_conclusion,
        chart_evidence=[],
        rule_evidence=[],
        timing_conditions=[],
        practical_advice=[],
        uncertainty_limitations=[],
    )


def _with_local_evidence(
    answer: BaziAIAnswer,
    context: AIRequestContext,
) -> BaziAIAnswer:
    """Attach deterministic local details after cloud prose is validated."""
    local = build_local_answer(context)
    return local.model_copy(
        update={"analysis_conclusion": answer.analysis_conclusion},
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
    if config.provider not in {"kimi", "openai"}:
        return _local_result(context, "service_unavailable")
    if not config.enabled:
        return _local_result(context, "missing_api_key")
    try:
        service = client or build_ai_client(config)
    except AIServiceError as exc:
        return _local_result(context, _degradation_reason(exc.code))
    except Exception:
        return _local_result(context, "service_unavailable")

    try:
        cloud_answer = service.answer(context)
    except AIServiceError as exc:
        return _local_result(context, _degradation_reason(exc.code))
    except Exception:
        return _local_result(context, "service_unavailable")

    candidate = _cloud_prose_candidate(cloud_answer)
    guard = validate_ai_answer(candidate, context)
    if not guard.accepted:
        return _local_result(context, "local_validation_failed")
    grounded = _with_local_evidence(candidate, context)
    return _answer_result(
        grounded,
        source="cloud_validated",
        provider=config.provider,
    )
