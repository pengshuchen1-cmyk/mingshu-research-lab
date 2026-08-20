from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PhoneIn(BaseModel):
    phone: str


class VerifyIn(PhoneIn):
    code: str = Field(pattern=r"^\d{6}$")


class PhonePasswordIn(PhoneIn):
    password: str = Field(min_length=8, max_length=128, repr=False)


class PasswordChangeIn(BaseModel):
    current_password: str | None = Field(
        default=None, min_length=8, max_length=128, repr=False
    )
    new_password: str = Field(min_length=8, max_length=128, repr=False)


class PasswordResetIn(VerifyIn):
    new_password: str = Field(min_length=8, max_length=128, repr=False)


class OTPOut(BaseModel):
    message: str
    development_code: str | None = None


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    new_user: bool = False


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


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
    model_config = ConfigDict(from_attributes=True)

    id: str
    phone: str | None
    role: str
    is_active: bool
    has_password: bool = False
    created_at: datetime


class UserActiveIn(BaseModel):
    is_active: bool


class BirthProfileIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    gender: Literal["男", "女"]
    calendar_type: Literal["solar", "lunar"]
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_hour: int | None = Field(default=None, ge=0, le=23)
    birth_minute: int | None = Field(default=None, ge=0, le=59)
    birth_place: str = Field(default="", max_length=200)
    is_leap_month: bool = False
    time_label: str = Field(default="精确时间", min_length=1, max_length=40)

    @model_validator(mode="after")
    def validate_birth_semantics(self):
        year, month, day = (int(part) for part in self.birth_date.split("-"))
        if year < 1900 or year > datetime.now(UTC).year:
            raise ValueError("birth year must be between 1900 and the current year")
        if self.calendar_type == "solar":
            try:
                solar_date = date(year, month, day)
            except ValueError as exc:
                raise ValueError("birth_date is not a valid solar date") from exc
            if solar_date > datetime.now(UTC).date():
                raise ValueError("birth_date cannot be in the future")
        elif not 1 <= month <= 12 or not 1 <= day <= 30:
            raise ValueError("lunar birth month/day is outside 1-12/1-30")
        if (self.birth_hour is None) != (self.birth_minute is None):
            raise ValueError("birth_hour and birth_minute must both be known or unknown")
        if self.calendar_type == "solar" and self.is_leap_month:
            raise ValueError("is_leap_month is only valid for lunar input")
        return self


class BirthProfileConfirmIn(BirthProfileIn):
    expected_input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_chart_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ChartPreviewOut(BaseModel):
    input_fingerprint: str
    chart_fingerprint: str
    engine_version: str
    input_text: str
    solar_datetime: str
    pillars: list[str]
    calculation_basis: str


class BirthProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    gender: str
    calendar_type: str
    birth_date: str
    solar_birth_date: date
    birth_hour: int | None
    birth_minute: int | None
    birth_place: str
    is_leap_month: bool
    time_label: str
    last_edited_at: datetime | None
    next_edit_at: datetime | None = None
    can_edit: bool = True
    created_at: datetime
    updated_at: datetime


class BaziChartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    input_fingerprint: str
    chart_fingerprint: str
    engine_version: str
    chart: dict
    generated_at: datetime


class BirthProfileDetailOut(BaseModel):
    profile: BirthProfileOut
    chart: BaziChartOut
