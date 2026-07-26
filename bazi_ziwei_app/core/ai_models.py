"""Typed contracts for privacy-safe Bazi AI Q&A."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


QuestionCategory = Literal[
    "overview", "wealth", "career", "relationship", "timing", "family", "other"
]


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


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class RoutedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: QuestionCategory
    requires_timing: bool = False


class AIRequestContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=500)
    category: QuestionCategory
    requires_timing: bool
    chart_facts: dict[str, object]
    rule_evidence: list[dict[str, str]] = Field(min_length=1, max_length=24)
    history: list[ChatMessage] = Field(default_factory=list, max_length=6)


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
    reasoning_effort: str = "high"
    timeout_seconds: int = 30
    provider: str = "kimi"
    base_url: str = "https://api.moonshot.cn/v1"

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
        reasoning = _setting(source, "MINGSHU_AI_REASONING", "high").lower()
        if provider == "kimi":
            reasoning = "high" if reasoning == "medium" else reasoning
            if reasoning not in {"low", "high", "max"}:
                reasoning = "high"
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
            timeout_seconds=min(60, max(5, timeout)),
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
]


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sections: dict[str, str]
    chart_evidence: tuple[str, ...]
    rule_evidence: tuple[str, ...]
    timing_conditions: tuple[str, ...]
    practical_advice: tuple[str, ...]
    uncertainty: tuple[str, ...]
    source: Literal["cloud_validated", "local_rules"]
    degraded_reason: DegradationReason | None = None
