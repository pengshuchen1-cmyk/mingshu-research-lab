"""Durable conversation storage and short MySQL transaction helpers."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..errors import APIError, ErrorDefinition, Errors
from ..models import AIAnswerRun, AIConversation, AIMessage

NEW_CONVERSATION_TITLE = "新会话"


def as_utc(value: datetime) -> datetime:
    """Normalize MySQL/SQLite naive datetimes according to the project's UTC convention."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def database_utc(value: datetime) -> datetime:
    """Return a naive UTC value suitable for MySQL DATETIME comparisons."""
    return as_utc(value).replace(tzinfo=None)


def encode_conversation_cursor(conversation: AIConversation) -> str:
    payload = json.dumps(
        {
            "last_message_at": as_utc(conversation.last_message_at).isoformat(),
            "id": conversation.id,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode_conversation_cursor(value: str) -> tuple[datetime, str]:
    try:
        padding = "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(value + padding).decode("utf-8"))
        timestamp = datetime.fromisoformat(str(payload["last_message_at"]))
        conversation_id = str(payload["id"])
        if timestamp.tzinfo is None or len(conversation_id) != 36:
            raise ValueError
        return database_utc(timestamp), conversation_id
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise APIError(Errors.AI_CURSOR_INVALID) from None


async def owned_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
    *,
    for_update: bool = False,
) -> AIConversation:
    query = select(AIConversation).where(
        AIConversation.id == conversation_id,
        AIConversation.user_id == user_id,
        AIConversation.deleted_at.is_(None),
    )
    if for_update:
        query = query.with_for_update()
    conversation = (await db.execute(query)).scalar_one_or_none()
    if conversation is None:
        raise APIError(Errors.AI_CONVERSATION_NOT_FOUND)
    return conversation


async def list_owned_conversations(
    db: AsyncSession,
    user_id: str,
    *,
    profile_id: str | None,
    status: str | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[AIConversation], str | None]:
    query = select(AIConversation).where(
        AIConversation.user_id == user_id,
        AIConversation.deleted_at.is_(None),
    )
    if profile_id is not None:
        query = query.where(AIConversation.profile_id == profile_id)
    if status is not None:
        query = query.where(AIConversation.status == status)
    if cursor is not None:
        cursor_time, cursor_id = decode_conversation_cursor(cursor)
        query = query.where(
            or_(
                AIConversation.last_message_at < cursor_time,
                and_(
                    AIConversation.last_message_at == cursor_time,
                    AIConversation.id < cursor_id,
                ),
            )
        )
    rows = (
        (
            await db.execute(
                query.order_by(
                    AIConversation.last_message_at.desc(),
                    AIConversation.id.desc(),
                ).limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    items = list(rows[:limit])
    next_cursor = encode_conversation_cursor(items[-1]) if has_more and items else None
    return items, next_cursor


async def list_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    *,
    before_sequence: int | None,
    limit: int,
) -> tuple[list[AIMessage], int | None]:
    query = select(AIMessage).where(AIMessage.conversation_id == conversation_id)
    if before_sequence is not None:
        query = query.where(AIMessage.sequence_no < before_sequence)
    rows = (
        (
            await db.execute(
                query.order_by(AIMessage.sequence_no.desc()).limit(limit + 1)
            )
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    page = list(rows[:limit])
    page.reverse()
    next_before = page[0].sequence_no if has_more and page else None
    return page, next_before


async def completed_history_before(
    db: AsyncSession,
    conversation_id: str,
    sequence_no: int,
) -> list[dict[str, str]]:
    """Load only the six most recent completed messages for the existing AI contract."""
    rows = (
        (
            await db.execute(
                select(AIMessage)
                .where(
                    AIMessage.conversation_id == conversation_id,
                    AIMessage.sequence_no < sequence_no,
                    AIMessage.status == "completed",
                    AIMessage.content.is_not(None),
                )
                .order_by(AIMessage.sequence_no.desc())
                .limit(6)
            )
        )
        .scalars()
        .all()
    )
    return [
        {"role": message.role, "content": message.content or ""}
        for message in reversed(rows)
    ]


@dataclass(slots=True)
class TurnState:
    conversation: AIConversation
    run: AIAnswerRun
    user_message: AIMessage
    assistant_message: AIMessage
    replayed: bool = False


class TurnStartError(Exception):
    """Business conflict found after stale pending rows may have been repaired."""

    def __init__(self, error: ErrorDefinition, *, commit_repairs: bool = False):
        self.error = error
        self.commit_repairs = commit_repairs
        super().__init__(error.code)


async def _messages_for_turn(
    db: AsyncSession,
    conversation_id: str,
    turn_id: str,
) -> tuple[AIMessage | None, AIMessage | None]:
    rows = (
        (
            await db.execute(
                select(AIMessage).where(
                    AIMessage.conversation_id == conversation_id,
                    AIMessage.turn_id == turn_id,
                )
            )
        )
        .scalars()
        .all()
    )
    by_role = {message.role: message for message in rows}
    return by_role.get("user"), by_role.get("assistant")


async def start_turn(
    db: AsyncSession,
    *,
    conversation_id: str,
    user_id: str,
    question: str,
    idempotency_key: str,
    chart_fingerprint: str,
    provider: str | None,
    model: str | None,
    timeout_seconds: int,
) -> TurnState:
    """Reserve one ordered turn without holding a transaction during the model call."""
    conversation = await owned_conversation(
        db,
        conversation_id,
        user_id,
        for_update=True,
    )
    if conversation.status != "active":
        raise TurnStartError(Errors.AI_CONVERSATION_NOT_ACTIVE)

    now = datetime.now(UTC)
    stale_before = now - timedelta(seconds=timeout_seconds + 30)
    pending_runs = (
        (
            await db.execute(
                select(AIAnswerRun).where(
                    AIAnswerRun.conversation_id == conversation.id,
                    AIAnswerRun.status == "pending",
                )
            )
        )
        .scalars()
        .all()
    )
    active_pending: list[AIAnswerRun] = []
    repaired_stale = False
    for pending in pending_runs:
        if as_utc(pending.started_at) > stale_before:
            active_pending.append(pending)
            continue
        pending.status = "failed"
        pending.failure_code = "STALE_PENDING_REQUEST"
        pending.completed_at = now
        _, stale_assistant = await _messages_for_turn(db, conversation.id, pending.id)
        if stale_assistant is not None:
            stale_assistant.status = "failed"
        repaired_stale = True

    existing = (
        await db.execute(
            select(AIAnswerRun).where(
                AIAnswerRun.conversation_id == conversation.id,
                AIAnswerRun.idempotency_key == idempotency_key,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing_user, existing_assistant = await _messages_for_turn(
            db,
            conversation.id,
            existing.id,
        )
        if existing_user is None or existing_user.content != question:
            raise TurnStartError(
                Errors.AI_IDEMPOTENCY_KEY_CONFLICT,
                commit_repairs=repaired_stale,
            )
        if (
            existing.status == "completed"
            and existing_assistant is not None
            and existing_assistant.status == "completed"
            and existing_assistant.content is not None
        ):
            return TurnState(
                conversation,
                existing,
                existing_user,
                existing_assistant,
                replayed=True,
            )
        if existing.status == "pending":
            raise TurnStartError(
                Errors.AI_CONVERSATION_BUSY,
                commit_repairs=repaired_stale,
            )
        raise TurnStartError(
            Errors.AI_REQUEST_PREVIOUSLY_FAILED,
            commit_repairs=repaired_stale,
        )

    if active_pending:
        raise TurnStartError(
            Errors.AI_CONVERSATION_BUSY,
            commit_repairs=repaired_stale,
        )

    turn_id = str(uuid4())
    first_sequence = conversation.message_count + 1
    user_message = AIMessage(
        conversation_id=conversation.id,
        turn_id=turn_id,
        sequence_no=first_sequence,
        role="user",
        content=question,
        status="completed",
    )
    assistant_message = AIMessage(
        conversation_id=conversation.id,
        turn_id=turn_id,
        sequence_no=first_sequence + 1,
        role="assistant",
        content=None,
        status="pending",
    )
    run = AIAnswerRun(
        id=turn_id,
        conversation_id=conversation.id,
        idempotency_key=idempotency_key,
        status="pending",
        provider=provider,
        model=model,
        chart_fingerprint=chart_fingerprint,
        violation_codes=[],
        interpretation_receipt="",
        started_at=now,
    )
    if conversation.message_count == 0 and conversation.title == NEW_CONVERSATION_TITLE:
        compact_question = " ".join(question.split())
        conversation.title = compact_question[:30] or NEW_CONVERSATION_TITLE
    conversation.message_count += 2
    conversation.last_message_at = now
    db.add_all([user_message, assistant_message, run])
    await db.flush()
    return TurnState(conversation, run, user_message, assistant_message)


async def fail_turn(db: AsyncSession, state: TurnState, failure_code: str) -> None:
    now = datetime.now(UTC)
    run = await db.get(AIAnswerRun, state.run.id)
    if run is not None and run.status == "pending":
        run.status = "failed"
        run.failure_code = failure_code
        run.completed_at = now
    assistant = await db.get(AIMessage, state.assistant_message.id)
    if assistant is not None and assistant.status == "pending":
        assistant.status = "failed"
