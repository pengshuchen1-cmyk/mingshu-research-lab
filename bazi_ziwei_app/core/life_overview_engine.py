"""
命盘总体结论引擎 — v1.1-A2

综合四柱、五行、十神、藏干、日主强弱、命局类型、大运背景等信息，
生成财富格局、桃花感情、健康稳定度、事业发展、整体格局的综合评价。

输出包含 scores、evidence、source_ids、source_titles，
每条结论都基于命盘真实数据，不写绝对化断言。

参考来源：渊海子平、三命通会、子平真诠、穷通宝鉴、滴天髓阐微、命理探源、神峰通考
"""

from __future__ import annotations

import json
from pathlib import Path

from core.bazi_constants import (
    BRANCH_MAIN_ELEMENTS,
    STEM_ELEMENTS,
    CONTROLLING,
    GENERATING,
)
from core.chart_fingerprint import build_chart_fingerprint
from core.chart_type import classify_chart
from core.report_diversity import build_chart_signature_text
from core.romance_star_engine import detect_peach_blossom_stars

RULES_DIR = Path(__file__).resolve().parents[1] / "rules"
_SOURCE_REGISTRY_CACHE: dict | None = None


def _load_source_registry() -> dict:
    global _SOURCE_REGISTRY_CACHE
    if _SOURCE_REGISTRY_CACHE is not None:
        return _SOURCE_REGISTRY_CACHE
    try:
        path = RULES_DIR / "source_registry.json"
        with open(path, "r", encoding="utf-8") as f:
            _SOURCE_REGISTRY_CACHE = json.load(f)
        return _SOURCE_REGISTRY_CACHE
    except Exception:
        _SOURCE_REGISTRY_CACHE = {}
        return _SOURCE_REGISTRY_CACHE


def _source_titles(source_ids: list[str]) -> list[str]:
    reg = _load_source_registry()
    return [reg[s]["title"] for s in source_ids if s in reg]


def _load_rules(name: str) -> list[dict]:
    path = RULES_DIR / name
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("rules", [])
    except Exception:
        return []


def _get_ten_god_groups(counts: dict) -> dict[str, int]:
    return {
        "wealth": counts.get("正财", 0) + counts.get("偏财", 0),
        "officer": counts.get("正官", 0) + counts.get("七杀", 0),
        "output": counts.get("食神", 0) + counts.get("伤官", 0),
        "resource": counts.get("正印", 0) + counts.get("偏印", 0),
        "peer": counts.get("比肩", 0) + counts.get("劫财", 0),
    }


def _get_element_strength(five_elements: dict) -> dict[str, str]:
    if not five_elements:
        return {}
    total = sum(float(v) for v in five_elements.values()) or 1
    result = {}
    for elem, score in five_elements.items():
        pct = float(score) / total * 100
        result[elem] = "偏旺" if pct >= 30 else "偏弱" if pct < 10 else "适中"
    return result


def _day_zhi_clashed(chart: dict) -> bool:
    """检查日支是否与其他地支相冲。"""
    pillars = chart.get("pillars", {})
    day_zhi = pillars.get("day", {}).get("zhi", "")
    if not day_zhi:
        return False
    clash_map = {"子":"午","丑":"未","寅":"申","卯":"酉","辰":"戌","巳":"亥",
                  "午":"子","未":"丑","申":"寅","酉":"卯","戌":"辰","亥":"巳"}
    target = clash_map.get(day_zhi, "")
    if not target:
        return False
    for key in ("year", "month", "hour"):
        if pillars.get(key, {}).get("zhi", "") == target:
            return True
    return False


def _spouse_element_relation(chart: dict, favorable: set, unfavorable: set) -> tuple[bool, bool, str]:
    """判断夫妻宫五行喜忌关系。"""
    day_zhi = chart.get("pillars", {}).get("day", {}).get("zhi", "")
    element = BRANCH_MAIN_ELEMENTS.get(day_zhi, "")
    if not element:
        return False, False, ""
    return element in favorable, element in unfavorable, element


def _has_special_combination(chart: dict, name: str) -> bool:
    """判断是否包含特殊组合。"""
    try:
        ct = classify_chart(chart)
        return name in ct.get("special_combinations", [])
    except Exception:
        return False


def _score_wealth(chart: dict, fp: dict, groups: dict) -> tuple[int, list[str]]:
    """计算财富评分（0-100）。"""
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")
    wealth_el_map = {"甲":"土","乙":"土","丙":"金","丁":"金","戊":"水","己":"水","庚":"木","辛":"木","壬":"火","癸":"火"}
    wealth_el = wealth_el_map.get(day_master, "")

    score = 50
    reasons = []

    # 财星数量
    score += groups["wealth"] * 8
    if groups["wealth"] >= 3:
        reasons.append("财星数量较多")
    elif groups["wealth"] >= 1:
        reasons.append("有财星透出")

    # 食伤生财
    if _has_special_combination(chart, "食神生财"):
        score += 15
        reasons.append("食神生财")

    # 杀印相生
    if _has_special_combination(chart, "杀印相生"):
        score += 8
        reasons.append("杀印相生")

    # 财星喜忌
    if wealth_el in favorable:
        score += 12
        reasons.append("财星为喜用")
    elif wealth_el in unfavorable:
        score -= 10
        reasons.append("财星为忌神")

    # 身强能担财
    s = strength.get("strength", "")
    if s == "身强" and groups["wealth"] >= 2:
        score += 10
        reasons.append("身强能担财")
    elif s == "身弱" and groups["wealth"] >= 2:
        score -= 8
        reasons.append("财多身弱")

    # 比劫制财
    if groups["peer"] >= 3 and groups["wealth"] >= 2:
        score -= 6
        reasons.append("比劫制财需注意")

    return max(0, min(100, score)), reasons


def _score_romance(chart: dict, fp: dict, groups: dict) -> tuple[int, list[str]]:
    """计算感情评分（0-100）。"""
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    peach = detect_peach_blossom_stars(chart)
    profile = chart.get("profile", {})
    gender = profile.get("gender", "")

    score = 50
    reasons = []

    # 桃花星
    score += peach["peach_count"] * 10
    if peach["peach_count"] >= 1:
        reasons.append(f"桃花星{peach['peach_count']}处")

    # 配偶星
    if gender == "女":
        spouse_score = groups["officer"] * 8
        if groups["officer"] >= 2:
            reasons.append("官杀明显")
        elif groups["officer"] == 0:
            spouse_score -= 5
            reasons.append("配偶星不显")
    elif gender == "男":
        spouse_score = groups["wealth"] * 8
        if groups["wealth"] >= 2:
            reasons.append("财星明显")
        elif groups["wealth"] == 0:
            spouse_score -= 5
            reasons.append("妻星不显")
    else:
        spouse_score = 0
    score += spouse_score

    # 夫妻宫喜忌
    fav, unfav, el = _spouse_element_relation(chart, favorable, set())
    if fav:
        score += 10
        reasons.append("夫妻宫为喜用")
    else:
        sp_uf, _, _ = _spouse_element_relation(chart, set(), strength.get("unfavorable_elements", []))
        if sp_uf:
            score -= 8
            reasons.append("夫妻宫为忌神")

    # 日支逢冲
    if _day_zhi_clashed(chart):
        score -= 8
        reasons.append("夫妻宫逢冲")

    # 食伤表达
    if groups["output"] >= 3:
        score += 6
        reasons.append("表达力较强")

    # 比劫自我
    if groups["peer"] >= 3:
        score -= 3
        reasons.append("自我边界强")

    return max(0, min(100, score)), reasons


def _score_health(chart: dict, fp: dict) -> tuple[int, list[str]]:
    """计算健康稳定度评分（0-100）。"""
    strength = chart.get("day_master_strength", {})
    five_elements = chart.get("five_elements", {})
    s = strength.get("strength", "")

    score = 65
    reasons = []

    # 日主强弱
    if s == "身强":
        score += 12
        reasons.append("日主强旺")
    elif s == "身弱":
        score -= 10
        reasons.append("日主偏弱")

    # 五行完整度
    present = [e for e, v in five_elements.items() if float(v) > 0]
    missing = 5 - len(present)
    if missing <= 1:
        score += 8
        reasons.append("五行较全")
    elif missing >= 3:
        score -= 10
        reasons.append("五行缺失较多")

    # 过旺五行减分
    el_strength = _get_element_strength(five_elements)
    strong = [e for e, st in el_strength.items() if st == "偏旺"]
    score -= len(strong) * 5
    if strong:
        reasons.append(f"{'/'.join(strong)}偏旺")

    # 官杀压力
    groups = _get_ten_god_groups(chart.get("ten_god_counts", {}))
    if groups["officer"] >= 3:
        score -= 6
        reasons.append("官杀压力偏大")

    return max(0, min(100, score)), reasons


def _score_career(chart: dict, fp: dict, groups: dict) -> tuple[int, list[str]]:
    """计算事业发展评分（0-100）。"""
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))

    score = 50
    reasons = []

    # 日主强弱
    s = strength.get("strength", "")
    if s == "身强":
        score += 10
        reasons.append("身强主动性强")
    elif s == "身弱":
        score -= 5
        reasons.append("身弱需借力")

    # 十神配置
    max_group = max(groups, key=groups.get)
    max_val = groups[max_group]
    if max_val >= 3:
        score += 10
        type_names = {"wealth": "财星", "officer": "官杀", "output": "食伤", "resource": "印星", "peer": "比劫"}
        reasons.append(f"{type_names.get(max_group, '')}突出")

    # 喜用五行
    if favorable:
        score += 6
        reasons.append("有喜用助力")

    # 特殊组合
    if _has_special_combination(chart, "杀印相生"):
        score += 12
        reasons.append("杀印相生贵格")
    if _has_special_combination(chart, "食神生财"):
        score += 10
        reasons.append("食神生财")

    return max(0, min(100, score)), reasons


def _format_level(score: int) -> str:
    if score >= 80:
        return "偏强"
    elif score >= 65:
        return "中上"
    elif score >= 45:
        return "中等"
    elif score >= 30:
        return "需经营"
    else:
        return "波动较大"


def _bounded_score(base: int, sub_scores: dict[str, int], deductions: list[tuple[str, int]]) -> int:
    total = base + sum(sub_scores.values()) - sum(abs(v) for _, v in deductions)
    return max(0, min(100, int(round(total))))


def _wealth_element(day_master: str) -> str:
    return {"甲":"土","乙":"土","丙":"金","丁":"金","戊":"水","己":"水","庚":"木","辛":"木","壬":"火","癸":"火"}.get(day_master, "")


def _score_detail_wealth(chart: dict, groups: dict, favorable: set, unfavorable: set) -> dict:
    s = chart.get("day_master_strength", {}).get("strength", "")
    wealth_el = _wealth_element(chart.get("day_master", ""))
    sub = {
        "wealth_star_strength": min(24, groups["wealth"] * 7),
        "wealth_star_position": 12 if groups["wealth"] >= 2 else 4 if groups["wealth"] else 0,
        "favorable_support": 14 if wealth_el in favorable else -8 if wealth_el in unfavorable else 2,
        "output_generates_wealth": min(16, groups["output"] * 5) if groups["wealth"] else min(8, groups["output"] * 3),
        "capacity_to_hold_wealth": 10 if s == "身强" and groups["wealth"] >= 2 else -10 if s == "身弱" and groups["wealth"] >= 2 else 2,
    }
    deductions = []
    if groups["peer"] >= 3 and groups["wealth"] >= 1:
        deductions.append(("比劫竞争财星", min(18, groups["peer"] * 4)))
    if wealth_el in unfavorable:
        deductions.append(("财星为忌带来消耗", 8))
    evidence = []
    if groups["wealth"]:
        evidence.append(f"财星数量{groups['wealth']}个")
    if groups["output"]:
        evidence.append(f"食伤数量{groups['output']}个，可观察技能变现")
    if wealth_el in favorable:
        evidence.append(f"财星五行{wealth_el}为喜用")
    elif wealth_el in unfavorable:
        evidence.append(f"财星五行{wealth_el}为忌神")
    return {
        "dimension": "wealth",
        "score": _bounded_score(34, sub, deductions),
        "level": _format_level(_bounded_score(34, sub, deductions)),
        "sub_scores": sub,
        "evidence": evidence or ["财星不突出，财富更依赖后天路径"],
        "deductions": [name for name, _ in deductions],
        "advice": ["把收入来源拆成稳定收入、项目收入和弹性收入三类管理。"],
    }


def _score_detail_romance(chart: dict, groups: dict, favorable: set) -> dict:
    profile = chart.get("profile", {}) or {}
    gender = profile.get("gender", "")
    peach = detect_peach_blossom_stars(chart)
    spouse_fav, spouse_unfav, spouse_el = _spouse_element_relation(
        chart, favorable, set(chart.get("day_master_strength", {}).get("unfavorable_elements", []))
    )
    spouse_group = groups["officer"] if gender == "女" else groups["wealth"] if gender == "男" else 0
    sub = {
        "spouse_star_visibility": min(24, spouse_group * 8),
        "spouse_palace_support": 12 if spouse_fav else -10 if spouse_unfav else 2,
        "peach_blossom_signal": min(18, peach.get("peach_count", 0) * 8),
        "expression_quality": min(12, groups["output"] * 4),
        "relationship_stability": -14 if _day_zhi_clashed(chart) else 8,
    }
    deductions = []
    if groups["peer"] >= 3:
        deductions.append(("自我边界较强", 8))
    if _day_zhi_clashed(chart):
        deductions.append(("夫妻宫逢冲", 12))
    evidence = [
        f"夫妻宫五行为{spouse_el or '待确认'}",
        f"配偶星数量{spouse_group}个",
        f"桃花信号{peach.get('peach_count', 0)}处",
    ]
    score = _bounded_score(38, sub, deductions)
    return {
        "dimension": "romance",
        "score": score,
        "level": _format_level(score),
        "sub_scores": sub,
        "evidence": evidence,
        "deductions": [name for name, _ in deductions],
        "advice": ["把关系节奏、现实规划和沟通边界分开处理，避免只靠情绪推进。"],
    }


def _score_detail_health(chart: dict, groups: dict, elements: dict, el_labels: dict) -> dict:
    s = chart.get("day_master_strength", {}).get("strength", "")
    strong = [e for e, l in el_labels.items() if l == "偏旺"]
    weak = [e for e, l in el_labels.items() if l == "偏弱"]
    present = [e for e, v in elements.items() if float(v) > 0]
    missing = 5 - len(present)
    sub = {
        "day_master_recovery": 12 if s == "身强" else -10 if s == "身弱" else 4,
        "element_completeness": 14 if missing <= 1 else -14 if missing >= 3 else 4,
        "pressure_management": -min(16, groups["officer"] * 4),
        "output_consumption": -min(12, groups["output"] * 3),
        "resource_recovery": min(14, groups["resource"] * 4),
    }
    deductions = []
    if strong:
        deductions.append((f"{'/'.join(strong[:2])}偏旺", min(16, len(strong) * 6)))
    if weak:
        deductions.append((f"{'/'.join(weak[:2])}偏弱", min(12, len(weak) * 5)))
    score = _bounded_score(60, sub, deductions)
    return {
        "dimension": "health_stability",
        "score": score,
        "level": _format_level(score),
        "sub_scores": sub,
        "evidence": [f"日主{s}", f"偏旺元素：{'、'.join(strong) or '不明显'}", f"偏弱元素：{'、'.join(weak) or '不明显'}"],
        "deductions": [name for name, _ in deductions],
        "advice": ["健康部分只做五行状态参考，建议结合体检和专业医生意见。"],
    }


def _score_detail_career(chart: dict, groups: dict, favorable: set) -> dict:
    s = chart.get("day_master_strength", {}).get("strength", "")
    top_group = max(groups, key=groups.get)
    sub = {
        "dominant_ten_god_pattern": min(22, groups[top_group] * 6),
        "responsibility_and_rules": min(18, groups["officer"] * 5),
        "skill_and_expression": min(18, groups["output"] * 5),
        "platform_and_learning": min(16, groups["resource"] * 4),
        "initiative_capacity": 12 if s == "身强" else -8 if s == "身弱" else 4,
    }
    deductions = []
    if groups["peer"] >= 3 and groups["officer"] <= 1:
        deductions.append(("竞争强于组织承接", 10))
    if groups["officer"] >= 3 and s == "身弱":
        deductions.append(("压力目标偏重", 12))
    score = _bounded_score(36, sub, deductions)
    return {
        "dimension": "career",
        "score": score,
        "level": _format_level(score),
        "sub_scores": sub,
        "evidence": [f"最强十神组：{top_group}{groups[top_group]}个", f"日主{s}", f"喜用：{'、'.join(favorable) or '需结合运势'}"],
        "deductions": [name for name, _ in deductions],
        "advice": ["先确认自己适合靠规则、技能、资源、经营还是平台发力，再安排年度动作。"],
    }


def _extra_score_details(groups: dict, details: dict) -> dict:
    learning = max(25, min(100, 38 + groups["resource"] * 10 + groups["output"] * 4))
    social = max(25, min(100, 40 + groups["peer"] * 8 + groups["wealth"] * 3 - max(0, groups["peer"] - 3) * 8))
    risk_control = max(20, min(100, 78 - groups["peer"] * 5 - groups["officer"] * 4 + groups["resource"] * 3))
    pace = int(round((details["wealth"]["score"] + details["romance"]["score"] + details["health_stability"]["score"] + details["career"]["score"]) / 4))
    return {
        "learning_growth": {"dimension": "learning_growth", "score": learning, "level": _format_level(learning), "sub_scores": {"resource_support": groups["resource"] * 10, "output_practice": groups["output"] * 4}, "evidence": [f"印星{groups['resource']}个", f"食伤{groups['output']}个"], "deductions": [], "advice": ["适合把学习转成证书、作品或可复用方法。"]},
        "social_resources": {"dimension": "social_resources", "score": social, "level": _format_level(social), "sub_scores": {"peer_network": groups["peer"] * 8, "wealth_connection": groups["wealth"] * 3}, "evidence": [f"比劫{groups['peer']}个", f"财星{groups['wealth']}个"], "deductions": ["比劫过旺时人情消耗增加"] if groups["peer"] >= 4 else [], "advice": ["社交资源要分清合作、朋友和人情请托。"]},
        "risk_control": {"dimension": "risk_control", "score": risk_control, "level": _format_level(risk_control), "sub_scores": {"resource_buffer": groups["resource"] * 3}, "evidence": [f"官杀{groups['officer']}个", f"比劫{groups['peer']}个"], "deductions": ["压力与人情同时明显"] if groups["peer"] and groups["officer"] else [], "advice": ["风险控制优先看合同、现金流、身体恢复和关系边界。"]},
        "overall_pace": {"dimension": "overall_pace", "score": pace, "level": _format_level(pace), "sub_scores": {"four_core_average": pace}, "evidence": ["综合财富、感情、健康、事业四项评分"], "deductions": [], "advice": ["把命盘评分当成节奏提示，不作为单一决策依据。"]},
    }


# ============================================================
# 公共入口
# ============================================================

def analyze_life_overview(chart: dict, luck_data: dict | None = None) -> dict:
    """
    生成命盘总体结论，包括财富、桃花、健康、事业、整体格局。
    """
    fp = build_chart_fingerprint(chart)
    groups = _get_ten_god_groups(chart.get("ten_god_counts", {}))
    strength = chart.get("day_master_strength", {})
    s = strength.get("strength", "中和")
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")
    favorable = list(strength.get("favorable_elements", []))
    unfavorable = list(strength.get("unfavorable_elements", []))
    elements = chart.get("five_elements", {})
    el_labels = _get_element_strength(elements)

    # ==== Scoring ====
    score_details = {
        "wealth": _score_detail_wealth(chart, groups, set(favorable), set(unfavorable)),
        "romance": _score_detail_romance(chart, groups, set(favorable)),
        "health_stability": _score_detail_health(chart, groups, elements, el_labels),
        "career": _score_detail_career(chart, groups, set(favorable)),
    }
    score_details.update(_extra_score_details(groups, score_details))
    w_score = score_details["wealth"]["score"]
    r_score = score_details["romance"]["score"]
    h_score = score_details["health_stability"]["score"]
    c_score = score_details["career"]["score"]
    w_reasons = score_details["wealth"]["evidence"] + score_details["wealth"].get("deductions", [])
    r_reasons = score_details["romance"]["evidence"] + score_details["romance"].get("deductions", [])
    h_reasons = score_details["health_stability"]["evidence"] + score_details["health_stability"].get("deductions", [])
    c_reasons = score_details["career"]["evidence"] + score_details["career"].get("deductions", [])
    overall = score_details["overall_pace"]["score"]

    # ==== Overall Pattern ====
    max_group = max(groups, key=groups.get) if max(groups.values()) > 0 else "output"
    group_name = {"wealth": "财星", "officer": "官杀", "output": "食伤", "resource": "印星", "peer": "比劫"}
    pattern = f"{day_master}{day_el}日主{s} · {group_name.get(max_group, '')}格局"
    strong_els = [e for e, l in el_labels.items() if l == "偏旺"]
    weak_els = [e for e, l in el_labels.items() if l == "偏弱"]

    # ==== Keywords ====
    keywords = [f"{day_master}日主", s]
    if strong_els:
        keywords.extend([f"{e}偏旺" for e in strong_els[:2]])
    if max(groups.values(), default=0) >= 3:
        keywords.append(f"{group_name.get(max_group, '')}格局")
    keywords.extend(favorable[:2])

    # ==== Key Strengths & Risks ====
    key_strengths = []
    key_risks = []
    if s == "身强":
        key_strengths.append("日主强旺，承压能力和主动性较好")
    if groups["wealth"] >= 2:
        key_strengths.append("财星有力，对收益和资源敏感")
    if groups["output"] >= 2:
        key_strengths.append("食伤充足，表达和创造能力较强")
    if _has_special_combination(chart, "杀印相生"):
        key_strengths.append("杀印相生，能将压力转化为成长动力")
    if _has_special_combination(chart, "食神生财"):
        key_strengths.append("食神生财，能力可转化为实际收益")
    if favorable:
        key_strengths.append(f"喜用{'、'.join(favorable[:2])}有补充空间")

    if s == "身弱":
        key_risks.append("日主偏弱，需要更多借力和休息")
    if groups["peer"] >= 3 and groups["wealth"] >= 2:
        key_risks.append("比劫制财，合作和竞争消耗需注意")
    if groups["officer"] >= 3:
        key_risks.append("官杀偏重，压力管理是长期课题")
    if _day_zhi_clashed(chart):
        key_risks.append("夫妻宫逢冲，亲密关系中需要更多耐心和协调")
    if len(strong_els) >= 2:
        key_risks.append(f"{'、'.join(strong_els)}偏旺，对应系统需要长期养护")

    # ==== Evidence ====
    evidence = []
    if groups["wealth"] >= 2:
        evidence.append(f"财星{groups['wealth']}个（正财{chart.get('ten_god_counts', {}).get('正财', 0)}/偏财{chart.get('ten_god_counts', {}).get('偏财', 0)}）")
    if groups["officer"] >= 2:
        evidence.append(f"官杀{groups['officer']}个（正官{chart.get('ten_god_counts', {}).get('正官', 0)}/七杀{chart.get('ten_god_counts', {}).get('七杀', 0)}）")
    if groups["output"] >= 2:
        evidence.append(f"食伤{groups['output']}个")
    if strong_els:
        evidence.append(f"五行：{'、'.join(strong_els)}偏旺")
    if weak_els:
        evidence.append(f"五行：{'、'.join(weak_els)}偏弱")
    peach = detect_peach_blossom_stars(chart)
    if peach["has_peach_blossom"]:
        evidence.append(f"桃花：{peach['peach_zhi']}出现在{'、'.join(peach['positions'])}")
    branches = chart.get("pillars", {}) or {}
    branch_line = "、".join(
        branches.get(pos, {}).get("zhi", "")
        for pos in ("year", "month", "day", "hour")
        if branches.get(pos, {}).get("zhi", "")
    )
    if branch_line:
        evidence.append(f"地支结构：{branch_line}")
    gender = (chart.get("profile", {}) or {}).get("gender", "")
    if gender == "男":
        evidence.append("男命关系取象侧重财星、现实经营与资源边界")
    elif gender == "女":
        evidence.append("女命关系取象侧重官杀、承诺压力与关系质量")
    evidence.append(f"日主{s}，净评分{strength.get('net_score', 0):+.1f}")

    # ==== Source IDs (deduplicated) ====
    src_ids = []
    for rule_name in ["wealth_overview_rules.json", "romance_overview_rules.json",
                       "health_overview_rules.json", "career_overview_rules.json"]:
        for r in _load_rules(rule_name):
            for sid in r.get("source_ids", []):
                if sid not in src_ids:
                    src_ids.append(sid)

    # ==== Build overview texts ====
    wealth_texts = _build_wealth_text(chart, fp, groups, favorable, unfavorable, w_score, w_reasons)
    romance_texts = _build_romance_text(chart, fp, groups, favorable, r_score, r_reasons, peach)
    health_texts = _build_health_text(chart, fp, groups, elements, el_labels, s, h_score, h_reasons)
    career_texts = _build_career_text(chart, fp, groups, favorable, c_score, c_reasons)
    signature_text = build_chart_signature_text(chart, "命盘总览差异依据")
    profile = chart.get("profile", {}) or {}
    profile_key = (
        f"{profile.get('name', '')}｜{profile.get('gender', '')}｜"
        f"{profile.get('birth_date', '')}｜{profile.get('birth_hour', '')}:"
        f"{profile.get('birth_minute', '')}｜{profile.get('birth_place', '')}"
    )

    return {
        "overall_pattern": pattern,
        "overall_summary": (
            f"{profile_key}。{pattern}，整体{_format_level(overall)}。{keyword_summary(keywords)}\n"
            f"{signature_text}"
        ),
        "life_keywords": keywords,
        "wealth_overview": wealth_texts,
        "romance_overview": romance_texts,
        "health_overview": health_texts,
        "career_overview": career_texts,
        "scores": {
            "wealth": w_score,
            "romance": r_score,
            "health_stability": h_score,
            "career": c_score,
            "learning_growth": score_details["learning_growth"]["score"],
            "social_resources": score_details["social_resources"]["score"],
            "risk_control": score_details["risk_control"]["score"],
            "overall_pace": score_details["overall_pace"]["score"],
            "overall_balance": overall,
        },
        "score_details": score_details,
        "key_strengths": key_strengths,
        "key_risks": key_risks,
        "long_term_advice": [
            "建议把命盘结构作为自我观察的辅助工具，每月回顾和记录关键变化。",
            "年度运程和流月分析可以帮助判断每个阶段的发力点和风险点。",
            "重大决策（换工作、投资、婚恋、迁居）建议多角度评估后再行动。",
            "持续关注五行调候对应的身体系统和作息习惯的长期养护。",
        ],
        "evidence": evidence,
        "source_ids": src_ids,
        "source_titles": _source_titles(src_ids),
    }


def keyword_summary(keywords: list[str]) -> str:
    return f"核心关键词：{'、'.join(keywords[:5])}。"


# ============================================================
# 各维度详情构建
# ============================================================

def _element_role(element: str, favorable: list | set, unfavorable: list | set) -> str:
    if element in set(favorable):
        return "喜用"
    if element in set(unfavorable):
        return "忌神"
    return "中性"


def _visible_pillar_signature(chart: dict) -> str:
    pillars = chart.get("pillars", {}) or {}
    line = "/".join(
        pillars.get(pos, {}).get("pillar", "")
        for pos in ("year", "month", "day", "hour")
        if pillars.get(pos, {}).get("pillar", "")
    )
    return f"四柱{line}；" if line else ""


def _visible_wealth_basis(chart: dict, groups: dict, favorable: list, unfavorable: list) -> str:
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")
    strength = chart.get("day_master_strength", {}).get("strength", "")
    wealth_el = _wealth_element(day_master)
    role = _element_role(wealth_el, favorable, unfavorable)
    return (
        f"{_visible_pillar_signature(chart)}"
        f"{day_master}{day_el}{strength}，财{groups['wealth']}食伤{groups['output']}比劫{groups['peer']}，"
        f"财星{wealth_el}{role}。"
    )


def _visible_romance_basis(chart: dict, groups: dict, peach: dict) -> str:
    signature = _build_relationship_signature(chart, groups, peach)
    return _visible_relationship_basis(signature)


def _visible_relationship_basis(signature: dict) -> str:
    palace = signature["spouse_palace"]
    spouse = signature["spouse_star"]
    return (
        f"夫妻宫{palace['branch']}{palace['element']}（{palace['role']}），"
        f"{spouse['basis']}{spouse['total']}个，桃花{signature['peach_blossom']['count']}处。"
    )


_RELATION_LABELS = {
    "clashes": {
        frozenset(("子", "午")): "子午冲",
        frozenset(("丑", "未")): "丑未冲",
        frozenset(("寅", "申")): "寅申冲",
        frozenset(("卯", "酉")): "卯酉冲",
        frozenset(("辰", "戌")): "辰戌冲",
        frozenset(("巳", "亥")): "巳亥冲",
    },
    "combinations": {
        frozenset(("子", "丑")): "子丑合",
        frozenset(("寅", "亥")): "寅亥合",
        frozenset(("卯", "戌")): "卯戌合",
        frozenset(("辰", "酉")): "辰酉合",
        frozenset(("巳", "申")): "巳申合",
        frozenset(("午", "未")): "午未合",
    },
}


def _spouse_palace_relations(chart: dict) -> dict[str, list[str]]:
    pillars = chart.get("pillars", {}) or {}
    day_zhi = pillars.get("day", {}).get("zhi", "")
    result: dict[str, list[str]] = {"clashes": [], "combinations": []}
    if not day_zhi:
        return result
    position_names = {"year": "年支", "month": "月支", "hour": "时支"}
    for position in ("year", "month", "hour"):
        other = pillars.get(position, {}).get("zhi", "")
        pair = frozenset((day_zhi, other))
        for relation_name, labels in _RELATION_LABELS.items():
            if pair in labels:
                result[relation_name].append(f"{position_names[position]}{labels[pair]}")
    return result


def _build_relationship_signature(chart: dict, groups: dict, peach: dict) -> dict:
    """将关系结论使用的命盘事实收拢为无姓名、无随机数的稳定签名。"""
    profile = chart.get("profile", {}) or {}
    gender = profile.get("gender", "")
    counts = chart.get("ten_god_counts", {}) or {}
    strength = chart.get("day_master_strength", {}) or {}
    favorable = list(strength.get("favorable_elements", []) or [])
    unfavorable = list(strength.get("unfavorable_elements", []) or [])
    day_zhi = (chart.get("pillars", {}) or {}).get("day", {}).get("zhi", "")
    spouse_element = BRANCH_MAIN_ELEMENTS.get(day_zhi, "")

    if gender == "男":
        spouse_star = {
            "basis": "财星",
            "total": counts.get("正财", 0) + counts.get("偏财", 0),
            "proper": counts.get("正财", 0),
            "indirect": counts.get("偏财", 0),
        }
    elif gender == "女":
        spouse_star = {
            "basis": "官杀",
            "total": counts.get("正官", 0) + counts.get("七杀", 0),
            "proper": counts.get("正官", 0),
            "indirect": counts.get("七杀", 0),
        }
    else:
        spouse_star = {"basis": "配偶星口径未设定", "total": 0, "proper": 0, "indirect": 0}

    return {
        "spouse_palace": {
            "branch": day_zhi,
            "element": spouse_element,
            "role": _element_role(spouse_element, favorable, unfavorable) if spouse_element else "待确认",
        },
        "spouse_relations": _spouse_palace_relations(chart),
        "spouse_star": spouse_star,
        "ten_god_support": {
            "output": groups.get("output", 0),
            "peer": groups.get("peer", 0),
            "resource": groups.get("resource", 0),
        },
        "peach_blossom": {
            "count": peach.get("peach_count", 0),
            "positions": list(peach.get("positions", []) or []),
        },
        "strength_preference": {
            "strength": strength.get("strength", ""),
        },
    }


def _relationship_base_outcome(signature: dict) -> tuple[str, str]:
    """按特异性由高到低选取关系核心画像与基础经营点。"""
    palace = signature["spouse_palace"]
    relations = signature["spouse_relations"]
    spouse = signature["spouse_star"]
    support = signature["ten_god_support"]
    peach = signature["peach_blossom"]

    if not palace["branch"]:
        return "关系信号待观察", "先补充出生信息，再结合现实互动观察"
    if relations["clashes"]:
        return "边界修复型", "先处理外部变化与相处边界"
    if relations["combinations"]:
        return "协同经营型", "把默契落实为分工与共同节奏"
    if peach["count"]:
        return "社交互动型", "辨别社交吸引与长期匹配"
    if support["output"] >= 3:
        return "表达协商型", "校准表达分寸与倾听反馈"
    if support["peer"] >= 3:
        return "独立边界型", "明确自主空间与共同责任"
    if palace["role"] == "忌神":
        return "现实磨合型", "降低关系消耗并建立可持续相处方式"
    if spouse["indirect"] >= 2 and spouse["indirect"] > spouse["proper"]:
        if spouse["basis"] == "财星":
            return "节奏筛选型", "在互动机会中核对现实投入与资源边界"
        return "节奏筛选型", "在互动机会中核对责任承诺与压力边界"
    if spouse["proper"] >= 2 and spouse["proper"] > spouse["indirect"]:
        return "承诺落实型", "把稳定意愿落实到时间与责任安排"
    if support["resource"] >= 3:
        return "慢热信任型", "用持续回应累积安全感"
    if palace["role"] == "喜用":
        return "支持共建型", "让关系支持成长，同时保留各自节奏"
    if spouse["total"] >= 2:
        return "现实规划型", "核对价值观、时间表与责任分工"
    return "关系信号待观察", "当前关系信号不集中，结合现实互动继续观察"


def _relationship_outcome(signature: dict) -> tuple[str, str]:
    core_portrait, primary_focus = _relationship_base_outcome(signature)
    if not signature["spouse_palace"]["branch"]:
        return core_portrait, primary_focus

    preference = signature["strength_preference"]
    strength = preference["strength"]
    if strength and strength != "中和":
        primary_focus = f"{primary_focus}；按日主{strength}安排推进与缓冲"
    return core_portrait, primary_focus


def _relationship_evidence(signature: dict) -> list[str]:
    palace = signature["spouse_palace"]
    spouse = signature["spouse_star"]
    if not palace["branch"]:
        return ["夫妻宫与配偶星信息暂不完整", "当前不据空缺信息推断关系类型"]

    evidence = [
        f"夫妻宫：{palace['branch']}（{palace['element']}，{palace['role']}）",
        f"{spouse['basis']}：正星{spouse['proper']}/偏星{spouse['indirect']}",
    ]
    drivers = []
    relations = signature["spouse_relations"]
    relation_items = relations["clashes"] + relations["combinations"]
    if relation_items:
        drivers.append(f"冲合：{'、'.join(relation_items)}")
    else:
        peach = signature["peach_blossom"]
        if peach["count"]:
            drivers.append(f"桃花：{peach['count']}处（{'、'.join(peach['positions'])}）")
    support = signature["ten_god_support"]
    if not drivers and (support["output"] >= 3 or support["peer"] >= 3 or support["resource"] >= 3):
        drivers.append(
            f"十神辅助：食伤{support['output']}/比劫{support['peer']}/印星{support['resource']}"
        )
    strength = signature["strength_preference"]["strength"]
    if strength and strength != "中和":
        drivers.append(f"日主强弱：{strength}")
    evidence.extend(drivers[:2])
    return evidence


def _visible_health_basis(chart: dict, groups: dict, el_labels: dict, missing: list[str]) -> str:
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")
    strength = chart.get("day_master_strength", {}).get("strength", "")
    strong = [e for e, l in el_labels.items() if l == "偏旺"]
    weak = [e for e, l in el_labels.items() if l == "偏弱"]
    structure = []
    if strong:
        structure.append(f"{'、'.join(strong[:2])}旺")
    if weak:
        structure.append(f"{'、'.join(weak[:2])}弱")
    if missing:
        structure.append(f"{'、'.join(missing[:2])}缺")
    if not structure:
        structure.append("五行较均")
    return (
        f"{_visible_pillar_signature(chart)}"
        f"{day_master}{day_el}{strength}，{''.join(structure)}，"
        f"官杀{groups['officer']}食伤{groups['output']}。"
    )


def _wealth_archetypes(groups: dict, strength: str, favorable: list, unfavorable: list) -> list[str]:
    types = []
    if groups["wealth"] >= 3 and strength != "身强":
        types.append("现金流压力型")
    if groups["wealth"] >= 4:
        types.append("经营现金流型")
    if groups["output"] >= 3 and groups["wealth"] >= 2:
        types.append("内容流量型")
    if groups["wealth"] >= 2 and groups["output"] >= 1:
        types.append("项目回款型")
    if groups["peer"] >= 2 and groups["wealth"] >= 1:
        types.append("合伙分账型")
    if groups["peer"] >= 3:
        types.append("人情破耗型")
    if groups["output"] >= 2:
        types.append("技术输出型")
    if groups["officer"] >= 2 and groups["wealth"] >= 1:
        types.append("稳定工资型")
    if groups["resource"] >= 2 and groups["wealth"] >= 1:
        types.append("资源变现型")
    if groups["output"] >= 2 and groups["wealth"] >= 1:
        types.append("销售成交型")
    if groups["wealth"] >= 3 and strength != "身强":
        types.append("投资波动型")
    if groups["wealth"] >= 3 and strength == "身强":
        types.append("经营现金流型")
    if groups["resource"] >= 3:
        types.append("家庭资产型")
    if groups["wealth"] >= 2 and strength == "身弱":
        types.append("现金流压力型")
    deduped = []
    for item in types:
        if item not in deduped:
            deduped.append(item)
    return deduped or ["稳定工资型", "技术输出型"]


def _romance_archetypes(chart: dict, groups: dict, peach: dict) -> list[str]:
    signature = _build_relationship_signature(chart, groups, peach)
    core_portrait, _ = _relationship_outcome(signature)
    return [core_portrait]


def _health_archetypes(groups: dict, el_labels: dict, strength: str) -> list[str]:
    types = []
    if strength == "身弱" or groups["resource"] >= 2:
        types.append("睡眠恢复型")
    if el_labels.get("土") in ("偏旺", "偏弱"):
        types.append("脾胃消化型")
    if groups["officer"] >= 2:
        types.append("情绪压力型")
    if el_labels.get("木") in ("偏旺", "偏弱"):
        types.append("肝胆筋骨型")
    if el_labels.get("金") in ("偏旺", "偏弱"):
        types.append("呼吸皮肤型")
    if el_labels.get("水") in ("偏旺", "偏弱"):
        types.append("腰肾精力型")
    if groups["output"] >= 2 or groups["officer"] >= 3:
        types.append("过劳疲劳型")
    if el_labels.get("土") == "偏旺":
        types.append("湿气代谢型")
    if el_labels.get("火") == "偏旺":
        types.append("心火焦虑型")
    if strength == "身弱" or len([v for v in el_labels.values() if v != "适中"]) >= 3:
        types.append("体检复查型")
    return types or ["睡眠恢复型", "体检复查型"]


def _career_archetypes(groups: dict, strength: str) -> list[str]:
    types = []
    if groups["peer"] >= 3 or strength == "身强":
        types.append("独立发展型")
    if groups["peer"] >= 2:
        types.append("团队协作型")
    if groups["officer"] >= 3:
        types.append("职场晋升型")
    if groups["wealth"] >= 2 and groups["output"] >= 1:
        types.append("项目突破型")
    if groups["output"] >= 2:
        types.append("技术专业型")
    if groups["output"] >= 3:
        types.append("内容表达型")
    if groups["officer"] >= 2:
        types.append("管理责任型")
    if groups["wealth"] >= 3 and groups["peer"] >= 1:
        types.append("创业经营型")
    if groups["wealth"] >= 2:
        types.append("客户销售型")
    if groups["officer"] >= 1 and groups["output"] >= 1:
        types.append("合同文书型")
    if groups["resource"] >= 2 and groups["wealth"] >= 1:
        types.append("资源整合型")
    if groups["resource"] >= 3 or strength == "身弱":
        types.append("学习转型型")
    deduped = []
    for item in types:
        if item not in deduped:
            deduped.append(item)
    return deduped or ["技术专业型", "稳定积累型"]


WEALTH_ARCHETYPE_TEXT = {
    "稳定工资型": "收入更容易从固定岗位、制度平台和长期客户里慢慢沉淀",
    "项目回款型": "重点在项目节点、尾款确认、报价结算和阶段性收益",
    "资源变现型": "适合把人脉、资质、渠道或已有资源转成可计价服务",
    "销售成交型": "财富动作常落在客户转化、报价谈判和成交节奏",
    "投资波动型": "机会与波动并存，尤其要看承接能力和现金流缓冲",
    "合伙分账型": "收益容易牵涉朋友、同辈、合伙分配和账目边界",
    "技术输出型": "靠手艺、专业、经验、咨询或解决问题的能力变现",
    "内容流量型": "适合通过表达、作品、账号、传播和曝光形成收益入口",
    "经营现金流型": "更像经营型盘，关键在客流、库存、成本和持续回款",
    "家庭资产型": "资产、房产、家庭资源或长期配置对财富感影响较大",
    "人情破耗型": "钱容易被人情、请托、朋友往来和临时帮忙牵动",
    "现金流压力型": "机会不一定少，但节奏容易前后错位，需要先守周转",
}


ROMANCE_ARCHETYPE_TEXT = {
    "边界修复型": "外部变化或生活节奏容易触动关系，需要先修复边界与协作方式",
    "协同经营型": "互动中较容易形成默契，适合进一步明确共同节奏与责任分工",
    "社交互动型": "社交吸引信号较明显，适合区分短期好感与长期匹配",
    "表达协商型": "表达意愿较强，关系质量取决于能否同时保留倾听与反馈",
    "独立边界型": "自主意识较强，适合提前说清个人空间与共同责任",
    "现实磨合型": "亲密互动容易牵动现实消耗，需要用具体安排降低摩擦",
    "节奏筛选型": "互动机会与变化感较明显，适合放慢筛选并核对责任匹配",
    "承诺落实型": "稳定与责任信号较集中，适合把意愿落实为可执行安排",
    "慢热信任型": "关系更依赖持续回应与安全感积累，不必急于下结论",
    "支持共建型": "关系具备相互支持的条件，也要保留双方各自的成长节奏",
    "现实规划型": "关系议题较容易落到价值观、时间表与责任安排",
    "稳步了解型": "当前没有单一信号压倒其他因素，适合在持续互动中核对匹配度",
    "关系信号待观察": "现有信息不足以形成具体关系画像",
    "稳定陪伴型": "关系更重陪伴、照顾、信任和长期稳定感",
    "桃花社交型": "容易在社交场、活动、人情往来中出现互动信号",
    "旧人回流型": "旧关系、老朋友、过去的情绪议题容易再次被触碰",
    "慢热观察型": "进入关系前会先观察安全感、现实条件和相处节奏",
    "家庭介入型": "家庭意见、居住安排或现实责任会影响关系判断",
    "合作生情型": "关系可能从合作、同事、项目或共同目标中升温",
    "关系摩擦型": "关系里要特别注意语气、边界、旧账和情绪反复",
    "价值观磨合型": "钱、时间、家庭规划和未来目标是磨合重点",
    "远距离/节奏差型": "距离、作息、工作节奏不同，会影响亲密感",
    "婚姻规划型": "适合把感情落到房车、家庭、时间表和责任分工",
}


HEALTH_ARCHETYPE_TEXT = {
    "睡眠恢复型": "恢复力和睡眠质量是身体状态的第一观察点",
    "脾胃消化型": "饮食、消化、代谢和湿重感容易影响精神状态",
    "情绪压力型": "压力一上来，身体状态容易先通过情绪和紧绷感表现",
    "肝胆筋骨型": "筋骨舒展、运动疏泄和肝胆节奏值得长期关注",
    "呼吸皮肤型": "呼吸道、皮肤干敏、过敏和环境变化更需要留意",
    "腰肾精力型": "精力恢复、腰背状态和过度透支是重点",
    "过劳疲劳型": "忙起来容易靠意志硬撑，真正要防的是持续透支",
    "湿气代谢型": "困倦、沉重、代谢慢和饮食结构需要长期管理",
    "心火焦虑型": "焦躁、上火、睡浅和急迫感会更明显",
    "体检复查型": "适合把小信号早处理，用体检和复查降低不确定感",
}


CAREER_ARCHETYPE_TEXT = {
    "职场晋升型": "更适合在组织、职级、职责和考核体系里往上走",
    "项目突破型": "事业机会常藏在项目卡点、关键节点和阶段成果里",
    "技术专业型": "靠专业能力、工具方法和可复用经验建立竞争力",
    "内容表达型": "适合用表达、作品、传播和展示打开职业机会",
    "管理责任型": "承担责任、带团队、定规则会成为事业主线之一",
    "创业经营型": "适合看客户、成本、现金流和持续经营能力",
    "客户销售型": "客户沟通、成交转化和资源维护是重要抓手",
    "合同文书型": "流程、合同、审核、材料和制度细节会影响事业推进",
    "资源整合型": "能不能把人、平台、信息和项目串起来，是发展关键",
    "学习转型型": "学习、证书、训练和换赛道准备会带来机会",
    "团队协作型": "事业成败受同事、伙伴、分工和协作边界影响较大",
    "独立发展型": "更适合主动开路，形成自己的方法、客户或影响力",
}

def _build_wealth_text(chart: dict, fp: dict, groups: dict,
                       favorable: list, unfavorable: list,
                       score: int, reasons: list) -> dict:
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")
    gender = (chart.get("profile", {}) or {}).get("gender", "")
    ten_god_counts = chart.get("ten_god_counts", {})
    wealth_el_map = {"甲":"土","乙":"土","丙":"金","丁":"金","戊":"水","己":"水","庚":"木","辛":"木","壬":"火","癸":"火"}
    wealth_el = wealth_el_map.get(day_master, "")
    s = chart.get("day_master_strength", {}).get("strength", "")

    types = _wealth_archetypes(groups, s, favorable, unfavorable)

    # 收入模式
    modes = []
    if groups["wealth"] >= 2:
        modes.append("主业收入 + 稳定客户")
    if groups["output"] >= 2:
        modes.append("技术/内容/服务输出")
    if groups["officer"] >= 2:
        modes.append("职位晋升和平台收入")
    if groups["peer"] >= 2:
        modes.append("合伙或项目制收益")
    if not modes:
        modes.append("稳定积累为主")

    # 财富机会
    opportunities = []
    if _has_special_combination(chart, "食神生财"):
        opportunities.append("将技能和内容转化为可持续收益")
    if groups["wealth"] >= 2 and s == "身强":
        opportunities.append("项目型、资源型收益机会")
    if groups["officer"] >= 2 and groups["wealth"] >= 2:
        opportunities.append("职位晋升带动收入增长")
    if not opportunities:
        opportunities.append("持续能力积累带来的复利效应")

    # 财富风险
    risks = []
    if groups["peer"] >= 3 and groups["wealth"] >= 2:
        risks.append("比劫制财：合作、人情、竞争消耗")
    if wealth_el in set(unfavorable):
        risks.append("财星为忌神：求财消耗较大")
    if s == "身弱" and groups["wealth"] >= 2:
        risks.append("财多身弱：机会多但承接难")
    if not risks:
        risks.append("财富风险不集中在单一问题上，更适合用预算表和现金流节奏来管理")

    return {
        "wealth_level": _format_level(score),
        "wealth_type": " · ".join(types[:2]),
        "wealth_score": score,
        "wealth_summary": (
            f"{_visible_wealth_basis(chart, groups, favorable, unfavorable)}"
            f"{WEALTH_ARCHETYPE_TEXT.get(types[0], '')}；"
            f"{WEALTH_ARCHETYPE_TEXT.get(types[1], '需要靠长期积累形成安全边际') if len(types)>1 else '需要靠长期积累形成安全边际'}。"
            f"{gender or '此命盘'}按{types[0]} / {types[1] if len(types)>1 else '稳健积累型'}处理，"
            f"{day_master}{day_el}盘财{groups['wealth']}、食伤{groups['output']}、比劫{groups['peer']}，"
            f"财富分{score}（{_format_level(score)}），依据：{'、'.join(reasons[:4])}。"
        ),
        "income_modes": modes,
        "wealth_opportunities": opportunities,
        "wealth_risks": risks,
        "money_management_advice": (
            "建议把收入按稳定部分和弹性部分分开管理，弹性部分用于投资和项目尝试。"
            if s == "身强"
            else "建议先保护好现金流，投资和扩张项目多留缓冲期。"
        ),
        "evidence": [
            f"正财{ten_god_counts.get('正财',0)}/偏财{ten_god_counts.get('偏财',0)}",
            f"财星五行{wealth_el}",
            f"日主{s}{', 喜用'+'、'.join(favorable) if favorable else ''}",
        ],
        "source_ids": ["yuan_hai_zi_ping", "san_ming_tong_hui", "zi_ping_zhen_quan"],
    }


def _build_romance_text(chart: dict, fp: dict, groups: dict,
                        favorable: list, score: int, reasons: list,
                        peach: dict) -> dict:
    signature = _build_relationship_signature(chart, groups, peach)
    core_portrait, primary_focus = _relationship_outcome(signature)
    relationship_evidence = _relationship_evidence(signature)
    palace = signature["spouse_palace"]
    relations = signature["spouse_relations"]
    spouse = signature["spouse_star"]
    support = signature["ten_god_support"]
    peach_signal = signature["peach_blossom"]
    strength = signature["strength_preference"]["strength"]
    spouse_basis = signature["spouse_star"]["basis"]
    basis_context = (
        "财星口径侧重现实经营与资源边界。"
        if spouse_basis == "财星"
        else "官杀口径侧重责任承诺与压力边界。"
        if spouse_basis == "官杀"
        else ""
    )

    if core_portrait == "关系信号待观察":
        if palace["branch"]:
            neutral_summary = (
                f"{_visible_relationship_basis(signature)}"
                f"关系核心画像：{core_portrait}。主要经营点：{primary_focus}。"
                "当前关系事实完整，但没有单一信号达到具体规则阈值，因此保持中性观察。"
            )
        else:
            neutral_summary = (
                f"关系核心画像：{core_portrait}。主要经营点：{primary_focus}。"
                "当前夫妻宫与性别条件下的配偶星信息不完整，因此不套用其他命盘的关系结论。"
            )
        return {
            "romance_level": _format_level(score),
            "romance_type": core_portrait,
            "romance_score": score,
            "core_portrait": core_portrait,
            "primary_relationship_focus": primary_focus,
            "relationship_signature": signature,
            "romance_summary": neutral_summary,
            "attraction_points": [],
            "relationship_strengths": [],
            "relationship_risks": [],
            "suitable_partner_type": [],
            "communication_advice": primary_focus,
            "evidence": relationship_evidence,
            "source_ids": ["yuan_hai_zi_ping", "san_ming_tong_hui", "ming_li_tan_yuan"],
        }

    # 吸引力
    attraction = []
    if peach_signal["count"]:
        attraction.append(f"桃花出现在{'、'.join(peach_signal['positions'])}")
    if support["output"] >= 3:
        attraction.append("表达力和感染力较强")
    if strength == "身强":
        attraction.append("个人气场较明显")

    # 关系优势
    strengths = []
    if palace["role"] == "喜用":
        strengths.append("夫妻宫为喜用，关系对整体运势有助益")
    if spouse["basis"] == "官杀" and spouse["total"] >= 2:
        strengths.append("重视承诺和责任匹配")
    if spouse["basis"] == "财星" and spouse["total"] >= 2:
        strengths.append("重视现实基础和稳定性")

    # 关系风险
    risks = []
    if relations["clashes"]:
        risks.append("夫妻宫逢冲，关系易受外部因素影响")
    if palace["role"] == "忌神":
        risks.append("夫妻宫为忌神，关系中需要更多包容")
    if spouse["basis"] == "官杀" and spouse["total"] >= 3:
        risks.append("官杀信号较集中，适合核对责任感和关系质量")
    if support["peer"] >= 3:
        risks.append("自我边界强，需注意双方平衡")

    # 适合的伴侣类型
    suitable = []
    if spouse["basis"] == "财星" and spouse["total"] >= 2:
        suitable.append("务实稳定型")
    if spouse["basis"] == "官杀" and spouse["total"] >= 2:
        suitable.append("责任匹配型")
    if support["output"] >= 2:
        suitable.append("沟通表达型")
    if support["resource"] >= 2:
        suitable.append("学识修养型")

    return {
        "romance_level": _format_level(score),
        "romance_type": core_portrait,
        "romance_score": score,
        "core_portrait": core_portrait,
        "primary_relationship_focus": primary_focus,
        "relationship_signature": signature,
        "romance_summary": (
            f"{_visible_relationship_basis(signature)}"
            f"{basis_context}"
            f"关系核心画像：{core_portrait}。{ROMANCE_ARCHETYPE_TEXT.get(core_portrait, '')}。"
            f"主要经营点：{primary_focus}。"
            f"感情分{score}（{_format_level(score)}），依据：{'、'.join(relationship_evidence)}。"
        ),
        "attraction_points": attraction,
        "relationship_strengths": strengths,
        "relationship_risks": risks,
        "suitable_partner_type": suitable,
        "communication_advice": primary_focus,
        "evidence": relationship_evidence,
        "source_ids": ["yuan_hai_zi_ping", "san_ming_tong_hui", "ming_li_tan_yuan"],
    }


def _build_health_text(chart: dict, fp: dict, groups: dict,
                       elements: dict, el_labels: dict,
                       s: str, score: int, reasons: list) -> dict:
    strong_els = [e for e, l in el_labels.items() if l == "偏旺"]
    weak_els = [e for e, l in el_labels.items() if l == "偏弱"]
    present = [e for e, v in elements.items() if float(v) > 0]
    missing = [e for e in ["木","火","土","金","水"] if e not in present]

    ELEMENT_ORGANS = {
        "木": "肝胆、筋骨", "火": "心脏、睡眠、情绪",
        "土": "脾胃、消化、代谢", "金": "呼吸、皮肤、免疫力",
        "水": "腰肾、泌尿、精力恢复",
    }
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")

    sensitive = []
    for e in strong_els:
        sensitive.append(f"{e}偏旺：{ELEMENT_ORGANS.get(e, '对应系统')}需养护")
    for e in weak_els:
        sensitive.append(f"{e}偏弱：{ELEMENT_ORGANS.get(e, '对应系统')}需补充")
    for e in missing:
        sensitive.append(f"{e}缺失：{ELEMENT_ORGANS.get(e, '对应系统')}需后天补足")

    tendencies = []
    health_types = _health_archetypes(groups, el_labels, s)
    if strong_els:
        tendencies.append(f"{'、'.join(strong_els)}偏旺时对应系统需要更多养护")
    if weak_els:
        tendencies.append(f"{'、'.join(weak_els)}偏弱时需注意补充和调理")
    if groups["officer"] >= 3:
        tendencies.append("官杀偏重，压力管理是长期健康的重要方面")
    if s == "身弱":
        tendencies.append("日主偏弱，规律作息和精力恢复很重要")
    if not tendencies:
        tendencies.append("整体健康状态处于均衡范围，保持规律作息和适度运动即可")

    lifestyle_risks = []
    if groups["officer"] >= 3:
        lifestyle_risks.append("高压状态下容易忽略休息和运动")
    if groups["output"] >= 3:
        lifestyle_risks.append("表达型工作容易导致心力和体力消耗")
    if s == "身弱":
        lifestyle_risks.append("容易透支而不自知")

    return {
        "health_stability_level": _format_level(score),
        "health_type": " · ".join(health_types[:2]),
        "health_score": score,
        "health_summary": (
            f"{_visible_health_basis(chart, groups, el_labels, missing)}"
            f"{HEALTH_ARCHETYPE_TEXT.get(health_types[0], '')}；"
            f"{HEALTH_ARCHETYPE_TEXT.get(health_types[1], '规律恢复比短期补救更重要') if len(health_types)>1 else '规律恢复比短期补救更重要'}。"
            f"身体标签为{health_types[0]} / {health_types[1] if len(health_types)>1 else '作息恢复'}，"
            f"{day_master}{day_el}盘五行{'较全' if len(missing)<=1 else '有缺口'}、{s}，"
            f"健康分{score}（{_format_level(score)}），依据：{'、'.join(reasons[:4])}。"
        ),
        "sensitive_elements": sensitive,
        "body_system_tendencies": tendencies,
        "lifestyle_risks": lifestyle_risks if lifestyle_risks else ["暂无突出风险"],
        "long_term_care_advice": [
            f"五行{'偏旺' if strong_els else '缺失' if missing else '基本均衡'}，建议定期关注{','.join(strong_els[:2]) if strong_els else '整体'}系统的状态。",
            "规律作息和适度运动比任何调理都重要。",
            "建议每年一次全面体检，关注血压、血糖、血脂等基础指标。",
        ],
        "medical_disclaimer": "本部分仅为传统命理中的五行状态参考，不构成医学诊断或治疗建议。",
        "evidence": [
            f"五行态势：{'、'.join(f'{e}{l}' for e,l in el_labels.items() if l in('偏旺','偏弱')) or '基本均衡'}",
            f"日主{s}",
        ],
        "source_ids": ["qiong_tong_bao_jian", "san_ming_tong_hui", "di_tian_sui_chan_wei"],
    }


def _build_career_text(chart: dict, fp: dict, groups: dict,
                       favorable: list, score: int, reasons: list) -> dict:
    s = chart.get("day_master_strength", {}).get("strength", "")
    day_master = chart.get("day_master", "")
    day_el = STEM_ELEMENTS.get(day_master, "")

    types = _career_archetypes(groups, s)

    strengths = []
    if s == "身强":
        strengths.append("自主推进力和抗压能力较好")
    if groups["officer"] >= 2:
        strengths.append("责任感和规则意识较强")
    if groups["output"] >= 2:
        strengths.append("表达和创造能力较突出")
    if groups["resource"] >= 2:
        strengths.append("学习能力和贵人运较好")

    risks = []
    if groups["peer"] >= 3 and groups["officer"] == 0:
        risks.append("竞争摩擦和团队协作需注意")
    if s == "身弱":
        risks.append("容易在高压环境中透支")
    if groups["officer"] >= 3 and s == "身弱":
        risks.append("官杀攻身，压力和目标管理是长期课题")

    return {
        "career_type": " · ".join(types[:2]),
        "career_score": score,
        "career_summary": (
            f"{CAREER_ARCHETYPE_TEXT.get(types[0], '')}；"
            f"{CAREER_ARCHETYPE_TEXT.get(types[1], '先稳住基本盘，再逐步放大优势') if len(types)>1 else '先稳住基本盘，再逐步放大优势'}。"
            f"事业标签为{types[0]} / {types[1] if len(types)>1 else '稳定积累型'}，"
            f"{day_master}{day_el}盘官杀{groups['officer']}、食伤{groups['output']}、印{groups['resource']}，"
            f"事业分{score}（{_format_level(score)}），依据：{'、'.join(reasons[:4])}。"
        ),
        "development_path": [
            f"适合从{types[0] if types else '稳定积累'}方向切入",
            "建议在前3-5年积累核心能力和行业资源",
            "中期根据大运变化调整方向和节奏",
        ],
        "career_strengths": strengths,
        "career_risks": risks,
        "long_term_action_advice": [
            "先积累可迁移的核心能力，再根据阶段运势选择发力点。",
            "如果身强，可以主动push边界；如果身弱，先借力、再发力。",
        ],
        "evidence": [
            f"十神结构：{max(groups, key=groups.get)}{max(groups.values(), default=0)}个",
            f"日主{s}",
        ],
        "source_ids": ["yuan_hai_zi_ping", "san_ming_tong_hui", "zi_ping_zhen_quan"],
    }
