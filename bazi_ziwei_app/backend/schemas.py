"""Strict public API schemas."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


ShortText = Annotated[str, Field(max_length=120)]
Fingerprint = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class BirthInputRequest(StrictModel):
    name: ShortText
    gender: Literal["男", "女", "male", "female"]
    calendar: Literal["solar", "lunar"]
    year: Annotated[int, Field(ge=1900, le=2100)]
    month: Annotated[int, Field(ge=1, le=12)]
    day: Annotated[int, Field(ge=1, le=31)]
    hour: Annotated[int, Field(ge=0, le=23)] | None = None
    minute: Annotated[int, Field(ge=0, le=59)] | None = None
    is_leap_month: bool = False
    birth_place: ShortText = ""
    time_label: ShortText = "精确时间"
    privacy_consent: bool = False

    @model_validator(mode="after")
    def validate_time_pair(self) -> "BirthInputRequest":
        if (self.hour is None) != (self.minute is None):
            raise ValueError("hour and minute must both be provided or both be null")
        if self.calendar == "solar" and self.is_leap_month:
            raise ValueError("is_leap_month is only valid for lunar calendar input")
        return self


class ConfirmChartRequest(BirthInputRequest):
    preview_id: Annotated[str, Field(min_length=16, max_length=80)]
    input_fingerprint: Fingerprint
    chart_fingerprint: Fingerprint


class HealthResponse(StrictModel):
    status: Literal["ok"]
    version: str
    runtime_mode: Literal["public", "local"]


class PreviewResponse(StrictModel):
    preview_id: str
    input_text: str
    solar_datetime: str
    pillars: tuple[str, str, str, str]
    calculation_basis: str
    input_fingerprint: str
    chart_fingerprint: str


class DayunFacts(StrictModel):
    direction: str
    start: str


class ClassificationFacts(StrictModel):
    classification: str
    evidence: list[str]


class StrengthFacts(ClassificationFacts):
    favorable_elements: list[str]
    unfavorable_elements: list[str]


class SummaryFacts(StrictModel):
    summary: str
    evidence: list[str]


class StabilitySignal(StrictModel):
    polarity: str
    fact: str
    explanation: str


class RelationshipFacts(SummaryFacts):
    stability_signals: list[StabilitySignal]


class CanonicalChartFacts(StrictModel):
    gender: str
    pillars: list[str]
    day_master: str
    hidden_stems: dict[str, list[str]]
    ten_gods: dict[str, object]
    element_counts: dict[str, float]
    time_mode: str
    pillar_basis: str
    dayun: DayunFacts
    strength: StrengthFacts
    pattern: ClassificationFacts
    wealth: SummaryFacts
    relationship: RelationshipFacts
    internal_rule_version: str
    rule_ids: list[str]
    current_context: dict[str, object]


class ConfirmChartResponse(StrictModel):
    chart_id: str
    chart_facts: CanonicalChartFacts
    chart_fingerprint: str


class GetChartResponse(StrictModel):
    chart_id: str
    chart_facts: CanonicalChartFacts
    chart_fingerprint: str


class ErrorDetail(StrictModel):
    code: str
    message: str
    fields: list[str] = Field(default_factory=list)


class ErrorResponse(StrictModel):
    error: ErrorDetail
    request_id: str
