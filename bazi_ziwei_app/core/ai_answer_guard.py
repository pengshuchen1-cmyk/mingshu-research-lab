"""Local factual and language guard for model-generated Bazi answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from core.ai_models import AIRequestContext, BaziAIAnswer


DETERMINISTIC_PHRASES = (
    "一定会", "注定", "百分之百", "必然离婚", "肯定发财",
    "保证成功", "抵押房子一定能成",
)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STRENGTH_TERMS = ("身强", "身弱", "中和", "从旺", "从弱")


@dataclass(frozen=True)
class GuardResult:
    accepted: bool
    violations: tuple[str, ...]


def _bigrams(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text)
    return {compact[index:index + 2] for index in range(max(0, len(compact) - 1))}


def validate_ai_answer(answer: BaziAIAnswer, context: AIRequestContext) -> GuardResult:
    combined = "。".join(
        [answer.answer, *answer.chart_evidence, *answer.rule_evidence]
    )
    violations: list[str] = []
    if any(phrase in combined for phrase in DETERMINISTIC_PHRASES):
        violations.append("deterministic_claim")

    authorized_pillars = set(context.chart_facts.get("pillars", []))
    mentioned_pillars = set(re.findall(f"[{STEMS}][{BRANCHES}]", combined))
    rule_text = "。".join(item["statement"] for item in context.rule_evidence)
    unauthorized = {
        pillar for pillar in mentioned_pillars
        if pillar not in authorized_pillars and pillar not in rule_text
    }
    day_master = str(context.chart_facts.get("day_master", ""))
    mentioned_day_masters = set(re.findall(f"([{STEMS}])日主", combined))
    if unauthorized or any(stem != day_master for stem in mentioned_day_masters):
        violations.append("chart_fact_contradiction")

    strength = context.chart_facts.get("strength", {})
    if isinstance(strength, dict):
        expected_strength = str(strength.get("classification", ""))
        mentioned_strength = {term for term in STRENGTH_TERMS if term in combined}
        if mentioned_strength and expected_strength not in mentioned_strength:
            violations.append("strength_contradiction")

    chart_payload = json.dumps(context.chart_facts, ensure_ascii=False)
    if not all(_bigrams(item) & _bigrams(chart_payload) for item in answer.chart_evidence):
        violations.append("unmapped_chart_evidence")
    if not all(_bigrams(item) & _bigrams(rule_text) for item in answer.rule_evidence):
        violations.append("unmapped_rule_evidence")

    unique = tuple(dict.fromkeys(violations))
    return GuardResult(accepted=not unique, violations=unique)
