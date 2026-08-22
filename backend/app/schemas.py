from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PhoneIn(BaseModel):
    phone: str


class VerifyIn(PhoneIn):
    code: str = Field(pattern=r"^\d{6}$")


class PhonePasswordIn(PhoneIn):
    password: str = Field(min_length=8, max_length=128, repr=False)


class PasswordRegisterIn(PhonePasswordIn):
    pass


class PasswordChangeIn(BaseModel):
    current_password: str | None = Field(default=None, min_length=8, max_length=128, repr=False)
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


class DailyGuidanceDetailsOut(BaseModel):
    colors: list[str]
    relaxation: str
    actions: list[str]


class DailyGuidanceOut(BaseModel):
    kind: Literal["daily_guidance"]
    is_personal: Literal[False]
    date: date
    day_pillar: str
    title: str
    element_theme: Literal["木", "火", "土", "金", "水"]
    wearing_colors: list[str]
    wearing_advice: str
    cautions: list[str]
    primary_action: str
    theme: str
    focus: str
    action: str
    reminder: str
    details: DailyGuidanceDetailsOut
    basis: str
    boundary_note: str


class YearlyGuidanceOut(BaseModel):
    kind: Literal["yearly_guidance"]
    is_personal: Literal[False]
    year: int
    title: str
    theme: str
    focus: str
    actions: list[str]
    basis: str
    boundary_note: str


class TodayGuidanceOut(BaseModel):
    timezone: Literal["Asia/Shanghai"]
    daily_guidance: DailyGuidanceOut | None
    yearly_guidance: YearlyGuidanceOut


class FortuneBranchRelationOut(BaseModel):
    type: str
    label: str
    target: str
    native_zhi: str
    year_zhi: str
    text: str


class FortuneEventOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_type: str
    label: str
    category: str
    score: float = Field(ge=0, le=100)
    probability_level: str | None = None
    trigger_count: int | None = None
    evidence: list[Any] = Field(default_factory=list)
    display_trigger_factors: list[str] = Field(
        default_factory=list,
        description="根据事件证据翻译、去重后得到的用户可读触发因素，最多三项",
    )
    reason: str | None = None
    advice: str


class PersonalMonthlyFortuneOut(BaseModel):
    month: int = Field(ge=1, le=12)
    month_name: str
    pillar: str
    gan: str
    zhi: str
    gan_element: str
    zhi_element: str
    ten_god: str
    relation_to_favorable: str
    branch_relations: list[FortuneBranchRelationOut]
    theme: str
    event_tags: list[str]
    event_tendency: str
    likely_events: list[str]
    career_text: str
    wealth_text: str
    relationship_text: str
    health_text: str
    risk_text: str
    advice_text: str
    suitable_actions: list[str]
    actions_to_avoid: list[str]
    basis: str
    source_ids: list[str]
    source_titles: list[str]
    top_events: list[FortuneEventOut]


class PersonalYearlyFortuneOut(BaseModel):
    year: int
    pillar: str
    gan: str
    zhi: str
    gan_element: str
    zhi_element: str
    ten_god: str
    branch_ten_god: str
    branch_relations: list[FortuneBranchRelationOut]
    relation_to_favorable: str
    overall_level: str
    keywords: list[str]
    annual_keywords: list[str]
    overall_text: str
    career_text: str
    wealth_text: str
    relationship_text: str
    health_text: str
    risk_text: str
    advice_text: str
    brief_text: str
    suitable_actions: list[str]
    actions_to_avoid: list[str]
    high_attention_months: list[str]
    opportunity_months: list[str]
    career_good_months: list[str]
    career_bad_months: list[str]
    wealth_good_months: list[str]
    wealth_bad_months: list[str]
    relationship_good_months: list[str]
    relationship_bad_months: list[str]
    peach_months: list[str]
    health_concerns: list[str]


class FortunePeriodOut(BaseModel):
    index: int
    pillar: str
    gan: str
    zhi: str
    start_age: int
    end_age: int
    start_year: int
    end_year: int
    start_date: str
    end_date: str


class FortuneLuckContextOut(BaseModel):
    available: bool
    direction: Literal["forward", "reverse"] | None
    direction_label: str | None
    start_text: str
    current_period: FortunePeriodOut | None


class PersonalFortuneOut(BaseModel):
    kind: Literal["personal_fortune"]
    is_personal: Literal[True]
    profile_id: str
    chart_fingerprint: str
    target_year: int
    fortune_engine_version: str
    generated_at: datetime
    luck_context: FortuneLuckContextOut
    yearly: PersonalYearlyFortuneOut
    monthly: list[PersonalMonthlyFortuneOut]
    boundary_note: str
