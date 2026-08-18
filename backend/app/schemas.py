from datetime import datetime

from pydantic import BaseModel, Field


class PhoneIn(BaseModel):
    phone: str


class VerifyIn(PhoneIn):
    code: str = Field(pattern=r"^\d{6}$")


class RefreshIn(BaseModel):
    refresh_token: str


class PackageIn(BaseModel):
    name: str
    kind: str = Field(pattern="^(one_time|monthly)$")
    points: int = Field(gt=0)
    price_fen: int = Field(gt=0)
    active: bool = True


class RuleIn(BaseModel):
    points_cost: int = Field(ge=0)
    active: bool = True


class ConsumeIn(BaseModel):
    feature_code: str
    idempotency_key: str = Field(min_length=8, max_length=128)


class OrderIn(BaseModel):
    package_id: str
    provider: str = Field(pattern="^(wechat|alipay)$")


class WebhookIn(BaseModel):
    event_id: str
    order_id: str
    provider_trade_no: str


class UserOut(BaseModel):
    id: str
    phone: str | None
    role: str
    is_active: bool
    created_at: datetime


class UserActiveIn(BaseModel):
    is_active: bool
