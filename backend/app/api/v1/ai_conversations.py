"""Persistent, privacy-preserving AI consultation endpoints."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from time import perf_counter
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from ...ai.ai_conversation_store import (
    NEW_CONVERSATION_TITLE,
    TurnStartError,
    TurnState,
    as_utc,
    completed_history_before,
    fail_turn,
    list_conversation_messages,
    list_owned_conversations,
    owned_conversation,
    start_turn,
)
from ...ai.ai_models import DEFAULT_KIMI_MODEL, AIConfig, AnswerResult
from ...ai.ai_orchestrator import answer_question
from ...chart_domain import owned_profile_chart, profile_payload
from ...config import settings
from ...database import DBSession
from ...domain_schemas import (
    AIConversationCreateIn,
    AIConversationListOut,
    AIConversationOut,
    AIConversationUpdateIn,
    AIMessageCreateIn,
    AIMessageCreateOut,
    AIMessageListOut,
)
from ...errors import APIError, Errors
from ...models import AIAnswerRun, AIConversation, AIMessage
from ...security import CurrentUser

router = APIRouter(prefix="/ai-conversations", tags=["ai-consultation"])
BOUNDARY_NOTE = "命理分析仅供传统文化参考，不替代医疗、法律、投资或其他现实专业决策。"


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


def _conversation_payload(conversation: AIConversation) -> dict:
    return {
        "id": conversation.id,
        "profile_id": conversation.profile_id,
        "title": conversation.title,
        "status": conversation.status,
        "message_count": conversation.message_count,
        "last_message_at": as_utc(conversation.last_message_at),
        "created_at": as_utc(conversation.created_at),
        "updated_at": as_utc(conversation.updated_at),
    }


def _message_payload(message: AIMessage) -> dict:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sequence_no": message.sequence_no,
        "role": message.role,
        "content": message.content,
        "status": message.status,
        "structured_content": message.structured_content,
        "created_at": as_utc(message.created_at),
    }


def _structured_answer(result: AnswerResult) -> dict:
    return {
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
    }


def _turn_response(state: TurnState, *, replayed: bool) -> dict:
    structured = state.assistant_message.structured_content or {}
    return {
        "conversation_id": state.conversation.id,
        "user_message_id": state.user_message.id,
        "assistant_message_id": state.assistant_message.id,
        "profile_id": state.conversation.profile_id,
        "chart_fingerprint": state.run.chart_fingerprint,
        "mode": "cloud" if state.run.source == "cloud_validated" else "local",
        "answer": state.assistant_message.content or "",
        "structured_answer": structured,
        "degradation_reason": state.run.degradation_reason,
        "boundary_note": BOUNDARY_NOTE,
        "idempotent_replay": replayed,
    }


async def _has_pending_run(db: DBSession, conversation_id: str) -> bool:
    return (
        await db.execute(
            select(AIAnswerRun.id).where(
                AIAnswerRun.conversation_id == conversation_id,
                AIAnswerRun.status == "pending",
            ).limit(1)
        )
    ).scalar_one_or_none() is not None


@router.post("", response_model=AIConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: AIConversationCreateIn,
    user: CurrentUser,
    db: DBSession,
):
    """创建一个绑定当前用户命理档案的持久化 AI 会话。"""
    await owned_profile_chart(db, body.profile_id, user.id)
    now = datetime.now(UTC)
    conversation = AIConversation(
        user_id=user.id,
        profile_id=body.profile_id,
        title=body.title or NEW_CONVERSATION_TITLE,
        status="active",
        message_count=0,
        last_message_at=now,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return _conversation_payload(conversation)


@router.get("", response_model=AIConversationListOut)
async def list_conversations(
    user: CurrentUser,
    db: DBSession,
    profile_id: str | None = None,
    conversation_status: Annotated[
        Literal["active", "archived"] | None,
        Query(alias="status"),
    ] = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """按最后消息时间倒序查询当前用户的 AI 会话。"""
    items, next_cursor = await list_owned_conversations(
        db,
        user.id,
        profile_id=profile_id,
        status=conversation_status,
        cursor=cursor,
        limit=limit,
    )
    return {
        "items": [_conversation_payload(item) for item in items],
        "next_cursor": next_cursor,
    }


@router.get("/{conversation_id}", response_model=AIConversationOut)
async def get_conversation(conversation_id: str, user: CurrentUser, db: DBSession):
    """查询当前用户的一条 AI 会话详情。"""
    conversation = await owned_conversation(db, conversation_id, user.id)
    return _conversation_payload(conversation)


@router.patch("/{conversation_id}", response_model=AIConversationOut)
async def update_conversation(
    conversation_id: str,
    body: AIConversationUpdateIn,
    user: CurrentUser,
    db: DBSession,
):
    """修改会话标题，或在 active 和 archived 状态之间切换。"""
    conversation = await owned_conversation(
        db,
        conversation_id,
        user.id,
        for_update=True,
    )
    if (
        body.status == "archived"
        and conversation.status != "archived"
        and await _has_pending_run(db, conversation.id)
    ):
        raise APIError(Errors.AI_CONVERSATION_BUSY)
    if body.title is not None:
        conversation.title = body.title
    if body.status is not None:
        conversation.status = body.status
    conversation.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(conversation)
    return _conversation_payload(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser,
    db: DBSession,
):
    """软删除当前用户的一条会话；生成中的会话不能删除。"""
    conversation = await owned_conversation(
        db,
        conversation_id,
        user.id,
        for_update=True,
    )
    if await _has_pending_run(db, conversation.id):
        raise APIError(Errors.AI_CONVERSATION_BUSY)
    now = datetime.now(UTC)
    conversation.status = "deleted"
    conversation.deleted_at = now
    conversation.updated_at = now
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{conversation_id}/messages", response_model=AIMessageListOut)
async def get_messages(
    conversation_id: str,
    user: CurrentUser,
    db: DBSession,
    before_sequence: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
):
    """按会话内顺序查询消息；通过 before_sequence 向前翻页。"""
    conversation = await owned_conversation(db, conversation_id, user.id)
    items, next_before = await list_conversation_messages(
        db,
        conversation.id,
        before_sequence=before_sequence,
        limit=limit,
    )
    return {
        "items": [_message_payload(item) for item in items],
        "next_before_sequence": next_before,
    }


@router.post("/{conversation_id}/messages", response_model=AIMessageCreateOut)
async def send_message(
    conversation_id: str,
    body: AIMessageCreateIn,
    user: CurrentUser,
    db: DBSession,
):
    """保存用户问题，从服务端历史构建上下文，并持久化最终回答。"""
    conversation = await owned_conversation(db, conversation_id, user.id)
    profile, stored_chart = await owned_profile_chart(db, conversation.profile_id, user.id)
    config = _ai_config()
    try:
        state = await start_turn(
            db,
            conversation_id=conversation.id,
            user_id=user.id,
            question=body.question,
            idempotency_key=body.idempotency_key,
            chart_fingerprint=stored_chart.chart_fingerprint,
            provider=config.provider if config.provider in {"kimi", "openai"} else None,
            model=config.model if config.provider in {"kimi", "openai"} else None,
            timeout_seconds=config.timeout_seconds,
        )
    except TurnStartError as exc:
        if exc.commit_repairs:
            await db.commit()
        else:
            await db.rollback()
        raise APIError(exc.error) from None
    await db.commit()
    if state.replayed:
        return _turn_response(state, replayed=True)

    history = await completed_history_before(
        db,
        conversation.id,
        state.user_message.sequence_no,
    )
    chart = deepcopy(stored_chart.chart_json)
    safe_profile = profile_payload(profile)
    safe_profile.pop("id", None)
    safe_profile.pop("name", None)
    safe_profile.pop("birth_place", None)
    chart["profile"] = safe_profile
    started = perf_counter()
    try:
        result = await run_in_threadpool(
            answer_question,
            chart,
            body.question,
            history,
            config=config,
            session_id=f"user:{user.id}",
            request_id=state.run.id,
        )
    except Exception:  # noqa: BLE001 - persist a failed turn without exposing internals.
        await fail_turn(db, state, Errors.AI_QUESTION_UNAVAILABLE.code)
        await db.commit()
        raise APIError(Errors.AI_QUESTION_UNAVAILABLE) from None

    completed_at = datetime.now(UTC)
    structured_answer = _structured_answer(result)
    state.assistant_message.content = result.answer
    state.assistant_message.status = "completed"
    state.assistant_message.structured_content = structured_answer
    state.run.status = "completed"
    state.run.source = result.source
    state.run.degradation_reason = result.degraded_reason
    state.run.input_tokens = result.input_tokens
    state.run.output_tokens = result.output_tokens
    state.run.latency_ms = max(0, int((perf_counter() - started) * 1000))
    state.run.violation_codes = list(result.violation_codes)
    state.run.interpretation_receipt = result.interpretation_receipt
    state.run.completed_at = completed_at
    state.conversation.last_message_at = completed_at
    state.conversation.updated_at = completed_at
    await db.commit()
    return _turn_response(state, replayed=False)
