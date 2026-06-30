"""紫微斗数星曜组合匹配引擎。"""

from __future__ import annotations

from core.rule_engine import load_rules


def _normalize_pair(stars: list[str]) -> set[str]:
    return {star for star in stars if star}


def load_star_combination_rules() -> dict:
    """加载星曜组合规则。"""
    return load_rules("ziwei_star_combinations.json")


def match_star_combinations(stars: list[str], palace_name: str = "") -> list[dict]:
    """匹配同宫星曜组合。"""
    star_set = _normalize_pair(stars)
    if len(star_set) < 2:
        return []

    matched = []
    rules = load_star_combination_rules()
    for rule in rules.get("rules", []):
        required = _normalize_pair(rule.get("stars", []))
        if required and required.issubset(star_set):
            item = dict(rule)
            item["palace_name"] = palace_name
            item["match_scope"] = "同宫"
            suitable = item.get("suitable_palaces", [])
            if palace_name:
                if palace_name in suitable:
                    item["palace_interpretation"] = f"{item.get('title', '')}落在{palace_name}时，组合力量与本宫主题较贴合，可优先观察现实表现。"
                else:
                    item["palace_interpretation"] = f"{item.get('title', '')}落在{palace_name}时，仍可参考组合含义，但需要结合本宫主题转译。"
            else:
                item["palace_interpretation"] = "未指定宫位，先按同宫组合的一般含义观察。"
            matched.append(item)
    return matched


def format_star_combination(rule: dict, sihua: list[str] | None = None) -> str:
    """把组合规则格式化为普通用户可读文案。"""
    sihua = sihua or []
    strengths = "、".join(rule.get("strengths", [])[:3])
    risks = "、".join(rule.get("risks", [])[:3])
    examples = "；".join(rule.get("reality_examples", [])[:2])
    triggers = "、".join(rule.get("trigger_signals", [])[:3])
    sihua_text = f"四化提示：{'、'.join(sihua)}。" if sihua else "四化提示：本宫未见明显四化，先看长期模式。"
    return (
        f"星曜组合：{rule.get('title', '')}。"
        f"当前组合怎么看：{rule.get('plain_meaning', '')}"
        f"现实表现：{rule.get('real_world_view', '')}"
        f"落宫提示：{rule.get('palace_interpretation', '')}"
        f"现实例子：{examples}。"
        f"触发信号：{triggers}。"
        f"优势：{strengths}。"
        f"风险：{risks}。"
        f"{sihua_text}"
        f"建议：{rule.get('advice', '')}"
        f"边界：{rule.get('boundary', '此组合仅供趋势参考。')}"
    )
