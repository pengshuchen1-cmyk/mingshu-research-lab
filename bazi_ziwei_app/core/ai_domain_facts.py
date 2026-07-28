"""Compile question-domain facts from existing local chart evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Callable

from core.ai_models import FactItem


DOMAIN_FACT_SPECS = {
    "career": (
        "day_master_strength",
        "pattern_analysis",
        "ten_gods",
        "wealth_analysis",
    ),
    "family": (
        "pillars.year",
        "pillars.month",
        "ten_gods.year",
        "ten_gods.month",
        "branch_relations",
    ),
    "health_advisory": (
        "five_elements",
        "seasonal_adjustment",
        "day_master_strength",
    ),
    "children": ("pillars.hour", "ten_gods.hour", "hidden_stems.hour"),
    "education": ("ten_gods", "day_master_strength", "pattern_analysis"),
    "relocation": ("branch_relations", "pillars", "day_master_strength"),
    "property": ("wealth_analysis", "day_master_strength", "five_elements"),
    "benefactor": ("ten_gods", "pattern_analysis", "branch_relations"),
}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _clip(value: object, limit: int = 500) -> str:
    text = _text(value)
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _item(domain: str, name: str, text: str) -> FactItem:
    return FactItem(
        id=f"domain.{domain}.{name}",
        kind="domain",
        text=_clip(text),
        source="domain",
    )


def _pillar_text(chart: Mapping[str, object], position: str) -> str:
    raw = _mapping(_mapping(chart.get("pillars")).get(position))
    return _text(raw.get("pillar"))


def _ten_god_text(chart: Mapping[str, object], position: str) -> str:
    raw = _mapping(_mapping(chart.get("ten_gods")).get(position))
    visible = _text(raw.get("gan"))
    hidden = [
        _text(item.get("ten_god"))
        for item in raw.get("hidden_stems", [])
        if isinstance(item, Mapping) and _text(item.get("ten_god"))
    ]
    parts = []
    if visible:
        parts.append(f"天干十神{visible}")
    if hidden:
        parts.append(f"藏干十神{'、'.join(hidden)}")
    return "；".join(parts)


def _ten_gods_summary(chart: Mapping[str, object]) -> str:
    entries = []
    for position in ("year", "month", "day", "hour"):
        value = _ten_god_text(chart, position)
        if value:
            entries.append(f"{position}柱{value}")
    return "；".join(entries)


def _strength_text(chart: Mapping[str, object]) -> str:
    strength = _mapping(chart.get("day_master_strength"))
    classification = _text(strength.get("strength"))
    favorable = [
        _text(item) for item in strength.get("favorable_elements", []) if _text(item)
    ]
    unfavorable = [
        _text(item) for item in strength.get("unfavorable_elements", []) if _text(item)
    ]
    parts = []
    if classification:
        parts.append(f"日主强弱为{classification}")
    if favorable:
        parts.append(f"喜用五行为{'、'.join(favorable)}")
    if unfavorable:
        parts.append(f"需审慎观察的五行为{'、'.join(unfavorable)}")
    return "；".join(parts)


def _pattern_text(chart: Mapping[str, object]) -> str:
    pattern = _mapping(chart.get("pattern_analysis"))
    return _text(pattern.get("plain_text") or pattern.get("public_text"))


def _wealth_text(chart: Mapping[str, object]) -> str:
    wealth = _mapping(chart.get("wealth_analysis"))
    return _text(wealth.get("public_text"))


def _elements_text(chart: Mapping[str, object]) -> str:
    elements = _mapping(chart.get("five_elements"))
    values = []
    for element, raw in elements.items():
        try:
            values.append((_text(element), float(raw)))
        except (TypeError, ValueError):
            continue
    values = [(element, value) for element, value in values if element]
    if not values:
        return ""
    counts = "、".join(f"{element}{value:g}" for element, value in values)
    highest_value = max(value for _, value in values)
    lowest_value = min(value for _, value in values)
    highest = [element for element, value in values if value == highest_value]
    lowest = [element for element, value in values if value == lowest_value]
    if highest_value == lowest_value:
        return f"本地五行计数为{counts}；各元素计数相同，无唯一偏盛或偏弱元素"
    extrema = []
    if len(highest) == 1:
        extrema.append(f"相对偏盛为{highest[0]}")
    else:
        extrema.append(f"最高值并列为{'、'.join(highest)}，无唯一偏盛元素")
    if len(lowest) == 1:
        extrema.append(f"相对偏弱为{lowest[0]}")
    else:
        extrema.append(f"最低值并列为{'、'.join(lowest)}，无唯一偏弱元素")
    return f"本地五行计数为{counts}；{'；'.join(extrema)}"


def _branch_relations_text(chart: Mapping[str, object]) -> str:
    value = chart.get("branch_relations")
    if isinstance(value, Mapping):
        entries = [
            f"{_text(key)}：{_text(item)}"
            for key, item in value.items()
            if _text(key) and _text(item)
        ]
        return "；".join(entries)
    if isinstance(value, list):
        entries = []
        for item in value:
            if isinstance(item, Mapping):
                text = _text(
                    item.get("text")
                    or item.get("fact")
                    or item.get("label")
                    or item.get("relation")
                )
            else:
                text = _text(item)
            if text:
                entries.append(text)
        return "；".join(entries)
    return ""


def _career_items(chart: dict) -> list[FactItem]:
    candidates = (
        ("strength", _strength_text(chart)),
        ("pattern", _pattern_text(chart)),
        ("ten_gods", _ten_gods_summary(chart)),
        ("wealth", _wealth_text(chart)),
    )
    return [
        _item("career", name, text)
        for name, text in candidates
        if text
    ]


def _family_items(chart: dict) -> list[FactItem]:
    year_pillar = _pillar_text(chart, "year")
    month_pillar = _pillar_text(chart, "month")
    candidates = (
        ("year_pillar", f"年柱为{year_pillar}" if year_pillar else ""),
        ("month_pillar", f"月柱为{month_pillar}" if month_pillar else ""),
        ("year_ten_gods", _ten_god_text(chart, "year")),
        ("month_ten_gods", _ten_god_text(chart, "month")),
        ("branch_relations", _branch_relations_text(chart)),
    )
    return [
        _item("family", name, text)
        for name, text in candidates
        if text
    ]


def _health_items(chart: dict) -> list[FactItem]:
    season = _mapping(chart.get("seasonal_adjustment"))
    candidates = (
        ("elements", _elements_text(chart)),
        ("season", _text(season.get("plain_text"))),
        ("strength", _strength_text(chart)),
    )
    items = [
        _item("health_advisory", name, text)
        for name, text in candidates
        if text
    ]
    items.append(
        _item(
            "health_advisory",
            "status_limit",
            "现实健康状态未知；以上仅用于五行、季节、作息与精力管理参考。",
        )
    )
    return items


def _children_items(chart: dict) -> list[FactItem]:
    hour_pillar = _pillar_text(chart, "hour")
    hidden = [
        _text(item.get("gan"))
        for item in _mapping(chart.get("hidden_stems")).get("hour", [])
        if isinstance(item, Mapping) and _text(item.get("gan"))
    ]
    candidates = (
        ("hour_pillar", f"时柱为{hour_pillar}" if hour_pillar else ""),
        ("hour_ten_gods", _ten_god_text(chart, "hour")),
        (
            "hour_hidden_stems",
            f"时支藏干为{'、'.join(hidden)}" if hidden else "",
        ),
    )
    items = [
        _item("children", name, text)
        for name, text in candidates
        if text
    ]
    items.append(
        _item(
            "children",
            "status_limit",
            "现实生育及子女状态未知；时柱与食伤结构只作命盘倾向参考。",
        )
    )
    return items


def _education_items(chart: dict) -> list[FactItem]:
    candidates = (
        ("ten_gods", _ten_gods_summary(chart)),
        ("strength", _strength_text(chart)),
        ("pattern", _pattern_text(chart)),
    )
    return [
        _item("education", name, text)
        for name, text in candidates
        if text
    ]


def _relocation_items(chart: dict) -> list[FactItem]:
    pillars = [
        _pillar_text(chart, position)
        for position in ("year", "month", "day", "hour")
    ]
    pillars = [pillar for pillar in pillars if pillar]
    candidates = (
        ("branch_relations", _branch_relations_text(chart)),
        ("pillars", f"四柱为{'、'.join(pillars)}" if pillars else ""),
        ("strength", _strength_text(chart)),
    )
    return [
        _item("relocation", name, text)
        for name, text in candidates
        if text
    ]


def _property_items(chart: dict) -> list[FactItem]:
    candidates = (
        ("wealth", _wealth_text(chart)),
        ("strength", _strength_text(chart)),
        ("elements", _elements_text(chart)),
    )
    return [
        _item("property", name, text)
        for name, text in candidates
        if text
    ]


def _benefactor_items(chart: dict) -> list[FactItem]:
    candidates = (
        ("ten_gods", _ten_gods_summary(chart)),
        ("pattern", _pattern_text(chart)),
        ("branch_relations", _branch_relations_text(chart)),
    )
    return [
        _item("benefactor", name, text)
        for name, text in candidates
        if text
    ]


def domain_fact_items(chart: dict, domain: str) -> list[FactItem]:
    builders: dict[str, Callable[[dict], list[FactItem]]] = {
        "career": _career_items,
        "family": _family_items,
        "health_advisory": _health_items,
        "children": _children_items,
        "education": _education_items,
        "relocation": _relocation_items,
        "property": _property_items,
        "benefactor": _benefactor_items,
    }
    return builders.get(domain, lambda _chart: [])(chart)
