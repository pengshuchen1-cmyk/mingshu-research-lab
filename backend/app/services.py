import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Protocol

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import FeatureRule, OTPChallenge, PointBalance, PointLedger, User


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


async def issue_otp(db: AsyncSession, phone: str):
    if sms_provider is None:
        raise HTTPException(503, "SMS provider is not configured")
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
        raise HTTPException(429, "Daily OTP limit reached")
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
        raise HTTPException(429, "Please wait before requesting another OTP")
    # Generate a new OTP and store its hash in the database.
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(
        OTPChallenge(
            phone=phone,
            code_hash=digest(code),
            expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
        )
    )
    # Flush to ensure the OTPChallenge is persisted before sending the SMS.
    await db.flush()
    return await sms_provider.send(phone, code)


async def verify_otp(
    db: AsyncSession, phone: str, code: str
) -> tuple[User, bool]:
    now = datetime.now(UTC)
    # Lock the most recent OTPChallenge row for this phone to prevent concurrent verification attempts.
    row = (
        (
            await db.execute(
                select(OTPChallenge)
                .where(OTPChallenge.phone == phone)
                .order_by(OTPChallenge.created_at.desc())
                .with_for_update()
            )
        )
        .scalars()
        .first()
    )
    # Check the OTPChallenge row for validity, expiration, and attempt limits.
    if row and row.attempts >= settings.otp_max_attempts:
        raise HTTPException(429, "OTP attempt limit reached")
    if not row or row.consumed_at or row.expires_at.replace(tzinfo=UTC) < now:
        raise HTTPException(400, "Invalid or expired OTP")
    # Verify the provided code against the stored hash using a constant-time comparison to prevent timing attacks.
    if not secrets.compare_digest(row.code_hash, digest(code)):
        row.attempts += 1
        if row.attempts >= settings.otp_max_attempts:
            row.consumed_at = now
        raise HTTPException(400, "Invalid or expired OTP")
    # Mark the OTPChallenge as consumed to prevent reuse and return the associated user, creating a new user if necessary.
    row.consumed_at = now
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    new = user is None
    if user is None:
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
    return user, new


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
            raise HTTPException(409, "Idempotency key was reused for a different operation")
        return existing
    if current + delta < 0:
        raise HTTPException(409, "Insufficient points")
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
        raise HTTPException(404, "Feature rule not found")
    return await credit(db, user_id, -rule.points_cost, "consume", key, feature)
