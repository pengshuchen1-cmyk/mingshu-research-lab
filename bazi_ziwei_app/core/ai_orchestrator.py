"""Grounded Bazi AI orchestration with at most one cloud generation."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Callable, Literal, Mapping, Sequence, cast
from uuid import uuid4

from core.ai_analysis_plan import build_analysis_plan
from core.ai_answer_format import render_adaptive_markdown
from core.ai_context import (
    _build_resolved_legacy_context,
    build_ai_context,
    build_canonical_chart_facts,
    redact_customer_text,
)
from core.ai_fact_compiler import compile_fact_packet
from core.ai_intent import (
    CURRENT_MARRIAGE_DISCLAIMER,
)
from core.ai_models import (
    AIConfig,
    AIRequestContext,
    AnalysisPlan,
    AnswerResult,
    BaziAIAnswer,
    ChatMessage,
    CloudBaziAnalysis,
    CloudGeneration,
    DegradationReason,
    ProgressStage,
    ResolvedQuestion,
    is_retryable_degradation,
)
from core.ai_question_resolver import resolve_question
from core.ai_request_control import (
    AIRequestController,
    request_controller_for_config,
)
from core.ai_scope_gate import check_bazi_scope
from core.ai_segment_guard import validate_and_repair_segments
from core.chart_facts import chart_facts_from_chart
from core.local_bazi_answer import build_local_answer, render_local_plan
from core.luck_engine import get_luck_cycles
from services.ai_client_factory import build_ai_client
from services.ai_service_errors import AIServiceError
from services.kimi_bazi_client import KIMI_MODEL


_TRADITIONAL_CULTURE_DISCLAIMER = (
    "命理分析仅供传统文化参考，不替代现实中的医疗、法律或财务决策。"
)
_BOUNDARY_MESSAGES = {
    "prompt_injection": "该请求涉及系统或校验规则，超出四柱问答范围。",
    "medical_diagnosis": "四柱问答不能提供医疗诊断或治疗方案。",
    "legal_advice": "四柱问答不能提供法律意见或诉讼策略。",
    "investment_operation": "四柱问答不能代替具体投资买卖决策。",
    "unsupported_system": "当前仅支持四柱八字范围内的问题。",
}
_SERVICE_DEGRADATION_REASONS = frozenset(
    {
        "insufficient_quota",
        "invalid_credentials",
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
        "unparseable_response",
        "daily_budget",
        "duplicate_request",
        "concurrency_limit",
    }
)


class CloudAnswerCapacityError(ValueError):
    """Cloud prose exceeded the bounded customer-facing answer contract."""


def _answer_result(
    answer: BaziAIAnswer,
    *,
    source: Literal["cloud_validated", "local_rules"],
    degraded_reason: DegradationReason | None = None,
    provider: Literal["kimi", "openai"] | None = None,
    interpretation_receipt: str = "",
    retryable: bool = False,
    violation_codes: tuple[str, ...] = (),
    input_tokens: int = 0,
    output_tokens: int = 0,
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
        interpretation_receipt=interpretation_receipt,
        retryable=retryable,
        violation_codes=violation_codes,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _terminal_result(
    answer: str,
    *,
    source: Literal["boundary", "clarification"],
) -> AnswerResult:
    return AnswerResult(
        answer=answer,
        sections={},
        chart_evidence=(),
        rule_evidence=(),
        timing_conditions=(),
        practical_advice=(),
        uncertainty=(),
        source=source,
    )


def _local_result(
    local: BaziAIAnswer,
    resolved: ResolvedQuestion,
    degraded_reason: DegradationReason,
    *,
    retryable: bool | None = None,
    violation_codes: tuple[str, ...] = (),
) -> AnswerResult:
    return _answer_result(
        local,
        source="local_rules",
        degraded_reason=degraded_reason,
        interpretation_receipt=resolved.interpretation_receipt,
        retryable=(
            is_retryable_degradation(degraded_reason)
            if retryable is None
            else retryable
        ),
        violation_codes=violation_codes,
    )


def _degradation_reason(code: str) -> DegradationReason:
    if code in _SERVICE_DEGRADATION_REASONS:
        return cast(DegradationReason, code)
    return "service_unavailable"


def _resolved_dayun_periods(
    chart: dict,
    resolved: ResolvedQuestion,
) -> list[Mapping[str, object]] | None:
    if resolved.time_scope == "none":
        return None
    working_chart = deepcopy(chart)
    luck = get_luck_cycles(
        working_chart.get("profile", {}),
        working_chart,
    )
    raw_periods = luck.get("dayun_list") if luck.get("available") else None
    if not isinstance(raw_periods, list):
        return None
    return [
        period
        for period in raw_periods
        if isinstance(period, Mapping)
    ]


def _legacy_context(
    chart: dict,
    resolved: ResolvedQuestion,
    history: Sequence[ChatMessage | Mapping[str, object]],
) -> AIRequestContext:
    facts = chart_facts_from_chart(chart)
    return _build_resolved_legacy_context(
        facts,
        resolved,
        history,
        dayun_periods=_resolved_dayun_periods(chart, resolved),
    )


def _canonical_guard_chart_facts(
    chart: dict,
    resolved: ResolvedQuestion,
) -> dict[str, object]:
    return build_canonical_chart_facts(
        chart_facts_from_chart(chart),
        requires_timing=resolved.time_scope != "none",
        question=resolved.safe_question,
        target_years=resolved.target_years,
        dayun_periods=_resolved_dayun_periods(chart, resolved),
    )


def _emergency_local_answer(
    chart: dict,
    resolved: ResolvedQuestion,
    history: Sequence[ChatMessage | Mapping[str, object]],
) -> BaziAIAnswer:
    """Keep local failures private and readable without using cloud output."""
    try:
        return build_local_answer(_legacy_context(chart, resolved, history))
    except Exception:
        return BaziAIAnswer(
            analysis_conclusion=(
                "当前命盘事实未能通过本地结构校验，请核对排盘资料后再试。"
                "\n\n"
                + _TRADITIONAL_CULTURE_DISCLAIMER
            ),
            chart_evidence=[],
            rule_evidence=[],
            timing_conditions=[],
            practical_advice=["请先核对出生资料与排盘结果是否完整。"],
            uncertainty_limitations=["本次未形成可供解释的本地事实包。"],
        )


def _complete_local_answer(
    plan: AnalysisPlan,
    chart: dict,
    history: Sequence[ChatMessage | Mapping[str, object]],
) -> BaziAIAnswer:
    local = render_local_plan(plan)
    if (
        plan.resolved.current_marriage_status_requested
        or any(
            marker in plan.resolved.safe_question
            for marker in (
                "房贷",
                "按揭",
                "借钱",
                "负债",
                "融资",
                "抵押",
                "借贷",
                "贷款",
                "杠杆",
            )
        )
    ):
        # Preserve the established customer-facing tendency wording and
        # complete borrowing-risk advice while the grounded plan remains the
        # cloud repair source.
        return _emergency_local_answer(chart, plan.resolved, history)
    return local


def _cloud_answer_text(
    guarded_text: str,
    resolved: ResolvedQuestion,
) -> str:
    text = guarded_text.strip()
    receipt = resolved.interpretation_receipt.strip()
    if (
        receipt
        and receipt not in text
        and resolved.current_marriage_status_requested
        and text.startswith(CURRENT_MARRIAGE_DISCLAIMER)
    ):
        remainder = text[len(CURRENT_MARRIAGE_DISCLAIMER):].lstrip()
        text = "\n\n".join(
            item
            for item in (
                CURRENT_MARRIAGE_DISCLAIMER,
                receipt,
                remainder,
            )
            if item
        )
    elif receipt and receipt not in text:
        text = f"{receipt}\n\n{text}"
    if _TRADITIONAL_CULTURE_DISCLAIMER not in text:
        text = f"{text}\n\n{_TRADITIONAL_CULTURE_DISCLAIMER}"
    if not text or len(text) > 6000:
        raise CloudAnswerCapacityError("cloud_answer_capacity_invalid")
    return text


def answer_question(
    chart: dict,
    question: str,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    previous: ResolvedQuestion | None = None,
    now: datetime | None = None,
    config: AIConfig | None = None,
    client: object | None = None,
    on_progress: Callable[[ProgressStage], None] | None = None,
    request_controller: AIRequestController | None = None,
    session_id: str = "anonymous",
    request_id: str = "",
) -> AnswerResult:
    def emit(stage: ProgressStage) -> None:
        if on_progress is not None:
            on_progress(stage)

    emit("validating_scope")
    scope = check_bazi_scope(question)
    if not scope.allowed:
        emit("rejected")
        return _terminal_result(
            _BOUNDARY_MESSAGES.get(
                scope.reason,
                "该问题超出当前四柱问答范围。",
            ),
            source="boundary",
        )

    emit("resolving_question")
    safe_question = redact_customer_text(question, max_input_chars=2000)
    resolved = resolve_question(
        safe_question,
        now=now or datetime.now(),
        previous=previous,
    )
    if resolved.ambiguity:
        emit("rejected")
        return _terminal_result(
            resolved.ambiguity,
            source="clarification",
        )

    emit("compiling_local_facts")
    try:
        packet = compile_fact_packet(deepcopy(chart), resolved)
        plan = build_analysis_plan(packet)
        local = _complete_local_answer(plan, chart, history)
    except Exception:
        local = _emergency_local_answer(chart, resolved, history)
        emit("degraded")
        return _local_result(
            local,
            resolved,
            "local_validation_failed",
        )

    selected_config = config or AIConfig.from_environment()
    if selected_config.provider not in {"kimi", "openai"}:
        emit("degraded")
        return _local_result(
            local,
            resolved,
            "service_unavailable",
            retryable=False,
        )
    if (
        selected_config.provider == "kimi"
        and selected_config.model != KIMI_MODEL
    ):
        emit("degraded")
        return _local_result(
            local,
            resolved,
            "service_unavailable",
            retryable=False,
        )
    if not selected_config.enabled:
        emit("degraded")
        return _local_result(
            local,
            resolved,
            "missing_api_key",
        )

    try:
        context = build_ai_context(
            packet,
            plan,
            history,
            canonical_chart_facts=_canonical_guard_chart_facts(
                chart,
                resolved,
            ),
        )
    except Exception:
        emit("degraded")
        return _local_result(
            local,
            resolved,
            "local_validation_failed",
        )

    controller = request_controller or request_controller_for_config(
        selected_config,
    )
    control_request_id = request_id or uuid4().hex
    decision = controller.preflight(
        session_id,
        control_request_id,
    )
    if not decision.allowed:
        emit("degraded")
        return _local_result(
            local,
            resolved,
            _degradation_reason(str(decision.reason or "")),
        )

    try:
        try:
            service = client or build_ai_client(selected_config)
        except AIServiceError as exc:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                _degradation_reason(exc.code),
            )
        except Exception:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "service_unavailable",
            )

        emit("generating_cloud_answer")
        try:
            generation = service.answer(context)
        except AIServiceError as exc:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                _degradation_reason(exc.code),
            )
        except Exception:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "service_unavailable",
            )

        if isinstance(generation, CloudGeneration):
            controller.record_usage(
                control_request_id,
                input_tokens=generation.input_tokens,
                output_tokens=generation.output_tokens,
            )

        emit("validating_answer")
        if (
            not isinstance(generation, CloudGeneration)
            or not isinstance(generation.analysis, CloudBaziAnalysis)
            or type(generation.input_tokens) is not int
            or type(generation.output_tokens) is not int
            or generation.input_tokens < 0
            or generation.output_tokens < 0
        ):
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "local_validation_failed",
                violation_codes=("CLOUD_STRUCTURE_INVALID",),
            )

        try:
            guarded = validate_and_repair_segments(generation, plan, context)
        except Exception:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "local_validation_failed",
                violation_codes=("CLOUD_SEGMENT_GUARD_ERROR",),
            )
        if guarded.full_fallback:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "local_validation_failed",
                violation_codes=guarded.violation_codes,
            )

        try:
            cloud_text = _cloud_answer_text(guarded.answer_text, resolved)
        except CloudAnswerCapacityError:
            emit("degraded")
            return _local_result(
                local,
                resolved,
                "local_validation_failed",
                violation_codes=("CLOUD_ANSWER_TOO_LONG",),
            )
        grounded = local.model_copy(
            update={"analysis_conclusion": cloud_text},
        )
        emit("completed")
        return _answer_result(
            grounded,
            source="cloud_validated",
            provider=cast(
                Literal["kimi", "openai"],
                selected_config.provider,
            ),
            interpretation_receipt=resolved.interpretation_receipt,
            violation_codes=guarded.violation_codes,
            input_tokens=generation.input_tokens,
            output_tokens=generation.output_tokens,
        )
    finally:
        controller.release(control_request_id)
