"""Local factual and language guard for model-generated Bazi answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from core.ai_intent import (
    CURRENT_MARRIAGE_DISCLAIMER,
    is_current_marriage_question,
)
from core.ai_models import AIRequestContext, BaziAIAnswer


DETERMINISTIC_PHRASES = (
    "一定会", "注定", "百分之百", "必然离婚", "肯定发财",
    "保证成功", "抵押房子一定能成",
)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STRENGTH_TERMS = ("身强", "身弱", "中和", "从旺", "从弱")
PATTERN_TERMS = (
    "正官格", "七杀格", "正印格", "偏印格", "食神格", "伤官格",
    "正财格", "偏财格", "比肩格", "劫财格", "建禄格", "月刃格", "从旺格", "从弱格",
)
WEALTH_ELEMENT_BY_DAY_ELEMENT = {
    "木": "土", "火": "金", "土": "水", "金": "木", "水": "火",
}
_CURRENT_MARRIAGE_PREDICATE = re.compile(
    r"(?:"
    r"婚姻(?:登记)?(?:状态|状况)(?:为|是)(?:已婚|未婚)"
    r"|(?:属于|是|处于|仍是)(?:已婚|未婚)(?:人士|状态)?"
    r"|(?:已经结婚|结婚了|没有结婚|尚未结婚|仍未结婚)"
    r"|(?:有|无|没有)配偶"
    r"|(?:处于|仍处于|进入|维持)婚姻关系"
    r")"
)
_CURRENT_MARRIAGE_TENDENCY = re.compile(
    r"(?:更?偏向|倾向于?|大概率|很可能|较可能|可能|或许|未必|"
    r"不一定|不像)(?:认为|是|为)?[^，,。；;！？!?\r\n]{0,8}"
    r"(?:已经结婚|结婚|已婚|未婚|有配偶|无配偶|处于婚姻关系)"
)
_CLAUSE_SPLIT = re.compile(r"[，,。；;！？!?\r\n]+")


@dataclass(frozen=True)
class GuardResult:
    accepted: bool
    violations: tuple[str, ...]


def _string_facts(value: object) -> set[str]:
    values: set[str] = set()
    if isinstance(value, str):
        if len(value.strip()) >= 2:
            values.add(value.strip())
    elif isinstance(value, dict):
        for item in value.values():
            values.update(_string_facts(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.update(_string_facts(item))
    return values


def _has_unqualified_current_marriage_claim(text: str) -> bool:
    for clause in _CLAUSE_SPLIT.split(text):
        if not _CURRENT_MARRIAGE_PREDICATE.search(clause):
            continue
        if not _CURRENT_MARRIAGE_TENDENCY.search(clause):
            return True
    return False


def validate_ai_answer(answer: BaziAIAnswer, context: AIRequestContext) -> GuardResult:
    combined = "。".join(
        [
            answer.analysis_conclusion,
            *answer.chart_evidence,
            *answer.rule_evidence,
            *answer.timing_conditions,
            *answer.practical_advice,
            *answer.uncertainty_limitations,
        ]
    )
    violations: list[str] = []
    if any(phrase in combined for phrase in DETERMINISTIC_PHRASES):
        violations.append("deterministic_claim")
    current_marriage_question = (
        context.category == "relationship"
        and is_current_marriage_question(context.question)
    )
    if current_marriage_question and (
        not answer.analysis_conclusion.strip().startswith(
            CURRENT_MARRIAGE_DISCLAIMER
        )
        or _has_unqualified_current_marriage_claim(combined)
    ):
        violations.append("current_marriage_status_claim")

    chart_payload = json.dumps(context.chart_facts, ensure_ascii=False)
    authorized_pillars = set(re.findall(f"[{STEMS}][{BRANCHES}]", chart_payload))
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

    expected_gender = str(context.chart_facts.get("gender", ""))
    mentioned_genders = {term for term in ("男命", "女命") if term in combined}
    expected_gender_term = "女命" if expected_gender == "female" else "男命"
    if mentioned_genders and mentioned_genders != {expected_gender_term}:
        violations.append("gender_contradiction")

    pattern = context.chart_facts.get("pattern", {})
    expected_pattern = str(pattern.get("classification", "")) if isinstance(pattern, dict) else str(pattern)
    mentioned_patterns = {term for term in PATTERN_TERMS if term in combined}
    if mentioned_patterns and any(term not in expected_pattern for term in mentioned_patterns):
        violations.append("pattern_contradiction")

    try:
        from core.bazi_constants import STEM_ELEMENTS

        wealth_element = WEALTH_ELEMENT_BY_DAY_ELEMENT.get(STEM_ELEMENTS.get(day_master, ""), "")
    except Exception:
        wealth_element = ""
    claimed_wealth_elements = {
        value
        for match in re.findall(
            r"财星(?:的?五行)?(?:为|是|属)([木火土金水])(?:也为([木火土金水]))?",
            combined,
        )
        for value in match
        if value
    }
    if claimed_wealth_elements and claimed_wealth_elements != {wealth_element}:
        violations.append("wealth_element_contradiction")

    spouse_claims = {
        value
        for match in re.findall(
            r"(?:配偶星|妻星|夫星)(?:为|是|属)(财星|官杀|官星|印星|食伤|比劫)"
            r"(?:也为(财星|官杀|官星|印星|食伤|比劫))?",
            combined,
        )
        for value in match
        if value
    }
    spouse_claims.update(
        re.findall(r"以(财星|官杀|官星|印星|食伤|比劫)为(?:配偶星|妻星|夫星)", combined)
    )
    spouse_claims = {"官杀" if value == "官星" else value for value in spouse_claims}
    expected_spouse = "官杀" if expected_gender == "female" else "财星"
    wrong_relation_label = (
        ("妻星" in combined and expected_gender == "female")
        or ("夫星" in combined and expected_gender == "male")
    )
    if wrong_relation_label or (spouse_claims and spouse_claims != {expected_spouse}):
        violations.append("spouse_star_contradiction")

    strength = context.chart_facts.get("strength", {})
    if isinstance(strength, dict):
        expected_strength = str(strength.get("classification", ""))
        mentioned_strength = {term for term in STRENGTH_TERMS if term in combined}
        if mentioned_strength and mentioned_strength != {expected_strength}:
            violations.append("strength_contradiction")

    authorized_facts = _string_facts(context.chart_facts)
    authorized_facts.update(authorized_pillars)
    if day_master:
        authorized_facts.add(f"{day_master}日主")
    if isinstance(strength, dict) and strength.get("classification"):
        authorized_facts.add(str(strength["classification"]))
    if any(not item.strip() for item in answer.chart_evidence) or not all(
        any(fact in item or item in fact for fact in authorized_facts)
        for item in answer.chart_evidence
    ):
        violations.append("unmapped_chart_evidence")
    rule_statements = [item["statement"] for item in context.rule_evidence]
    if any(not item.strip() for item in answer.rule_evidence) or not all(
        any(statement in item or item in statement for statement in rule_statements)
        for item in answer.rule_evidence
    ):
        violations.append("unmapped_rule_evidence")

    unique = tuple(dict.fromkeys(violations))
    return GuardResult(accepted=not unique, violations=unique)
