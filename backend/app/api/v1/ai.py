"""Privacy-preserving Bazi question-answering endpoint."""

from __future__ import annotations

from copy import deepcopy

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from ...ai.ai_models import DEFAULT_KIMI_MODEL, AIConfig
from ...ai.ai_orchestrator import answer_question
from ...chart_domain import owned_profile_chart, profile_payload
from ...config import settings
from ...database import DBSession
from ...domain_schemas import AIQuestionIn, AIQuestionOut
from ...errors import APIError, Errors
from ...security import CurrentUser

router = APIRouter(prefix="/chart-profiles", tags=["ai-consultation"])


def _ai_config() -> AIConfig:
    provider = settings.ai_provider
    model = settings.ai_model.strip()
    if not model:
        model = DEFAULT_KIMI_MODEL if provider == "kimi" else "gpt-5.6-sol"
    base_url = settings.ai_base_url.strip()
    if not base_url:
        base_url = (
            "https://api.moonshot.cn/v1"
            if provider == "kimi"
            else "https://api.openai.com/v1"
        )
    key = settings.ai_api_key.get_secret_value()
    return AIConfig(
        api_key=key,
        enabled=bool(key) and provider in {"kimi", "openai"},
        model=model,
        reasoning_effort=settings.ai_reasoning_effort,
        kimi_thinking=settings.ai_kimi_thinking,
        timeout_seconds=settings.ai_timeout_seconds,
        provider=provider,
        base_url=base_url,
        per_session_per_minute=settings.ai_per_user_per_minute,
        per_session_daily_requests=settings.ai_per_user_daily_requests,
        daily_token_budget=settings.ai_daily_token_budget,
        max_concurrent_requests=settings.ai_max_concurrent_requests,
    )


@router.post("/{profile_id}/questions", response_model=AIQuestionOut)
async def ask_chart_question(
    profile_id: str,
    body: AIQuestionIn,
    user: CurrentUser,
    db: DBSession,
):
    """用本地事实回答命理问题；配置云模型时仅发送去标识化事实并校验输出。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    chart = deepcopy(stored_chart.chart_json)
    # The timing engine requires confirmed birth inputs, but identity and place
    # are neither needed nor allowed to enter the AI orchestration pipeline.
    safe_profile = profile_payload(profile)
    safe_profile.pop("id", None)
    safe_profile.pop("name", None)
    safe_profile.pop("birth_place", None)
    chart["profile"] = safe_profile
    history = [item.model_dump() for item in body.history]
    try:
        result = await run_in_threadpool(
            answer_question,
            chart,
            body.question,
            history,
            config=_ai_config(),
            session_id=f"user:{user.id}",
        )
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.AI_QUESTION_UNAVAILABLE) from None
    return {
        "profile_id": profile_id,
        "chart_fingerprint": stored_chart.chart_fingerprint,
        "mode": "cloud" if result.source == "cloud_validated" else "local",
        "answer": result.answer,
        "structured_answer": {
            "source": result.source,
            "provider": result.provider,
            "sections": result.sections,
            "chart_evidence": list(result.chart_evidence),
            "rule_evidence": list(result.rule_evidence),
            "timing_conditions": list(result.timing_conditions),
            "practical_advice": list(result.practical_advice),
            "uncertainty": list(result.uncertainty),
            "interpretation_receipt": result.interpretation_receipt,
            "retryable": result.retryable,
            "violation_codes": list(result.violation_codes),
        },
        "degradation_reason": result.degraded_reason,
        "boundary_note": "命理分析仅供传统文化参考，不替代医疗、法律、投资或其他现实专业决策。",
    }
