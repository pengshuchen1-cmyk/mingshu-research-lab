import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .errors import APIError, Errors
from .models import FeatureRule, OTPChallenge, PointBalance, PointLedger, User
from .passwords import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    password_needs_rehash,
    verify_password,
)

OTP_LOGIN = "login"
OTP_PASSWORD_RESET = "password_reset"


class SMSProvider(Protocol):
    async def send(self, phone: str, code: str) -> str | None: ...


class DevelopmentSMSProvider:
    """Local-only adapter. A production adapter must implement send(phone, code)."""
    async def send(self, phone: str, code: str) -> str | None:
        return code


sms_provider = DevelopmentSMSProvider() if settings.environment != "production" else None


def register_sms_provider(provider: SMSProvider) -> None:
    """Application bootstrap hook for a real, credentialed provider adapter."""
    global sms_provider
    sms_provider = provider


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


async def issue_otp(db: AsyncSession, phone: str, purpose: str = OTP_LOGIN):
    if sms_provider is None:
        raise APIError(Errors.SMS_PROVIDER_NOT_CONFIGURED)
    user = (
        await db.execute(select(User).where(User.phone == phone))
    ).scalar_one_or_none()
    if user is not None and not user.is_active:
        raise APIError(Errors.USER_UNAVAILABLE)
    now = datetime.now(UTC)
    # Check the daily limit and resend interval before issuing a new OTP.
    recent = (
        await db.execute(
            select(func.count())
            .select_from(OTPChallenge)
            .where(
                OTPChallenge.phone == phone,
                OTPChallenge.created_at > now - timedelta(days=1),
            )
        )
    ).scalar_one()
    if recent >= settings.otp_daily_limit:
        raise APIError(Errors.OTP_DAILY_LIMIT_REACHED)
    # Check the resend interval before issuing a new OTP.
    last = (
        (
            await db.execute(
                select(OTPChallenge)
                .where(OTPChallenge.phone == phone)
                .order_by(OTPChallenge.created_at.desc())
            )
        )
        .scalars()
        .first()
    )
    if last and last.created_at.replace(tzinfo=UTC) > now - timedelta(
        seconds=settings.otp_resend_seconds
    ):
        raise APIError(Errors.OTP_RESEND_TOO_SOON)
    # Generate a new OTP and store its hash in the database.
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        OTPChallenge(
            phone=phone,
            code_hash=digest(code),
            purpose=purpose,
            expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
        )
    )
    # Flush to ensure the OTPChallenge is persisted before sending the SMS.
    await db.flush()
    return await sms_provider.send(phone, code)


async def verify_otp(
    db: AsyncSession,
    phone: str,
    code: str,
    purpose: str = OTP_LOGIN,
    *,
    create_user: bool = True,
) -> tuple[User, bool]:
    now = datetime.now(UTC)
    # Lock the most recent OTPChallenge row for this phone to prevent concurrent verification attempts.
    row = (
        (
            await db.execute(
                select(OTPChallenge)
                .where(
                    OTPChallenge.phone == phone,
                    OTPChallenge.purpose == purpose,
                )
                .order_by(OTPChallenge.created_at.desc())
                .with_for_update()
            )
        )
        .scalars()
        .first()
    )
    # Check the OTPChallenge row for validity, expiration, and attempt limits.
    if row and row.attempts >= settings.otp_max_attempts:
        raise APIError(Errors.OTP_ATTEMPT_LIMIT_REACHED)
    if not row or row.consumed_at or row.expires_at.replace(tzinfo=UTC) < now:
        raise APIError(Errors.OTP_INVALID_OR_EXPIRED)
    # Verify the provided code against the stored hash using a constant-time comparison to prevent timing attacks.
    if not secrets.compare_digest(row.code_hash, digest(code)):
        row.attempts += 1
        if row.attempts >= settings.otp_max_attempts:
            row.consumed_at = now
        raise APIError(Errors.OTP_INVALID_OR_EXPIRED)
    # Mark the OTPChallenge as consumed to prevent reuse and return the associated user, creating a new user if necessary.
    row.consumed_at = now
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    new = user is None
    if user is None:
        if not create_user:
            raise APIError(Errors.USER_UNAVAILABLE)
        candidate = User(phone=phone)
        # Attempt to create a new user and grant the registration bonus in a nested transaction. 
        # If a concurrent transaction has already created a user with this phone, catch the IntegrityError and retrieve the existing user instead, 
        # ensuring that the registration bonus is only granted once per phone number.
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
                db.add(PointBalance(user_id=candidate.id, balance=0))
                await db.flush()
                await credit(
                    db, candidate.id, settings.registration_bonus_points,
                    "registration_bonus", f"signup:{candidate.id}"
                )
            user = candidate
        except IntegrityError:
            # Another transaction registered this phone; use that account and never grant twice.
            user = (await db.execute(select(User).where(User.phone == phone))).scalar_one()
            new = False
    assert user is not None
    if not user.is_active:
        raise APIError(Errors.USER_UNAVAILABLE)
    return user, new


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def authenticate_password(
    db: AsyncSession, phone: str, password: str
) -> User:
    now = datetime.now(UTC)
    user = (
        await db.execute(
            select(User).where(User.phone == phone).with_for_update()
        )
    ).scalar_one_or_none()
    if user and user.password_locked_until:
        if _as_utc(user.password_locked_until) > now:
            raise APIError(Errors.PASSWORD_LOGIN_LOCKED)
        user.password_locked_until = None
        user.password_failed_attempts = 0

    encoded = user.password_hash if user and user.password_hash else DUMMY_PASSWORD_HASH
    valid = await run_in_threadpool(verify_password, password, encoded)
    if not user or not user.is_active or not user.password_hash or not valid:
        if user and user.is_active and user.password_hash:
            user.password_failed_attempts += 1
            if user.password_failed_attempts >= settings.password_max_attempts:
                user.password_locked_until = now + timedelta(
                    minutes=settings.password_lock_minutes
                )
                raise APIError(Errors.PASSWORD_LOGIN_LOCKED)
        raise APIError(Errors.INVALID_PASSWORD_CREDENTIALS)

    user.password_failed_attempts = 0
    user.password_locked_until = None
    if password_needs_rehash(user.password_hash):
        user.password_hash = await run_in_threadpool(hash_password, password)
    return user


async def register_password_user(
    db: AsyncSession, phone: str, password: str
) -> User:
    """Create one phone/password account without SMS verification."""
    existing = (
        await db.execute(select(User).where(User.phone == phone))
    ).scalar_one_or_none()
    if existing is not None:
        raise APIError(Errors.ACCOUNT_ALREADY_REGISTERED)

    candidate = User(
        phone=phone,
        password_hash=await run_in_threadpool(hash_password, password),
    )
    try:
        async with db.begin_nested():
            db.add(candidate)
            await db.flush()
            db.add(PointBalance(user_id=candidate.id, balance=0))
            await db.flush()
            await credit(
                db,
                candidate.id,
                settings.registration_bonus_points,
                "registration_bonus",
                f"signup:{candidate.id}",
            )
    except IntegrityError:
        # A concurrent request may have registered the same normalized phone.
        raise APIError(Errors.ACCOUNT_ALREADY_REGISTERED)
    return candidate


async def change_user_password(
    db: AsyncSession,
    user_id: str,
    new_password: str,
    current_password: str | None = None,
    *,
    verify_existing_password: bool,
) -> User:
    user = (
        await db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    if verify_existing_password and user.password_hash:
        if current_password is None:
            raise APIError(Errors.CURRENT_PASSWORD_REQUIRED)
        now = datetime.now(UTC)
        if user.password_locked_until:
            if _as_utc(user.password_locked_until) > now:
                raise APIError(Errors.PASSWORD_LOGIN_LOCKED)
            user.password_locked_until = None
            user.password_failed_attempts = 0
        current_valid = await run_in_threadpool(
            verify_password, current_password, user.password_hash
        )
        if not current_valid:
            user.password_failed_attempts += 1
            if user.password_failed_attempts >= settings.password_max_attempts:
                user.password_locked_until = now + timedelta(
                    minutes=settings.password_lock_minutes
                )
                raise APIError(Errors.PASSWORD_LOGIN_LOCKED)
            raise APIError(Errors.INVALID_PASSWORD_CREDENTIALS)
        user.password_failed_attempts = 0
        user.password_locked_until = None
        if await run_in_threadpool(verify_password, new_password, user.password_hash):
            raise APIError(Errors.PASSWORD_UNCHANGED)

    user.password_hash = await run_in_threadpool(hash_password, new_password)
    user.password_failed_attempts = 0
    user.password_locked_until = None
    user.auth_version += 1
    return user


async def balance(db, user_id):
    value = await db.scalar(select(PointBalance.balance).where(PointBalance.user_id == user_id))
    return value or 0


# Credit and consume functions are designed to be used within a transaction, 
# and they will acquire a row-level lock on the user's PointBalance to prevent concurrent modifications.
async def credit(db, user_id, delta, event, key, reference=None, metadata=None):
    wallet = (await db.execute(select(PointBalance).where(PointBalance.user_id == user_id).with_for_update())).scalar_one_or_none()
    if not wallet:
        # Lock the user before creating a legacy/missing wallet so concurrent credits cannot fork it.
        await db.execute(select(User.id).where(User.id == user_id).with_for_update())
        wallet = await db.get(PointBalance, user_id)
        if not wallet:
            wallet = PointBalance(user_id=user_id, balance=0)
            db.add(wallet)
            await db.flush()
    current = wallet.balance
    # Must be checked after acquiring the wallet lock: another transaction may
    # have committed this same key while this transaction was waiting.
    existing = (await db.execute(select(PointLedger).where(PointLedger.user_id == user_id, PointLedger.idempotency_key == key))).scalar_one_or_none()
    if existing:
        if existing.delta != delta or existing.event_type != event or existing.reference_id != reference:
            raise APIError(Errors.IDEMPOTENCY_KEY_CONFLICT)
        return existing
    if current + delta < 0:
        raise APIError(Errors.INSUFFICIENT_POINTS)
    item = PointLedger(
        user_id=user_id,
        delta=delta,
        balance_after=current + delta,
        event_type=event,
        idempotency_key=key,
        reference_id=reference,
        metadata_=metadata or {},
    )
    db.add(item)
    wallet.balance = current + delta
    await db.flush()
    return item


async def consume(db, user_id, feature, key):
    rule = (
        await db.execute(
            select(FeatureRule).where(
                FeatureRule.feature_code == feature, FeatureRule.active.is_(True)
            )
        )
    ).scalar_one_or_none()
    if not rule:
        raise APIError(Errors.FEATURE_RULE_NOT_FOUND)
    return await credit(db, user_id, -rule.points_cost, "consume", key, feature)
