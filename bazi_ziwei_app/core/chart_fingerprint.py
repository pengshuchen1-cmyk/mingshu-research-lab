"""命盘差异化特征指纹。"""

from __future__ import annotations

from core.bazi_constants import BRANCH_HIDDEN_STEMS, BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.ten_gods import get_hidden_stem_ten_gods


WEALTH_STARS = {"正财", "偏财"}
OFFICER_STARS = {"正官", "七杀"}
OUTPUT_STARS = {"食神", "伤官"}
RESOURCE_STARS = {"正印", "偏印"}
PEER_STARS = {"比肩", "劫财"}


def _sorted_keys_by_value(data: dict, reverse: bool = True) -> list[str]:
    """按数值排序并过滤空值。"""
    return [
        key
        for key, value in sorted(data.items(), key=lambda item: (-item[1], item[0]) if reverse else (item[1], item[0]))
        if value > 0
    ]


def _count_group(counts: dict, names: set[str]) -> int:
    """统计十神组数量。"""
    return int(sum(int(counts.get(name, 0)) for name in names))


def _ten_god_counts_from_facts(ten_gods: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pillar in ten_gods.values():
        if not isinstance(pillar, dict):
            continue
        visible = pillar.get("gan")
        if visible and visible != "日主":
            counts[str(visible)] = counts.get(str(visible), 0) + 1
        for item in pillar.get("hidden_stems", []) or []:
            if isinstance(item, dict) and item.get("ten_god"):
                name = str(item["ten_god"])
                counts[name] = counts.get(name, 0) + 1
    return counts


def _canonical_inputs(chart: dict) -> tuple[dict, dict, dict, str, list[str], list[str], str, list[str]]:
    """Read the attached immutable fact projection when present."""
    facts = chart.get("facts")
    if isinstance(facts, dict):
        raw_strength = facts.get("strength", {}) or {}
        strength = {
            "strength": raw_strength.get("classification", "暂无法判断"),
            "favorable_elements": list(raw_strength.get("favorable_elements", [])),
            "unfavorable_elements": list(raw_strength.get("unfavorable_elements", [])),
        }
        ten_gods = facts.get("ten_gods", {}) or {}
        pillars = facts.get("pillars", []) or []
        day_pillar = str(pillars[2]) if len(pillars) > 2 else ""
        day_branch = day_pillar[1:2]
        day_hidden = ten_gods.get("day", {}) if isinstance(ten_gods, dict) else {}
        hidden_names = [
            str(item.get("ten_god"))
            for item in (day_hidden.get("hidden_stems", []) or [])
            if isinstance(item, dict) and item.get("ten_god")
        ]
        return (
            strength,
            _ten_god_counts_from_facts(ten_gods),
            facts.get("element_counts", {}) or {},
            str(facts.get("day_master", "")),
            list(strength.get("favorable_elements", [])),
            list(strength.get("unfavorable_elements", [])),
            day_branch,
            hidden_names,
        )
    strength = chart.get("day_master_strength", {})
    day_master = chart.get("day_master", "")
    day_branch = chart.get("pillars", {}).get("day", {}).get("zhi", "")
    spouse_hidden = get_hidden_stem_ten_gods(day_master, day_branch)
    return (
        strength,
        chart.get("ten_god_counts", {}),
        chart.get("five_elements", {}),
        day_master,
        list(strength.get("favorable_elements", [])),
        list(strength.get("unfavorable_elements", [])),
        day_branch,
        [item.get("ten_god", "") for item in spouse_hidden if item.get("ten_god")],
    )


def _element_tags(top_elements: list[str], weak_elements: list[str]) -> list[str]:
    """生成五行摘要标签。"""
    tags: list[str] = []
    for element in top_elements[:2]:
        tags.append(f"{element}旺")
    for element in weak_elements[:2]:
        tags.append(f"{element}弱")
    return tags


def _career_tags(groups: dict, strength: str, favorable: list[str]) -> list[str]:
    """生成事业模式标签。"""
    tags: list[str] = []
    if groups["output"] >= 3:
        tags.append("输出创作型")
    if groups["wealth"] >= 3:
        tags.append("经营资源型")
    if groups["officer"] >= 3:
        tags.append("规则管理型")
    if groups["resource"] >= 3:
        tags.append("学习研究型")
    if groups["peer"] >= 3:
        tags.append("自主竞争型")
    if strength == "身弱":
        tags.append("平台借力型")
    elif strength == "身强":
        tags.append("主动开拓型")
    for element in favorable[:2]:
        tags.append(f"喜{element}发力")
    return tags or ["阶段积累型"]


def _wealth_tags(groups: dict, favorable: list[str], unfavorable: list[str]) -> list[str]:
    """生成财富模式标签。"""
    tags: list[str] = []
    if groups["wealth"] >= 3:
        tags.append("财星明显")
    if groups["output"] >= 3:
        tags.append("食伤生财")
    if groups["peer"] >= 3:
        tags.append("合伙分账敏感")
    if groups["officer"] >= 3:
        tags.append("职位制度收入")
    if groups["resource"] >= 3:
        tags.append("知识资质收入")
    if any(element in favorable for element in ["金", "水", "土", "火", "木"]):
        tags.append(f"喜用{'/'.join(favorable[:2])}")
    if any(element in unfavorable for element in ["金", "水", "土", "火", "木"]):
        tags.append(f"忌神{'/'.join(unfavorable[:2])}")
    return tags or ["稳健积累"]


def _love_tags(groups: dict, spouse_element: str, hidden_ten_gods: list[str]) -> list[str]:
    """生成关系模式标签。"""
    tags: list[str] = []
    if spouse_element:
        tags.append(f"夫妻宫{spouse_element}")
    if hidden_ten_gods:
        tags.append(f"夫妻宫藏{'/'.join(hidden_ten_gods[:2])}")
    if groups["peer"] >= 3:
        tags.append("自我边界强")
    if groups["output"] >= 3:
        tags.append("表达反馈强")
    if groups["officer"] >= 3:
        tags.append("责任压力强")
    if groups["wealth"] >= 3:
        tags.append("现实经营强")
    if groups["resource"] >= 3:
        tags.append("安全感需求强")
    return tags or ["关系渐进观察"]


def build_chart_fingerprint(chart: dict) -> dict:
    """
    提取命盘的核心差异特征，用于驱动报告个性化。
    """
    (
        strength_info,
        counts,
        five_elements,
        day_master,
        favorable,
        unfavorable,
        day_branch,
        spouse_hidden_ten_gods,
    ) = _canonical_inputs(chart)
    day_master_element = STEM_ELEMENTS.get(day_master, "")

    top_elements = _sorted_keys_by_value(five_elements, True)[:3]
    weak_elements = _sorted_keys_by_value(five_elements, False)[:3]
    top_ten_gods = _sorted_keys_by_value(counts, True)[:4]
    weak_ten_gods = [name for name in ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"] if counts.get(name, 0) == 0]

    groups = {
        "wealth": _count_group(counts, WEALTH_STARS),
        "officer": _count_group(counts, OFFICER_STARS),
        "output": _count_group(counts, OUTPUT_STARS),
        "resource": _count_group(counts, RESOURCE_STARS),
        "peer": _count_group(counts, PEER_STARS),
    }

    spouse_element = BRANCH_MAIN_ELEMENTS.get(day_branch, "")

    career_tags = _career_tags(groups, strength_info.get("strength", ""), favorable)
    wealth_tags = _wealth_tags(groups, favorable, unfavorable)
    love_tags = _love_tags(groups, spouse_element, spouse_hidden_ten_gods)
    summary_tags = [
        f"{day_master}{day_master_element}日主" if day_master else "日主待确认",
        strength_info.get("strength", "强弱待确认"),
        *_element_tags(top_elements, weak_elements),
        *top_ten_gods[:3],
    ]

    return {
        "day_master": day_master,
        "day_master_element": day_master_element,
        "strength": strength_info.get("strength", "暂无法判断"),
        "favorable_elements": favorable,
        "unfavorable_elements": unfavorable,
        "top_elements": top_elements,
        "weak_elements": weak_elements,
        "top_ten_gods": top_ten_gods,
        "weak_ten_gods": weak_ten_gods,
        "wealth_star_count": groups["wealth"],
        "officer_star_count": groups["officer"],
        "output_star_count": groups["output"],
        "resource_star_count": groups["resource"],
        "peer_star_count": groups["peer"],
        "has_strong_wealth": groups["wealth"] >= 3,
        "has_strong_officer_killing": groups["officer"] >= 3,
        "has_strong_output": groups["output"] >= 3,
        "has_strong_resource": groups["resource"] >= 3,
        "has_strong_peer": groups["peer"] >= 3,
        "day_branch": day_branch,
        "spouse_palace_element": spouse_element,
        "spouse_palace_hidden_ten_gods": spouse_hidden_ten_gods,
        "career_pattern_tags": career_tags,
        "wealth_pattern_tags": wealth_tags,
        "love_pattern_tags": love_tags,
        "chart_summary_tags": summary_tags,
    }
