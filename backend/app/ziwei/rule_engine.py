"""JSON 规则库加载与匹配。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RULES_DIR = Path(__file__).resolve().parent / "rules"


def load_rules(rule_file: str) -> dict:
    """
    加载 JSON 规则库。
    """
    path = RULES_DIR / rule_file
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {"rules": [], "error": f"未找到规则文件：{rule_file}"}
    except json.JSONDecodeError as exc:
        return {"rules": [], "error": f"规则文件格式有误：{exc}"}
    if isinstance(data, list):
        return {"rules": data}
    if isinstance(data, dict):
        data.setdefault("rules", [])
        return data
    return {"rules": [], "error": "规则文件内容不是有效结构。"}


def _condition_matches(context: dict, condition: dict) -> bool:
    """判断单条规则条件是否命中。"""
    if not condition:
        return True
    for key, expected in condition.items():
        actual = context.get(key)
        if key.endswith("_contains"):
            source_key = key[: -len("_contains")]
            source = context.get(source_key, [])
            source_values = set(source if isinstance(source, list) else [source])
            expected_values = set(expected if isinstance(expected, list) else [expected])
            if not source_values & expected_values:
                return False
        elif isinstance(expected, list):
            actual_values = set(actual if isinstance(actual, list) else [actual])
            if not actual_values & set(expected):
                return False
        elif actual != expected:
            return False
    return True


def match_rules(context: dict, rules: dict) -> list[dict]:
    """
    根据上下文匹配规则。
    """
    matched = []
    for rule in rules.get("rules", []):
        if _condition_matches(context, rule.get("condition", {})):
            matched.append(rule)
    return matched


def build_context_from_chart(
    chart: dict,
    luck_data: dict | None = None,
    yearly_data: dict | None = None,
) -> dict:
    """
    根据命盘、大运、年度等数据生成规则匹配上下文。
    """
    strength = chart.get("day_master_strength", {})
    counts = chart.get("ten_god_counts", {})
    top_ten_gods = [name for name, count in counts.items() if count >= 1]
    top_elements = [
        element
        for element, score in sorted(chart.get("five_elements", {}).items(), key=lambda item: item[1], reverse=True)
        if score
    ]
    context: dict[str, Any] = {
        "day_master": chart.get("day_master", ""),
        "strength": strength.get("strength", ""),
        "favorable_elements": strength.get("favorable_elements", []),
        "unfavorable_elements": strength.get("unfavorable_elements", []),
        "ten_gods": top_ten_gods,
        "elements": top_elements,
        "has_wealth": counts.get("正财", 0) + counts.get("偏财", 0) > 0,
        "has_output": counts.get("食神", 0) + counts.get("伤官", 0) > 0,
        "has_authority": counts.get("正官", 0) + counts.get("七杀", 0) > 0,
        "has_resource": counts.get("正印", 0) + counts.get("偏印", 0) > 0,
        "has_peer": counts.get("比肩", 0) + counts.get("劫财", 0) > 0,
    }
    if luck_data:
        context["luck_available"] = bool(luck_data.get("available"))
    if yearly_data:
        context["year_relation"] = yearly_data.get("relation_to_favorable", "")
        context["year_ten_god"] = yearly_data.get("ten_god", "")
        context["annual_keywords"] = yearly_data.get("annual_keywords", [])
    return context
