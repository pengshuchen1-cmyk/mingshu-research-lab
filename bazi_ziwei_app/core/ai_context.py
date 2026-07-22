"""Deterministic intent routing and de-identified AI context construction."""

from __future__ import annotations

import re
from typing import Mapping, Sequence

from core.ai_models import AIRequestContext, ChatMessage, RoutedQuestion
from core.bazi_rulebook import load_rulebook
from core.chart_facts import ChartFacts


CATEGORY_KEYWORDS = (
    ("wealth", ("财运", "赚钱", "收入", "投资", "创业", "借贷", "抵押")),
    ("career", ("工作", "事业", "职业", "升职", "岗位", "行业", "AI")),
    ("relationship", ("桃花", "姻缘", "婚姻", "对象", "感情", "伴侣", "结婚")),
    ("family", ("父母", "家庭", "原生家庭", "长辈")),
    ("overview", ("概括", "整体", "整个命盘", "八字怎么样", "强弱和格局")),
)
TIMING_KEYWORDS = ("今年", "明年", "后年", "什么时候", "流年", "流月", "每月", "未来")
DOMAIN_RULE_IDS = {
    "wealth": (
        "WEALTH-STAR-VISIBILITY", "WEALTH-CAPACITY",
        "WEALTH-REVENUE-RETENTION", "WEALTH-RISK-ADVICE",
    ),
    "career": ("STRENGTH-SEASON", "PATTERN-MONTH-QI", "WEALTH-CAPACITY"),
    "relationship": (
        "REL-SPOUSE-STAR", "REL-PALACE-STABILITY", "REL-STAGES", "REL-STATUS-UNKNOWN",
    ),
    "family": ("REL-PALACE-STABILITY", "SAFETY-NONDETERMINISTIC"),
    "overview": (
        "STRENGTH-SEASON", "PATTERN-MONTH-QI",
        "WEALTH-REVENUE-RETENTION", "REL-STAGES",
    ),
    "timing": ("DAYUN-DIRECTION", "DAYUN-START-DIV3"),
    "other": ("SAFETY-NONDETERMINISTIC",),
}


def _redact_personal_text(value: object) -> str:
    text = str(value or "").strip()
    patterns = (
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[邮箱已隐藏]"),
        (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[手机已隐藏]"),
        (r"(?<!\d)(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])(?!\d)", "[日期已隐藏]"),
        (r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)", "[时间已隐藏]"),
        (r"(?:姓名|称呼)\s*[:：]\s*[^\s，,。；;]+", "姓名：[已隐藏]"),
        (r"我叫[\u4e00-\u9fff]{2,5}", "我叫[已隐藏]"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def classify_question(question: str) -> RoutedQuestion:
    text = str(question or "").strip()
    requires_timing = any(keyword in text for keyword in TIMING_KEYWORDS) or bool(
        re.search(r"(?:19|20)\d{2}年", text)
    )
    category = None
    for candidate, keywords in CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            category = candidate
            break
    if category is None:
        category = "timing" if requires_timing else "other"
    return RoutedQuestion(category=category, requires_timing=requires_timing)


def _safe_history(history: Sequence[ChatMessage | Mapping[str, object]]) -> list[ChatMessage]:
    selected: list[ChatMessage] = []
    remaining = 6000
    for raw in reversed(history):
        if len(selected) >= 6 or remaining <= 0:
            break
        if isinstance(raw, ChatMessage):
            role, content = raw.role, raw.content
        else:
            role = str(raw.get("role", ""))
            content = str(raw.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        content = _redact_personal_text(content)
        content = content[-min(len(content), remaining, 4000):]
        selected.append(ChatMessage(role=role, content=content))
        remaining -= len(content)
    return list(reversed(selected))


def build_ai_context(
    facts: ChartFacts,
    question: str,
    history: Sequence[ChatMessage | Mapping[str, object]],
) -> AIRequestContext:
    routed = classify_question(question)
    raw = facts.to_dict()
    chart_facts: dict[str, object] = {
        "pillars": raw["pillars"],
        "gender": raw["gender"],
        "day_master": raw["day_master"],
        "hidden_stems": raw["hidden_stems"],
        "ten_gods": raw["ten_gods"],
        "element_counts": raw["element_counts"],
        "strength": raw["strength"],
        "pattern": raw["pattern"],
    }
    if routed.category in {"wealth", "career", "overview"}:
        chart_facts["wealth"] = raw["wealth"]
    if routed.category in {"relationship", "family", "overview"}:
        chart_facts["relationship"] = raw["relationship"]
    if routed.requires_timing or routed.category == "timing":
        chart_facts["dayun"] = raw["dayun"]
        chart_facts["current_context"] = raw["current_context"]

    selected_ids = list(facts.rule_ids)
    selected_ids.extend(DOMAIN_RULE_IDS[routed.category])
    if routed.requires_timing:
        selected_ids.extend(DOMAIN_RULE_IDS["timing"])
    selected_ids.extend(("SAFETY-NONDETERMINISTIC", "SAFETY-STATUS-UNKNOWN"))
    book = load_rulebook()
    rule_evidence = []
    for rule_id in dict.fromkeys(selected_ids):
        try:
            rule = book.by_id(rule_id)
        except KeyError:
            continue
        rule_evidence.append({"id": rule.id, "statement": rule.statement})

    return AIRequestContext(
        question=_redact_personal_text(question),
        category=routed.category,
        requires_timing=routed.requires_timing,
        chart_facts=chart_facts,
        rule_evidence=rule_evidence,
        history=_safe_history(history),
    )
