"""Presentation helpers for adaptive Bazi answers."""

from __future__ import annotations

from core.ai_models import BaziAIAnswer


def render_adaptive_markdown(answer: BaziAIAnswer) -> str:
    return answer.analysis_conclusion.strip()


def render_structured_answer(answer: BaziAIAnswer) -> dict[str, str]:
    """Compatibility hook: new answers no longer expose fixed UI sections."""
    return {}


def render_structured_markdown(answer: BaziAIAnswer) -> str:
    return render_adaptive_markdown(answer)
