"""Current-user profile and point-account endpoints."""

from fastapi import APIRouter
from sqlalchemy import select

from ...database import DBSession
from ...models import PointLedger
from ...schemas import ConsumeIn
from ...security import CurrentUser
from ...services import balance, consume

router = APIRouter(tags=["user"])


@router.get("/me")
async def profile(user: CurrentUser, db: DBSession):
    """返回当前登录用户的基本资料、角色和可用点数余额。"""
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role,
        "has_password": user.has_password,
        "points": await balance(db, user.id),
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
