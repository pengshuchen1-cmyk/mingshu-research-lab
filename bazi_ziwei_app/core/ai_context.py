"""Deterministic intent routing and de-identified AI context construction."""

from __future__ import annotations

import re
from typing import Mapping, Sequence

from core.ai_models import AIRequestContext, ChatMessage, RoutedQuestion
from core.bazi_rulebook import load_rulebook
from core.bazi_constants import EARTHLY_BRANCHES, HEAVENLY_STEMS
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
CATEGORY_LABELS = {
    "overview": "命盘概览",
    "wealth": "财运",
    "career": "事业",
    "relationship": "姻缘婚姻",
    "timing": "时运",
    "family": "原生家庭",
    "other": "其他",
}


def _canonical_question(question: str, routed: RoutedQuestion) -> str:
    """Turn arbitrary customer prose into an allowlisted intent, never raw text."""
    text = str(question or "")
    parts = [f"问题类别：{CATEGORY_LABELS[routed.category]}"]
    parts.append(f"时间维度：{'是' if routed.requires_timing else '否'}")
    timing_text = re.sub(
        r"(?:19|20)\d{2}年\d{1,2}月\d{1,2}日(?:出生)?",
        "",
        text,
    )
    years = list(dict.fromkeys(re.findall(r"(?:19|20)\d{2}(?=年)", timing_text)))[:4]
    if years:
        parts.append("目标年份：" + "、".join(f"{year}年" for year in years))
    topic_flags = []
    if any(word in text for word in ("抵押", "借贷", "贷款", "杠杆")):
        topic_flags.append("抵押借贷风险")
    if "AI" in text.upper() or "人工智能" in text:
        topic_flags.append("AI行业")
    if (("现在" in text or "当前" in text) and any(word in text for word in ("结婚", "已婚"))):
        topic_flags.append("当前婚姻状态")
    if any(word in text for word in ("每月", "流月", "12个月")):
        topic_flags.append("逐月走势")
    if topic_flags:
        parts.append("安全主题：" + "、".join(topic_flags))
    return "；".join(parts)


def _target_year_facts(question: str) -> list[dict[str, object]]:
    """Extract explicit forecast years and calculate only their year pillars."""
    text = re.sub(
        r"(?:我是|本人)?\s*(?:19|20)\d{2}年(?:出生|生人)",
        "",
        str(question or ""),
    )
    years = list(dict.fromkeys(int(value) for value in re.findall(r"((?:19|20)\d{2})(?=年)", text)))[:4]
    return [
        {
            "year": year,
            "year_pillar": (
                HEAVENLY_STEMS[(year - 4) % 10]
                + EARTHLY_BRANCHES[(year - 4) % 12]
            ),
        }
        for year in years
    ]


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
        if role == "user":
            routed = classify_question(content)
            content = f"此前用户询问：{CATEGORY_LABELS[routed.category]}"
        else:
            content = "此前助手已提供过回答"
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
        chart_facts["target_years"] = _target_year_facts(question)

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
        question=_canonical_question(question, routed),
        category=routed.category,
        requires_timing=routed.requires_timing,
        chart_facts=chart_facts,
        rule_evidence=rule_evidence,
        history=_safe_history(history),
    )
