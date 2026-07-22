"""Typed contracts for privacy-safe Bazi AI Q&A."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


QuestionCategory = Literal[
    "overview", "wealth", "career", "relationship", "timing", "family", "other"
]


class BaziAIAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=1, max_length=4000)
    chart_evidence: list[str] = Field(min_length=1, max_length=12)
    rule_evidence: list[str] = Field(min_length=1, max_length=12)
    uncertainty: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=8)


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


@dataclass(frozen=True)
class AIConfig:
    api_key: str = field(repr=False)
    enabled: bool
    model: str = "gpt-5.6-sol"
    reasoning_effort: str = "medium"
    timeout_seconds: int = 30

    @classmethod
    def from_environment(cls) -> "AIConfig":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        model = os.environ.get("MINGSHU_AI_MODEL", "gpt-5.6-sol").strip() or "gpt-5.6-sol"
        reasoning = os.environ.get("MINGSHU_AI_REASONING", "medium").strip().lower()
        if reasoning not in {"low", "medium", "high"}:
            reasoning = "medium"
        try:
            timeout = int(os.environ.get("MINGSHU_AI_TIMEOUT_SECONDS", "30"))
        except ValueError:
            timeout = 30
        timeout = min(60, max(5, timeout))
        return cls(
            api_key=api_key,
            enabled=bool(api_key),
            model=model,
            reasoning_effort=reasoning,
            timeout_seconds=timeout,
        )


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    chart_evidence: tuple[str, ...]
    rule_evidence: tuple[str, ...]
    uncertainty: tuple[str, ...]
    cautions: tuple[str, ...]
    source: Literal["cloud_validated", "local_rules"]
