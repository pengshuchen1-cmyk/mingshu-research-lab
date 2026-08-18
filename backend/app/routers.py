from datetime import datetime
from typing import Annotated

import jwt
import phonenumbers
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from .config import settings
from .database import DBSession
from .models import FeatureRule, PaymentOrder, PointLedger, PointPackage, User
from .schemas import *
from .security import AdminUser, CurrentUser, token_for
from .services import balance, consume, issue_otp, verify_otp

auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])
me = APIRouter(prefix="/api/v1", tags=["user"])
admin = APIRouter(prefix="/api/v1/admin", tags=["admin"])
pay = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def normalize(phone):
    try:
        parsed = phonenumbers.parse(phone, "CN")
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("invalid phone")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.NumberParseException, ValueError):
        raise HTTPException(422, "Invalid phone number")


@auth.post("/otp")
async def request_otp(body: PhoneIn, db: DBSession):
    """向有效手机号发送登录验证码；开发环境可返回调试验证码。"""
    code = await issue_otp(db, normalize(body.phone))
    await db.commit()
    return {"message": "OTP sent", "development_code": code}


@auth.post("/verify")
async def login(body: VerifyIn, db: DBSession):
    """校验短信验证码，自动注册新用户，并签发访问令牌和刷新令牌。"""
    try:
        user, new = await verify_otp(db, normalize(body.phone), body.code)
    except HTTPException:
        # Failed-attempt counter/lockout is deliberate security state.
        await db.commit()
        raise
    await db.commit()
    return {
        "access_token": token_for(user),
        "refresh_token": token_for(user, "refresh"),
        "token_type": "bearer",
        "new_user": new,
    }


@auth.post("/refresh")
async def refresh(body: RefreshIn, db: DBSession):
    """校验刷新令牌，为状态正常的用户签发新的访问令牌。"""
    try:
        p = jwt.decode(
            body.refresh_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")
    if p.get("typ") != "refresh":
        raise HTTPException(401, "Refresh token required")
    user = await db.get(User, p["sub"])
    if not user or not user.is_active:
        raise HTTPException(401, "User unavailable")
    return {"access_token": token_for(user), "token_type": "bearer"}


@auth.get("/wechat/qr")
async def wechat_qr():
    """预留微信公众号扫码登录入口；未配置微信适配器时返回 501。"""
    if not settings.wechat_app_id:
        raise HTTPException(501, "WeChat QR login is not configured")
    return {
        "message": "Implement official-account QR scene creation and callback signature verification here"
    }


@me.get("/me")
async def profile(user: CurrentUser, db: DBSession):
    """返回当前登录用户的基本资料、角色和可用点数余额。"""
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role,
        "points": await balance(db, user.id),
    }


@me.get("/points/ledger")
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


@me.post("/points/consume")
async def consume_points(
    body: ConsumeIn, user: CurrentUser, db: DBSession
):
    """按功能消耗策略扣减当前用户点数，并通过幂等键防止重复扣费。"""
    x = await consume(db, user.id, body.feature_code, body.idempotency_key)
    await db.commit()
    return {"ledger_id": x.id, "balance": x.balance_after}


@admin.post("/packages")
async def create_package(
    body: PackageIn, _: AdminUser, db: DBSession
):
    """管理员创建点数套餐，配置价格、点数、套餐类型和启用状态。"""
    x = PointPackage(**body.model_dump())
    db.add(x)
    await db.commit()
    return x


@admin.get("/packages")
async def packages(_: AdminUser, db: DBSession):
    """管理员查询全部点数套餐，包括当前未启用的套餐。"""
    return (await db.execute(select(PointPackage))).scalars().all()


@admin.put("/feature-rules/{code}")
async def set_rule(
    code: str, body: RuleIn, _: AdminUser, db: DBSession
):
    """管理员按功能编码新增或更新点数消耗规则。"""
    x = await db.get(FeatureRule, code)
    if x:
        x.points_cost = body.points_cost
        x.active = body.active
    else:
        x = FeatureRule(feature_code=code, **body.model_dump())
        db.add(x)
    await db.commit()
    return x


@admin.get("/users")
async def users(
    _: AdminUser,
    db: DBSession,
    phone: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """管理员分页查询用户，并可按手机号片段筛选。"""
    q = select(User)
    q = q.where(User.phone.contains(phone)) if phone else q
    return (await db.execute(q.order_by(User.created_at.desc()).offset(offset).limit(limit))).scalars().all()


@admin.patch("/users/{user_id}/active")
async def set_user_active(
    user_id: str, body: UserActiveIn, _: AdminUser, db: DBSession
):
    """管理员启用或停用指定用户；被停用用户不能继续访问受保护接口。"""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    target.is_active = body.is_active
    await db.commit()
    return {"id": target.id, "is_active": target.is_active}


@admin.get("/recharge-statistics")
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
        raise HTTPException(422, "start_at must be before end_at")
    q = (
        select(
            PaymentOrder.provider, func.count(), func.coalesce(func.sum(PaymentOrder.amount_fen), 0)
        )
        .where(PaymentOrder.status == "paid")
        .group_by(PaymentOrder.provider)
    )
    if provider:
        q = q.where(PaymentOrder.provider == provider)
    if package_id:
        q = q.where(PaymentOrder.package_id == package_id)
    if start_at:
        q = q.where(PaymentOrder.paid_at >= start_at)
    if end_at:
        q = q.where(PaymentOrder.paid_at <= end_at)
    return [
        {"provider": r[0], "orders": r[1], "amount_fen": r[2]} for r in (await db.execute(q)).all()
    ]


@pay.get("/packages")
async def public_packages(db: DBSession):
    """公开查询当前可购买的已启用点数套餐。"""
    return (
        (await db.execute(select(PointPackage).where(PointPackage.active.is_(True))))
        .scalars()
        .all()
    )


@pay.post("/orders")
async def order(body: OrderIn, user: CurrentUser, db: DBSession):
    """登录用户创建微信或支付宝待支付订单；预支付参数适配器尚未接入。"""
    package = await db.get(PointPackage, body.package_id)
    if not package or not package.active:
        raise HTTPException(404, "Package unavailable")
    x = PaymentOrder(
        user_id=user.id, package_id=package.id, provider=body.provider, amount_fen=package.price_fen
    )
    db.add(x)
    await db.commit()
    # Provider adapters must create signed WeChat/Alipay prepay payloads; never mark orders paid client-side.
    return {"order_id": x.id, "status": x.status, "provider": x.provider, "payment_payload": None}


@pay.post("/webhooks/{provider}")
async def webhook(provider: str, body: WebhookIn, db: DBSession):
    """预留微信和支付宝异步回调入口；验签适配器未配置时安全返回 501。"""
    if provider not in {"wechat", "alipay"}:
        raise HTTPException(404, "Unknown payment provider")
    # Safe by default: the raw platform callback/signature verifier is not implemented.
    # Do not write event/order state until the verifier has authenticated the callback.
    raise HTTPException(501, "Payment provider signature verification is not configured")
