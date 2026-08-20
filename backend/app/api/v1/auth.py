"""Registration, login, password, token, and reserved WeChat endpoints."""

import jwt
import phonenumbers
from fastapi import APIRouter

from ...config import settings
from ...database import DBSession
from ...errors import APIError, Errors
from ...models import User
from ...schemas import (
    AccessTokenOut,
    OTPOut,
    PasswordChangeIn,
    PasswordResetIn,
    PhoneIn,
    PhonePasswordIn,
    RefreshIn,
    TokenPairOut,
    VerifyIn,
)
from ...security import CurrentUser, token_for
from ...services import (
    OTP_PASSWORD_RESET,
    authenticate_password,
    change_user_password,
    issue_otp,
    verify_otp,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(user: User, *, new_user: bool = False) -> dict:
    return {
        "access_token": token_for(user),
        "refresh_token": token_for(user, "refresh"),
        "token_type": "bearer",
        "new_user": new_user,
    }


def normalize(phone: str) -> str:
    try:
        parsed = phonenumbers.parse(phone, "CN")
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(Errors.INVALID_PHONE.code)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.NumberParseException, ValueError):
        raise APIError(Errors.INVALID_PHONE) from None


@router.post("/otp/login/code", response_model=OTPOut)
async def request_login_otp(body: PhoneIn, db: DBSession):
    """向有效手机号发送登录验证码；开发环境可返回调试验证码。"""
    code = await issue_otp(db, normalize(body.phone))
    await db.commit()
    return {"message": "OTP sent", "development_code": code}


@router.post("/otp/login", response_model=TokenPairOut)
async def otp_login(body: VerifyIn, db: DBSession):
    """校验短信验证码，自动注册新用户，并签发访问令牌和刷新令牌。"""
    try:
        user, new = await verify_otp(db, normalize(body.phone), body.code)
    except APIError:
        # Failed-attempt counter/lockout is deliberate security state.
        await db.commit()
        raise
    await db.commit()
    return _token_pair(user, new_user=new)


@router.post("/password/login", response_model=TokenPairOut)
async def password_login(body: PhonePasswordIn, db: DBSession):
    """校验已有用户的手机号和密码，并签发访问令牌与刷新令牌。"""
    try:
        user = await authenticate_password(db, normalize(body.phone), body.password)
    except APIError:
        # Failed-attempt counters and temporary lockouts are security state.
        await db.commit()
        raise
    await db.commit()
    return _token_pair(user)


@router.put("/password", response_model=TokenPairOut)
async def set_or_change_password(
    body: PasswordChangeIn,
    user: CurrentUser,
    db: DBSession,
):
    """为登录用户设置首个密码，或校验当前密码后修改已有密码。"""
    try:
        updated = await change_user_password(
            db,
            user.id,
            body.new_password,
            body.current_password,
            verify_existing_password=True,
        )
    except APIError:
        # Wrong-current-password counters and temporary lockouts are security state.
        await db.commit()
        raise
    await db.commit()
    return _token_pair(updated)


@router.post("/password/reset/otp", response_model=OTPOut)
async def request_password_reset_otp(body: PhoneIn, db: DBSession):
    """发送只能用于找回密码的短信验证码，与登录验证码相互隔离。"""
    code = await issue_otp(db, normalize(body.phone), OTP_PASSWORD_RESET)
    await db.commit()
    return {"message": "OTP sent", "development_code": code}


@router.post("/password/reset", response_model=TokenPairOut)
async def reset_password(body: PasswordResetIn, db: DBSession):
    """校验密码重置验证码，设置新密码并使该用户之前的 JWT 失效。"""
    try:
        user, _ = await verify_otp(
            db,
            normalize(body.phone),
            body.code,
            OTP_PASSWORD_RESET,
            create_user=False,
        )
        updated = await change_user_password(
            db,
            user.id,
            body.new_password,
            verify_existing_password=False,
        )
    except APIError:
        # OTP failure attempts and consumption must survive the response error.
        await db.commit()
        raise
    await db.commit()
    return _token_pair(updated)


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh(body: RefreshIn, db: DBSession):
    """校验刷新令牌，为状态正常的用户签发新的访问令牌。"""
    try:
        payload = jwt.decode(
            body.refresh_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError:
        raise APIError(Errors.INVALID_REFRESH_TOKEN) from None
    if payload.get("typ") != "refresh":
        raise APIError(Errors.REFRESH_TOKEN_REQUIRED)
    subject = payload.get("sub")
    user = await db.get(User, subject) if isinstance(subject, str) else None
    if not user or not user.is_active:
        raise APIError(Errors.USER_UNAVAILABLE)
    if payload.get("ver", 0) != user.auth_version:
        raise APIError(Errors.INVALID_REFRESH_TOKEN)
    return {"access_token": token_for(user), "token_type": "bearer"}


@router.get("/wechat/qr")
async def wechat_qr():
    """预留微信公众号扫码登录入口；未配置微信适配器时返回 501。"""
    if not settings.wechat_app_id:
        raise APIError(Errors.WECHAT_QR_NOT_CONFIGURED)
    return {
        "message": "Implement official-account QR scene creation and callback signature verification here"
    }
