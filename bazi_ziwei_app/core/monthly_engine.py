"""流月分析。"""

from __future__ import annotations

import json
from pathlib import Path

from core.bazi_constants import BRANCH_MAIN_ELEMENTS, EARTHLY_BRANCHES, HEAVENLY_STEMS, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.report_diversity import build_chart_signature_text
from core.ten_gods import get_ten_god
from core.yearly_engine import TEN_GOD_THEMES
from report.narrative_engine import build_monthly_narrative


MONTH_NAMES = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]

TAG_MAP: dict[str, list[str]] = {
    "比肩": ["竞争增强", "团队摩擦", "合作边界"],
    "劫财": ["人情往来", "朋友求助", "合伙分账"],
    "食神": ["项目推进", "汇报展示", "感情升温"],
    "伤官": ["汇报展示", "合同文书", "关系摩擦"],
    "正财": ["财务整理", "客户回款", "伴侣沟通"],
    "偏财": ["偏财机会", "资源变现", "客户沟通"],
    "正官": ["上级压力", "合同文书", "岗位变化"],
    "七杀": ["竞争增强", "项目推进", "出行安全"],
    "正印": ["学习考试", "家庭事务", "睡眠作息"],
    "偏印": ["学习考试", "旧人联系", "腰肾疲劳"],
    "未知": ["项目推进", "财务整理", "睡眠作息"],
}

RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "monthly_event_rules.json"
SOURCE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "rules" / "source_registry.json"
_SOURCE_REGISTRY_CACHE: dict | None = None


def _load_source_registry() -> dict:
    """读取参考书注册表。"""
    global _SOURCE_REGISTRY_CACHE
    if _SOURCE_REGISTRY_CACHE is not None:
        return _SOURCE_REGISTRY_CACHE
    try:
        with open(SOURCE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            _SOURCE_REGISTRY_CACHE = json.load(f)
        return _SOURCE_REGISTRY_CACHE
    except Exception:
        _SOURCE_REGISTRY_CACHE = {}
        return _SOURCE_REGISTRY_CACHE


def _get_source_titles(source_ids: list[str]) -> list[str]:
    """根据 source_ids 返回可读书名列表。"""
    registry = _load_source_registry()
    return [registry[s]["title"] for s in source_ids if s in registry]


def _cycle_pillar(index: int) -> str:
    """按六十甲子循环生成干支。"""
    stem = HEAVENLY_STEMS[index % len(HEAVENLY_STEMS)]
    branch = EARTHLY_BRANCHES[index % len(EARTHLY_BRANCHES)]
    return f"{stem}{branch}"


def _fallback_month_pillar(target_year: int, month: int) -> str:
    """缺少日历库时生成简化月柱。"""
    return _cycle_pillar((target_year - 1984) * 12 + month + 1)


def _get_month_pillar(target_year: int, month: int) -> str:
    """获取目标月份的月柱。"""
    try:
        from lunar_python import Solar

        try:
            solar = Solar(target_year, month, 15, 12, 0, 0)
        except TypeError:
            solar = Solar.fromYmdHms(target_year, month, 15, 12, 0, 0)
        eight_char = solar.getLunar().getEightChar()
        for method_name in ["getMonth", "getMonthInGanZhi"]:
            method = getattr(eight_char, method_name, None)
            if callable(method):
                value = method()
                if value:
                    return str(value)
        gan = getattr(eight_char, "getMonthGan", lambda: "")()
        zhi = getattr(eight_char, "getMonthZhi", lambda: "")()
        return f"{gan}{zhi}" if gan and zhi else _fallback_month_pillar(target_year, month)
    except Exception:
        return _fallback_month_pillar(target_year, month)


def _relation(elements: list[str], favorable: set[str], unfavorable: set[str]) -> str:
    """判断流月五行与喜忌的关系。"""
    score = 0
    has_favorable = False
    has_unfavorable = False
    for element in elements:
        if element in favorable:
            score += 1
            has_favorable = True
        if element in unfavorable:
            score -= 1
            has_unfavorable = True
    if score > 0:
        return "喜用相关"
    if score < 0:
        return "忌神相关"
    if has_favorable and has_unfavorable:
        return "喜忌混杂"
    return "平稳观察"


def _theme_text(ten_god: str) -> str:
    """生成月份主题。"""
    theme = TEN_GOD_THEMES.get(ten_god, TEN_GOD_THEMES["未知"])
    return str(theme["theme"])


def _career_text(ten_god: str, relation: str) -> str:
    """生成事业流月文案。"""
    if relation == "喜用相关":
        prefix = "本月适合主动推进"
    elif relation == "忌神相关":
        prefix = "本月建议放慢节奏"
    else:
        prefix = "本月适合稳步观察"
    if ten_god in {"正官", "七杀"}:
        return f"{prefix}，重点放在职责、规则、目标拆解和执行稳定度上。"
    if ten_god in {"食神", "伤官"}:
        return f"{prefix}，适合输出作品、表达观点、打磨技能和整理方法。"
    if ten_god in {"正印", "偏印"}:
        return f"{prefix}，适合学习、复盘、获取支持和补充专业体系。"
    return f"{prefix}，工作上重视沟通、边界和可落地的阶段成果。"


def _wealth_text(ten_god: str, relation: str) -> str:
    """生成财富流月文案。"""
    if ten_god in {"正财", "偏财"}:
        text = "财务方面更适合关注收入、预算、项目回报和资源交换。"
    elif ten_god in {"比肩", "劫财"}:
        text = "财务方面需要注意朋友、合作、同业相关的支出和分配边界。"
    else:
        text = "财务方面以稳健为主，适合减少冲动消费，保持现金流意识。"
    if relation == "忌神相关":
        return f"{text} 本月对成本和风险要更谨慎。"
    return text


def _relationship_text(ten_god: str) -> str:
    """生成关系流月文案。"""
    if ten_god in {"比肩", "劫财"}:
        return "关系方面互动较多，适合把期待、分工和边界说清楚。"
    if ten_god in {"食神", "伤官"}:
        return "关系方面表达欲较明显，适合真诚沟通，也要避免过度情绪化。"
    if ten_god in {"正官", "七杀"}:
        return "关系方面责任和压力感较突出，建议用稳定沟通替代猜测。"
    return "关系方面宜保持温和、耐心和现实观察。"


def _health_text(relation: str) -> str:
    """生成身心流月文案。"""
    if relation == "忌神相关":
        return "身心节奏方面注意休息、睡眠和压力释放，避免长期透支。"
    return "身心节奏方面适合建立规律作息，保持轻量运动和情绪复盘。"


def _load_event_rules() -> list[dict]:
    """读取流月事件规则。"""
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _unique(items: list[str], limit: int | None = None) -> list[str]:
    """保持顺序去重。"""
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result if limit is None else result[:limit]


def _match_event_rules(
    ten_god: str,
    elements: list[str],
    branch_relations: list[dict],
    rules: list[dict],
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """根据十神、五行和地支冲动匹配事件规则，返回 tag, text, advice, source_ids, basis。"""
    relation_labels = [item.get("label", "") for item in branch_relations]
    matched: list[tuple[int, dict]] = []
    for rule in rules:
        trigger = rule.get("trigger", {})
        score = 0
        if ten_god in trigger.get("ten_gods", []):
            score += 3
        score += len(set(elements) & set(trigger.get("elements", [])))
        if set(relation_labels) & set(trigger.get("branch_relations", [])):
            score += 2
        if score > 0:
            matched.append((score, rule))
    matched.sort(key=lambda item: item[0], reverse=True)
    selected = [rule for _, rule in matched[:6]]
    return (
        _unique([rule.get("tag", "") for rule in selected], 6),
        _unique([rule.get("text", "") for rule in selected], 6),
        _unique([rule.get("advice", "") for rule in selected], 6),
        _unique(sum([rule.get("source_ids", []) for rule in selected], []), 8),
        _unique([rule.get("basis", "") for rule in selected if rule.get("basis")], 4),
    )


def analyze_monthly_fortune(chart: dict, target_year: int) -> list[dict]:
    """
    返回目标年份 12 个月的流月分析。
    """
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    items = []
    rules = _load_event_rules()
    signature_lines = build_chart_signature_text(chart, "本盘流月差异依据").splitlines()
    chart_hint = "；".join(line.replace("。", "；").rstrip("；") for line in signature_lines[:7])
    for month in range(1, 13):
        pillar = _get_month_pillar(target_year, month)
        gan = pillar[0] if len(pillar) >= 1 else ""
        zhi = pillar[1] if len(pillar) >= 2 else ""
        gan_element = STEM_ELEMENTS.get(gan, "")
        zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
        ten_god = get_ten_god(day_master, gan) if gan else "未知"
        elements = [item for item in [gan_element, zhi_element] if item]
        relation = _relation(elements, favorable, unfavorable)
        branch_relations = analyze_year_branch_relations(chart, zhi)
        rule_tags, rule_events, rule_advices, rule_source_ids, rule_basis = _match_event_rules(ten_god, elements, branch_relations, rules)
        relation_tag = "阶段校准" if relation == "平稳观察" else relation
        tags = _unique(list(TAG_MAP.get(ten_god, TAG_MAP["未知"])) + rule_tags + [relation_tag], 6)
        if relation_tag not in tags:
            tags.append(relation_tag)
        source_titles = _get_source_titles(rule_source_ids)
        basis_text = "；".join(rule_basis) if rule_basis else ""
        seed = {
            "month": month,
            "month_name": MONTH_NAMES[month - 1],
            "pillar": pillar,
            "gan": gan,
            "zhi": zhi,
            "gan_element": gan_element,
            "zhi_element": zhi_element,
            "ten_god": ten_god,
            "event_tags": tags,
            "rule_events": rule_events,
            "rule_advices": rule_advices,
            "rule_source_ids": rule_source_ids,
            "source_titles": source_titles,
            "basis": basis_text,
        }
        narrative = build_monthly_narrative(chart, seed)
        items.append(
            {
                "month": month,
                "month_name": MONTH_NAMES[month - 1],
                "pillar": pillar,
                "gan": gan,
                "zhi": zhi,
                "gan_element": gan_element,
                "zhi_element": zhi_element,
                "ten_god": ten_god,
                "relation_to_favorable": relation,
                "branch_relations": branch_relations,
                "theme": narrative["theme"],
                "event_tags": tags,
                "event_tendency": f"{narrative['event_tendency']} {MONTH_NAMES[month - 1]}本盘触发依据：{chart_hint}。",
                "likely_events": [
                    *narrative["likely_events"],
                    f"{MONTH_NAMES[month - 1]}本盘校准：{chart_hint}",
                ],
                "career_text": narrative["career_text"],
                "wealth_text": narrative["wealth_text"],
                "relationship_text": narrative["relationship_text"],
                "health_text": narrative["health_text"],
                "risk_text": narrative["risk_text"],
                "advice_text": narrative["advice_text"],
                "suitable_actions": narrative["suitable_actions"],
                "actions_to_avoid": narrative["actions_to_avoid"],
                "basis": basis_text,
                "source_ids": rule_source_ids,
                "source_titles": source_titles,
            }
        )
    return items
