"""Administrator configuration, user-management, and statistics endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from ...database import DBSession
from ...errors import APIError, Errors
from ...models import FeatureRule, PaymentOrder, PointPackage, User
from ...schemas import PackageIn, RuleIn, UserActiveIn, UserOut
from ...security import AdminUser

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/packages")
async def create_package(body: PackageIn, _: AdminUser, db: DBSession):
    """管理员创建点数套餐，配置价格、点数、套餐类型和启用状态。"""
    package = PointPackage(**body.model_dump())
    db.add(package)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise APIError(Errors.PACKAGE_NAME_ALREADY_EXISTS) from None
    return package


@router.get("/packages")
async def packages(_: AdminUser, db: DBSession):
    """管理员查询全部点数套餐，包括当前未启用的套餐。"""
    return (await db.execute(select(PointPackage))).scalars().all()


@router.put("/feature-rules/{code}")
async def set_rule(code: str, body: RuleIn, _: AdminUser, db: DBSession):
    """管理员按功能编码新增或更新点数消耗规则。"""
    rule = await db.get(FeatureRule, code)
    if rule:
        rule.points_cost = body.points_cost
        rule.active = body.active
    else:
        rule = FeatureRule(feature_code=code, **body.model_dump())
        db.add(rule)
    await db.commit()
    return rule


@router.get("/users", response_model=list[UserOut])
async def users(
    _: AdminUser,
    db: DBSession,
    phone: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """管理员分页查询用户，并可按手机号片段筛选。"""
    query = select(User)
    query = query.where(User.phone.contains(phone)) if phone else query
    return (
        await db.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
    ).scalars().all()


@router.patch("/users/{user_id}/active")
async def set_user_active(
    user_id: str, body: UserActiveIn, _: AdminUser, db: DBSession
):
    """管理员启用或停用指定用户；被停用用户不能继续访问受保护接口。"""
    target = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one_or_none()
    if not target:
        raise APIError(Errors.USER_NOT_FOUND)
    if target.is_active != body.is_active:
        target.is_active = body.is_active
        # Revoke every token issued before an account-status transition. This
        # also prevents old tokens becoming valid again after reactivation.
        target.auth_version += 1
    await db.commit()
    return {"id": target.id, "is_active": target.is_active}


@router.get("/recharge-statistics")
async def stats(
    _: AdminUser,
    db: DBSession,
    provider: str | None = None,
    package_id: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
):
    """管理员按支付渠道、套餐和支付时间范围汇总已支付订单。"""
    if start_at and end_at and start_at > end_at:
        raise APIError(Errors.INVALID_STATISTICS_TIME_RANGE)
    query = (
        select(
            PaymentOrder.provider,
            func.count(),
            func.coalesce(func.sum(PaymentOrder.amount_fen), 0),
        )
        .where(PaymentOrder.status == "paid")
        .group_by(PaymentOrder.provider)
    )
    if provider:
        query = query.where(PaymentOrder.provider == provider)
    if package_id:
        query = query.where(PaymentOrder.package_id == package_id)
    if start_at:
        query = query.where(PaymentOrder.paid_at >= start_at)
    if end_at:
        query = query.where(PaymentOrder.paid_at <= end_at)
    return [
        {"provider": row[0], "orders": row[1], "amount_fen": row[2]}
        for row in (await db.execute(query)).all()
    ]
