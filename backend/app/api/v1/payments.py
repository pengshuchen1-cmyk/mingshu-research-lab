"""Public packages, payment orders, and provider callback endpoints."""

from fastapi import APIRouter
from sqlalchemy import select

from ...database import DBSession
from ...errors import APIError, Errors
from ...models import PaymentOrder, PointPackage
from ...schemas import OrderIn, WebhookIn
from ...security import CurrentUser

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/packages")
async def public_packages(db: DBSession):
    """公开查询当前可购买的已启用点数套餐。"""
    return (
        (await db.execute(select(PointPackage).where(PointPackage.active.is_(True))))
        .scalars()
        .all()
    )


@router.post("/orders")
async def order(body: OrderIn, user: CurrentUser, db: DBSession):
    """登录用户创建微信或支付宝待支付订单；预支付参数适配器尚未接入。"""
    package = await db.get(PointPackage, body.package_id)
    if not package or not package.active:
        raise APIError(Errors.PACKAGE_UNAVAILABLE)
    payment_order = PaymentOrder(
        user_id=user.id,
        package_id=package.id,
        provider=body.provider,
        amount_fen=package.price_fen,
    )
    db.add(payment_order)
    await db.commit()
    # Provider adapters must create signed WeChat/Alipay prepay payloads; never
    # mark orders paid client-side.
    return {
        "order_id": payment_order.id,
        "status": payment_order.status,
        "provider": payment_order.provider,
        "payment_payload": None,
    }


@router.post("/webhooks/{provider}")
async def webhook(provider: str, body: WebhookIn, db: DBSession):
    """预留微信和支付宝异步回调入口；验签适配器未配置时安全返回 501。"""
    if provider not in {"wechat", "alipay"}:
        raise APIError(Errors.UNKNOWN_PAYMENT_PROVIDER)
    # Safe by default: the raw platform callback/signature verifier is not
    # implemented. Do not write event/order state until the verifier has
    # authenticated the callback.
    raise APIError(Errors.PAYMENT_SIGNATURE_NOT_CONFIGURED)
