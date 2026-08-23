"""Schemas for migrated chart interpretation, reports, Ziwei and AI APIs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChartInterpretationOut(BaseModel):
    """Combined deterministic interpretation of one stored Bazi chart."""

    profile_id: str
    chart_fingerprint: str
    chart_type: dict[str, Any]
    basic_report: dict[str, Any]
    life_assessment: dict[str, Any]
    life_overview: dict[str, Any]
    five_elements: dict[str, Any]
    useful_god: dict[str, Any]


class LuckCyclesOut(BaseModel):
    """Qiyun basis, ten complete Dayun periods and future annual trends."""

    profile_id: str
    chart_fingerprint: str
    available: bool
    direction: Literal["forward", "reverse"] | None = None
    direction_label: str | None = None
    start_age: int | None = None
    start_year: int | None = None
    start_month: int | None = None
    start_day: int | None = None
    start_text: str = ""
    dayun_basis: dict[str, Any] = Field(default_factory=dict)
    dayun_list: list[dict[str, Any]] = Field(default_factory=list)
    yearly_list: list[dict[str, Any]] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)


class SixtyJiaziEntryOut(BaseModel):
    """One enriched stem-branch knowledge entry."""

    model_config = ConfigDict(extra="allow")

    index: int
    pillar: str
    gan: str
    zhi: str
    gan_element: str
    zhi_element: str
    nayin: str


class SixtyJiaziListOut(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[SixtyJiaziEntryOut]


class ChartSixtyJiaziOut(BaseModel):
    profile_id: str
    chart_fingerprint: str
    pillar_cards: list[dict[str, Any]]
    nayin_comparison: dict[str, Any]


class SpecialReportOut(BaseModel):
    profile_id: str
    chart_fingerprint: str
    report_type: Literal["career", "wealth", "love"]
    report: dict[str, Any]


class CompatibilityIn(BaseModel):
    profile_id_1: str = Field(description="当前用户名下的第一个命理档案 ID")
    profile_id_2: str = Field(description="当前用户名下的第二个命理档案 ID")

    @model_validator(mode="after")
    def profiles_must_differ(self):
        if self.profile_id_1 == self.profile_id_2:
            raise ValueError("profile_id_1 and profile_id_2 must be different")
        return self


class CompatibilityOut(BaseModel):
    profile_id_1: str
    profile_id_2: str
    chart_fingerprint_1: str
    chart_fingerprint_2: str
    result: dict[str, Any]


class ZiweiOut(BaseModel):
    profile_id: str
    chart_fingerprint: str
    chart: dict[str, Any]
    life_card: dict[str, Any]
    report: dict[str, Any]


class AIChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AIQuestionIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[AIChatMessageIn] = Field(default_factory=list, max_length=10)


class AIQuestionOut(BaseModel):
    profile_id: str
    chart_fingerprint: str
    mode: Literal["local", "cloud"]
    answer: str
    structured_answer: dict[str, Any]
    degradation_reason: str | None = None
    boundary_note: str
