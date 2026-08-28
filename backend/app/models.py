import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    auth_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    password_failed_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    password_locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None


class BirthProfile(Base):
    """User-owned birth information used as the sole input to chart generation."""

    __tablename__ = "birth_profiles"
    __table_args__ = (
        CheckConstraint("gender IN ('男', '女')", name="ck_birth_profiles_gender"),
        CheckConstraint(
            "calendar_type IN ('solar', 'lunar')",
            name="ck_birth_profiles_calendar_type",
        ),
        CheckConstraint(
            "(birth_hour IS NULL AND birth_minute IS NULL) OR "
            "(birth_hour BETWEEN 0 AND 23 AND birth_minute BETWEEN 0 AND 59)",
            name="ck_birth_profiles_time_pair",
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[Literal["男", "女"]] = mapped_column(String(8))
    calendar_type: Mapped[Literal["solar", "lunar"]] = mapped_column(String(8))
    # Source-calendar text, rather than SQL DATE: a valid lunar date such as
    # lunar February 30 is not necessarily a valid Gregorian date object.
    birth_date: Mapped[str] = mapped_column(String(10))
    solar_birth_date: Mapped[date] = mapped_column(Date)
    birth_hour: Mapped[int | None] = mapped_column(Integer)
    birth_minute: Mapped[int | None] = mapped_column(Integer)
    birth_place: Mapped[str] = mapped_column(String(200), default="")
    is_leap_month: Mapped[bool] = mapped_column(Boolean, default=False)
    time_label: Mapped[str] = mapped_column(String(40), default="精确时间")
    edit_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BaziChart(Base):
    """Latest deterministic chart snapshot for one birth profile."""

    __tablename__ = "bazi_charts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("birth_profiles.id", ondelete="CASCADE"), unique=True
    )
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    chart_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    engine_version: Mapped[str] = mapped_column(String(32))
    chart_json: Mapped[dict] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MemoryEntry(Base):
    """User-owned facts and life events used by the memory archive UI."""

    __tablename__ = "memory_entries"
    __table_args__ = (
        CheckConstraint(
            "category IN ('基本信息', '职业事业', '感情关系', '家庭生活', "
            "'健康状态', '目标愿望', '重要人物', '其他记忆')",
            name="ck_memory_entries_category",
        ),
        CheckConstraint(
            "source IN ('manual', 'ai')",
            name="ck_memory_entries_source",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(16), index=True)
    content: Mapped[str] = mapped_column(Text)
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    is_timeline_event: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1"
    )
    source: Mapped[str] = mapped_column(String(16), default="manual", server_default="manual")
    feedback: Mapped[str | None] = mapped_column(Text)
    ai_use_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    purpose: Mapped[str] = mapped_column(String(20), default="login")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PointPackage(Base):
    __tablename__ = "point_packages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(16))  # one_time/monthly
    points: Mapped[int] = mapped_column(Integer)
    price_fen: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureRule(Base):
    __tablename__ = "feature_rules"
    feature_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    points_cost: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PointLedger(Base):
    __tablename__ = "point_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_ledger_user_idempotency"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    delta: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(32))
    reference_id: Mapped[str | None] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PointBalance(Base):
    """Locked balance cache; point_ledger remains the immutable audit source."""
    __tablename__ = "point_balances"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("point_packages.id"))
    provider: Mapped[str] = mapped_column(String(16))
    amount_fen: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    provider_trade_no: Mapped[str | None] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    provider: Mapped[str] = mapped_column(String(16))
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
