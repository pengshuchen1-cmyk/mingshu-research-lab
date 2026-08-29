"""Authenticated memory archive endpoints used by the personal-memory page."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import or_, select

from ...config import settings
from ...database import DBSession
from ...errors import APIError, Errors
from ...models import MemoryEntry
from ...schemas import (
    MemoryCategory,
    MemoryCategorySummaryOut,
    MemoryCreateIn,
    MemoryEntryOut,
    MemoryOverviewOut,
)
from ...security import CurrentUser

router = APIRouter(prefix="/memories", tags=["memories"])

MEMORY_CATEGORIES: tuple[MemoryCategory, ...] = (
    "基本信息",
    "职业事业",
    "感情关系",
    "家庭生活",
    "健康状态",
    "目标愿望",
    "重要人物",
    "其他记忆",
)

FOCUS_TAGS = {
    "基本信息": "重视自我认识",
    "职业事业": "关注事业发展",
    "感情关系": "重视亲密关系",
    "家庭生活": "关注家庭生活",
    "健康状态": "关注身心健康",
    "目标愿望": "有目标感",
    "重要人物": "珍视重要关系",
    "其他记忆": "记录生活细节",
}


def _as_utc(value: datetime | None) -> datetime | None:
    """MySQL drops tzinfo from DATETIME values; persisted timestamps are UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _memory_out(entry: MemoryEntry) -> MemoryEntryOut:
    return MemoryEntryOut(
        id=entry.id,
        title=entry.title,
        category=entry.category,
        content=entry.content,
        occurred_on=entry.occurred_on,
        is_timeline_event=entry.is_timeline_event,
        source=entry.source,
        deletable=True,
        feedback=entry.feedback,
        ai_use_count=entry.ai_use_count,
        last_used_at=_as_utc(entry.last_used_at),
        created_at=_as_utc(entry.created_at),
        updated_at=_as_utc(entry.updated_at),
    )


async def _owned_memory(db: DBSession, memory_id: str, user_id: str) -> MemoryEntry:
    entry = (
        await db.execute(
            select(MemoryEntry).where(
                MemoryEntry.id == memory_id,
                MemoryEntry.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if entry is None:
        raise APIError(Errors.MEMORY_NOT_FOUND)
    return entry


@router.get("/overview", response_model=MemoryOverviewOut)
async def memory_overview(user: CurrentUser, db: DBSession):
    """Return counts, latest dates and honest category-based understanding text."""
    entries = (
        (
            await db.execute(
                select(MemoryEntry)
                .where(MemoryEntry.user_id == user.id)
                .order_by(MemoryEntry.updated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    category_summaries: list[MemoryCategorySummaryOut] = []
    active_categories: list[MemoryCategory] = []
    for category in MEMORY_CATEGORIES:
        matching = [entry for entry in entries if entry.category == category]
        latest_date = max((entry.occurred_on for entry in matching), default=None)
        category_summaries.append(
            MemoryCategorySummaryOut(
                category=category,
                count=len(matching),
                latest_date=latest_date,
            )
        )
        if matching:
            active_categories.append(category)

    focus_tags = [FOCUS_TAGS[category] for category in active_categories[:6]]
    if entries:
        category_text = "、".join(active_categories[:3])
        understanding_summary = (
            f"目前已记录 {len(entries)} 条记忆"
            + (f"，主要集中在{category_text}" if category_text else "")
            + "。你可以继续补充背景和变化，让这些资料保持准确。"
        )
    else:
        understanding_summary = "还没有记忆记录。新增重要事实、目标或关系后，可在这里统一管理。"

    return MemoryOverviewOut(
        total_memories=len(entries),
        goal_count=sum(entry.category == "目标愿望" for entry in entries),
        important_people_count=sum(entry.category == "重要人物" for entry in entries),
        life_event_count=sum(entry.is_timeline_event for entry in entries),
        feedback_count=sum(bool(entry.feedback) for entry in entries),
        latest_updated_at=_as_utc(
            max((entry.updated_at for entry in entries), default=None)
        ),
        categories=category_summaries,
        focus_tags=focus_tags,
        understanding_summary=understanding_summary,
    )


@router.get("", response_model=list[MemoryEntryOut])
async def list_memories(
    user: CurrentUser,
    db: DBSession,
    category: MemoryCategory | None = None,
    search: Annotated[str, Query(max_length=100)] = "",
    has_feedback: bool | None = None,
    timeline_only: bool = False,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
):
    """List the current user's memories with filters required by the archive tabs."""
    statement = select(MemoryEntry).where(MemoryEntry.user_id == user.id)
    if category is not None:
        statement = statement.where(MemoryEntry.category == category)
    normalized_search = search.strip()
    if normalized_search:
        statement = statement.where(
            or_(
                MemoryEntry.title.contains(normalized_search),
                MemoryEntry.content.contains(normalized_search),
            )
        )
    if has_feedback is True:
        statement = statement.where(
            MemoryEntry.feedback.is_not(None),
            MemoryEntry.feedback != "",
        )
    elif has_feedback is False:
        statement = statement.where(
            or_(MemoryEntry.feedback.is_(None), MemoryEntry.feedback == "")
        )
    if timeline_only:
        statement = statement.where(MemoryEntry.is_timeline_event.is_(True))
    entries = (
        (
            await db.execute(
                statement.order_by(
                    MemoryEntry.occurred_on.desc(),
                    MemoryEntry.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [_memory_out(entry) for entry in entries]


@router.post("", response_model=MemoryEntryOut, status_code=status.HTTP_201_CREATED)
async def create_memory(body: MemoryCreateIn, user: CurrentUser, db: DBSession):
    """Persist one manually supplied memory under the authenticated account."""
    occurred_on = body.occurred_on or datetime.now(ZoneInfo(settings.app_timezone)).date()
    entry = MemoryEntry(
        user_id=user.id,
        title=body.title,
        category=body.category,
        content=body.content,
        occurred_on=occurred_on,
        is_timeline_event=body.is_timeline_event,
        source="manual",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return _memory_out(entry)


@router.get("/{memory_id}", response_model=MemoryEntryOut)
async def get_memory(memory_id: str, user: CurrentUser, db: DBSession):
    """Return one owned memory without revealing other users' entry IDs."""
    return _memory_out(await _owned_memory(db, memory_id, user.id))


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: str, user: CurrentUser, db: DBSession):
    """Permanently delete one owned memory."""
    entry = await _owned_memory(db, memory_id, user.id)
    await db.delete(entry)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
