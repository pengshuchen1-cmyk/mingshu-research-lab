"""Current-user profile and point-account endpoints."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from sqlalchemy import select

from ...config import settings
from ...database import DBSession
from ...models import PointLedger
from ...schemas import ConsumeIn, CurrentUserOut
from ...security import CurrentUser
from ...services import balance, consume

router = APIRouter(tags=["user"])


def _as_utc(value: datetime) -> datetime:
    """Normalize database datetimes; this project stores naive MySQL values as UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _companion_days_since(created_at: datetime, now: datetime | None = None) -> int:
    """Count product-local calendar days inclusively, so registration day is day one."""
    product_timezone = ZoneInfo(settings.app_timezone)
    created_date = _as_utc(created_at).astimezone(product_timezone).date()
    current_date = _as_utc(now or datetime.now(UTC)).astimezone(product_timezone).date()
    return max((current_date - created_date).days + 1, 1)


@router.get("/me", response_model=CurrentUserOut)
async def profile(user: CurrentUser, db: DBSession):
    """返回当前用户资料、余额、注册时间及按业务时区计算的陪伴天数。"""
    created_at = _as_utc(user.created_at)
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role,
        "has_password": user.has_password,
        "points": await balance(db, user.id),
        "created_at": created_at,
        "companion_days": _companion_days_since(created_at),
    }


@router.get("/points/ledger")
async def ledger(user: CurrentUser, db: DBSession):
    """按时间倒序返回当前登录用户的全部点数变动流水。"""
    return (
        (
            await db.execute(
                select(PointLedger)
                .where(PointLedger.user_id == user.id)
                .order_by(PointLedger.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


@router.post("/points/consume")
async def consume_points(body: ConsumeIn, user: CurrentUser, db: DBSession):
    """按功能消耗策略扣减当前用户点数，并通过幂等键防止重复扣费。"""
    item = await consume(db, user.id, body.feature_code, body.idempotency_key)
    await db.commit()
    return {"ledger_id": item.id, "balance": item.balance_after}
