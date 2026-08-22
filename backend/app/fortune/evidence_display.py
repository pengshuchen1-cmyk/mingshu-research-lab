"""Convert internal monthly-event evidence into user-facing trigger labels."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

EVIDENCE_TYPE_COPY = {
    "ten_god": "流月十神主题被引动",
    "ten_god_group": "流月十神主题被引动",
    "favorable_relation": "五行喜忌关系提示需要留意",
    "element": "流月五行关系被引动",
    "element_in": "流月五行关系被引动",
    "element_strength": "流月五行关系被引动",
    "unfavorable_any": "五行喜忌关系提示需要留意",
    "day_master_element": "流月五行关系被引动",
    "group_count_at_least": "原局结构提供相关线索",
    "branch_in": "地支关系提示本月留意变化",
    "gender": "个人命盘条件提供相关线索",
    "month_index": "本月节奏位置触发相关提醒",
}

_NEUTRAL_EVIDENCE_TYPES = {"month_index"}
_INTERNAL_EVIDENCE_MARKERS = (
    "month_index",
    "period_id",
    "case_id",
    "pattern_id",
    "师傅原文",
    "样本编号",
)


def _clean_evidence_copy(value: object) -> str:
    """Accept short display copy while filtering internal identifiers."""
    if not isinstance(value, (str, int, float)):
        return ""
    text = " ".join(str(value).split())
    lowered = text.lower()
    if not text or any(marker in lowered for marker in _INTERNAL_EVIDENCE_MARKERS):
        return ""
    if re.search(r"\b20\d{2}_m\d", lowered):
        return ""
    return text[:120]


def _evidence_type_copy(evidence_type: str) -> str:
    """Translate an internal evidence type using the legacy page vocabulary."""
    if evidence_type in EVIDENCE_TYPE_COPY:
        return EVIDENCE_TYPE_COPY[evidence_type]
    if evidence_type.startswith(("is_", "activate_")):
        return "相关命盘主题被流月引动"
    if evidence_type == "clash_any" or evidence_type.startswith("clash_"):
        return "地支关系提示本月留意变化"
    return ""


def _readable_evidence_items(value: object) -> list[str]:
    """Recursively turn structured evidence into safe, readable labels."""
    if isinstance(value, Mapping):
        evidence_type = str(value.get("type") or "")
        fallback = _evidence_type_copy(evidence_type)
        if not fallback:
            return []
        if evidence_type in _NEUTRAL_EVIDENCE_TYPES:
            return [fallback]
        for key in ("label", "text", "reason"):
            copy = _clean_evidence_copy(value.get(key))
            if copy:
                return [copy]
        return [fallback]
    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for entry in value:
            items.extend(_readable_evidence_items(entry))
        return list(dict.fromkeys(items))
    return []


def _readable_trigger_items(value: object) -> list[str]:
    """Normalize an engine-provided trigger list when one already exists."""
    if isinstance(value, (list, tuple, set)):
        items = [_clean_evidence_copy(item) for item in value]
        return [item for item in dict.fromkeys(items) if item]
    item = _clean_evidence_copy(value)
    return [item] if item else []


def build_display_trigger_factors(event: Mapping[str, Any], limit: int = 3) -> list[str]:
    """Build the same trigger-factor list that the legacy monthly page displayed."""
    explicit_factors = event.get("trigger_factors")
    factors = (
        _readable_trigger_items(explicit_factors)
        if explicit_factors
        else _readable_evidence_items(event.get("evidence"))
    )
    return factors[:limit]
