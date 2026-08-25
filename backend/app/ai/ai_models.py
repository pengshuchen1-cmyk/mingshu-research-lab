"""Typed contracts for privacy-safe Bazi AI Q&A."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

QuestionCategory = Literal[
    "overview", "wealth", "career", "relationship", "timing", "family", "other"
]
QuestionDomain = Literal[
    "overview", "wealth", "career", "relationship", "family",
    "health_advisory", "children", "education", "relocation",
    "property", "benefactor", "timing",
]
AnswerDepth = Literal["direct", "single_year", "topic", "long_range", "monthly"]
TimeScopeKind = Literal[
    "none", "current_year", "target_year", "year_range",
    "age", "month_range", "dayun",
]
ProgressStage = Literal[
    "validating_scope", "resolving_question", "compiling_local_facts",
    "generating_cloud_answer", "validating_answer", "completed",
    "degraded", "rejected",
]


class ResolvedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    safe_question: str = Field(min_length=1, max_length=2000)
    domain: QuestionDomain
    subdomains: list[QuestionDomain] = Field(default_factory=list, max_length=4)
    follow_up_reference: str = Field(default="", max_length=120)
    time_scope: TimeScopeKind = "none"
    target_years: list[int] = Field(default_factory=list, max_length=60)
    target_months: list[Annotated[int, Field(ge=1, le=12)]] = Field(
        default_factory=list, max_length=12
    )
    age_values: list[Annotated[int, Field(ge=0, le=120)]] = Field(
        default_factory=list, max_length=4
    )
    age_mode: Literal["unspecified", "solar_age", "nominal_age"] = "unspecified"
    requested_depth: AnswerDepth = "direct"
    ambiguity: str = Field(default="", max_length=240)
    interpretation_receipt: str = Field(default="", max_length=240)
    out_of_scope: bool = False
    scope_reason: str = Field(default="", max_length=80)
    current_marriage_status_requested: bool = False


class DialogueSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: QuestionDomain = "overview"
    time_scope: TimeScopeKind = "none"
    requested_depth: AnswerDepth = "direct"
    target_years: list[int] = Field(default_factory=list, max_length=60)
    target_months: list[int] = Field(default_factory=list, max_length=12)
    current_marriage_status_requested: bool = False
    last_claim_ids: list[str] = Field(default_factory=list, max_length=60)
    constraints: list[str] = Field(default_factory=list, max_length=12)


@dataclass(frozen=True)
class RequestStart:
    accepted: bool
    request_id: str
    cached_answer: str = ""


class FactItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,79}$")
    kind: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)
    source: Literal["chart", "dayun", "year", "month", "domain", "rule"]


class FactPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolved: ResolvedQuestion
    facts: list[FactItem] = Field(min_length=1, max_length=240)
    rule_evidence: list[dict[str, str]] = Field(min_length=1, max_length=80)


class ClaimPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_.:-]{0,79}$")
    topic: str = Field(min_length=1, max_length=80)
    allowed_conclusion: str = Field(min_length=1, max_length=800)
    local_text: str = Field(min_length=1, max_length=1200)
    fact_ids: list[str] = Field(min_length=1, max_length=24)
    rule_ids: list[str] = Field(min_length=1, max_length=16)
    conditions: list[str] = Field(default_factory=list, max_length=8)
    uncertainty: list[str] = Field(default_factory=list, max_length=8)
    prohibited_expansion: list[str] = Field(default_factory=list, max_length=8)


class AnalysisPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolved: ResolvedQuestion
    claims: list[ClaimPlan] = Field(min_length=1, max_length=60)


class BaziAIAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    analysis_conclusion: str = Field(min_length=1, max_length=6000)
    chart_evidence: list[Annotated[str, Field(min_length=1)]] = Field(max_length=12)
    rule_evidence: list[Annotated[str, Field(min_length=1)]] = Field(max_length=12)
    timing_conditions: list[Annotated[str, Field(min_length=1)]] = Field(max_length=12)
    practical_advice: list[Annotated[str, Field(min_length=1)]] = Field(max_length=12)
    uncertainty_limitations: list[Annotated[str, Field(min_length=1)]] = Field(
        max_length=8,
    )


class CloudSegment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    claim_ids: list[str] = Field(min_length=1, max_length=8)
    text: str = Field(min_length=1, max_length=1600)


class CloudBaziAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments: list[CloudSegment] = Field(min_length=1, max_length=60)


@dataclass(frozen=True)
class CloudGeneration:
    analysis: CloudBaziAnalysis
    input_tokens: int = 0
    output_tokens: int = 0


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class RoutedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: QuestionCategory
    requires_timing: bool = False


class AIRequestContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    category: Union[QuestionCategory, QuestionDomain]
    requires_timing: bool
    chart_facts: dict[str, object]
    rule_evidence: list[dict[str, str]] = Field(min_length=1, max_length=80)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)
    resolved_question: Optional[ResolvedQuestion] = None
    fact_packet: Optional[FactPacket] = None
    analysis_plan: Optional[AnalysisPlan] = None
    current_marriage_status_requested: bool = False


def _setting(
    secrets: Mapping[str, object],
    name: str,
    default: str = "",
) -> str:
    environment_value = os.environ.get(name)
    if environment_value is not None and environment_value.strip():
        return environment_value.strip()
    secret_value = secrets.get(name, default)
    return str(secret_value or default).strip()


@dataclass(frozen=True)
class AIConfig:
    api_key: str = field(repr=False)
    enabled: bool
    model: str = "kimi-k3"
    reasoning_effort: str = "low"
    timeout_seconds: int = 30
    provider: str = "kimi"
    base_url: str = "https://api.moonshot.cn/v1"
    per_session_per_minute: int = 3
    per_session_daily_requests: int = 30
    daily_token_budget: int = 500_000
    max_concurrent_requests: int = 4

    @classmethod
    def from_environment(
        cls,
        secrets: Mapping[str, object] | None = None,
    ) -> "AIConfig":
        source = secrets if secrets is not None else {}
        provider = _setting(source, "MINGSHU_AI_PROVIDER", "kimi").lower()
        key_name = "OPENAI_API_KEY" if provider == "openai" else "MOONSHOT_API_KEY"
        api_key = _setting(source, key_name)
        default_model = "gpt-5.6-sol" if provider == "openai" else "kimi-k3"
        default_base_url = (
            "https://api.openai.com/v1"
            if provider == "openai"
            else "https://api.moonshot.cn/v1"
        )
        model = _setting(source, "MINGSHU_AI_MODEL", default_model)
        default_reasoning = "medium" if provider == "openai" else "low"
        reasoning = _setting(
            source,
            "MINGSHU_AI_REASONING",
            default_reasoning,
        ).lower()
        if provider == "kimi":
            reasoning = "low" if reasoning == "medium" else reasoning
            if reasoning not in {"low", "high", "max"}:
                reasoning = "low"
        elif reasoning not in {"low", "medium", "high"}:
            reasoning = "medium"
        try:
            timeout = int(_setting(source, "MINGSHU_AI_TIMEOUT_SECONDS", "30"))
        except ValueError:
            timeout = 30
        return cls(
            api_key=api_key,
            enabled=bool(api_key) and provider in {"kimi", "openai"},
            model=model,
            reasoning_effort=reasoning,
            timeout_seconds=min(90, max(5, timeout)),
            provider=provider,
            base_url=_setting(source, "MINGSHU_AI_BASE_URL", default_base_url),
        )


DegradationReason = Literal[
    "missing_api_key",
    "insufficient_quota",
    "invalid_credentials",
    "rate_limited",
    "network_error",
    "timeout",
    "service_unavailable",
    "unparseable_response",
    "local_validation_failed",
    "daily_budget",
    "duplicate_request",
    "concurrency_limit",
]
RETRYABLE_DEGRADATION_REASONS = frozenset(
    {
        "rate_limited",
        "network_error",
        "timeout",
        "service_unavailable",
        "unparseable_response",
        "concurrency_limit",
    }
)


def is_retryable_degradation(reason: str | None) -> bool:
    return reason in RETRYABLE_DEGRADATION_REASONS


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sections: dict[str, str]
    chart_evidence: tuple[str, ...]
    rule_evidence: tuple[str, ...]
    timing_conditions: tuple[str, ...]
    practical_advice: tuple[str, ...]
    uncertainty: tuple[str, ...]
    source: Literal[
        "cloud_validated", "local_rules", "boundary", "clarification"
    ]
    degraded_reason: DegradationReason | None = None
    provider: Literal["kimi", "openai"] | None = None
    interpretation_receipt: str = ""
    retryable: bool = False
    request_id: str = ""
    violation_codes: tuple[str, ...] = ()
    input_tokens: int = 0
    output_tokens: int = 0
