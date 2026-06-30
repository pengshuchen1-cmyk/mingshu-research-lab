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
    else:
        spouse_score = groups["wealth"] * 8
        if groups["wealth"] >= 2:
            reasons.append("财星明显")
        elif groups["wealth"] == 0:
            spouse_score -= 5
            reasons.append("妻星不显")
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
    w_score, w_reasons = _score_wealth(chart, fp, groups)
    r_score, r_reasons = _score_romance(chart, fp, groups)
    h_score, h_reasons = _score_health(chart, fp)
    c_score, c_reasons = _score_career(chart, fp, groups)
    overall = (w_score + r_score + h_score + c_score) // 4

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

    return {
        "overall_pattern": pattern,
        "overall_summary": (
            f"此命局{pattern}，整体{_format_level(overall)}。{keyword_summary(keywords)}"
            "以下从财富、感情、健康、事业四个维度做趋势分析。"
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
            "overall_balance": overall,
        },
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

def _build_wealth_text(chart: dict, fp: dict, groups: dict,
                       favorable: list, unfavorable: list,
                       score: int, reasons: list) -> dict:
    day_master = chart.get("day_master", "")
    ten_god_counts = chart.get("ten_god_counts", {})
    wealth_el_map = {"甲":"土","乙":"土","丙":"金","丁":"金","戊":"水","己":"水","庚":"木","辛":"木","壬":"火","癸":"火"}
    wealth_el = wealth_el_map.get(day_master, "")
    s = chart.get("day_master_strength", {}).get("strength", "")

    # 财富类型
    types = []
    if groups["output"] >= 3:
        types.append("技能变现型")
    if groups["wealth"] >= 3 and s == "身强":
        types.append("项目经营型")
    if groups["wealth"] >= 3 and groups["officer"] >= 2:
        types.append("职位收入型")
    if groups["peer"] >= 3 and groups["wealth"] >= 2:
        types.append("合伙慎重型")
    if groups["resource"] >= 3:
        types.append("平台资质型")
    if not types:
        if groups["wealth"] >= 2:
            types.append("稳定收入型")
        else:
            types.append("技能变现型")

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
        risks.append("暂无特别突出的财富风险点，注意现金流和预算即可")

    return {
        "wealth_level": _format_level(score),
        "wealth_type": " · ".join(types[:2]),
        "wealth_score": score,
        "wealth_summary": (
            f"财星{'较强' if groups['wealth']>=2 else '一般'}，{'食伤生财助力' if _has_special_combination(chart,'食神生财') else '以稳为主'}。"
            f"评分{score}（{_format_level(score)}）。判断依据：{'、'.join(reasons[:3])}。"
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
    gender = chart.get("profile", {}).get("gender", "")
    ten_god_counts = chart.get("ten_god_counts", {})
    s = chart.get("day_master_strength", {}).get("strength", "")
    day_master = chart.get("day_master", "")
    day_zhi = chart.get("pillars", {}).get("day", {}).get("zhi", "")

    # 感情类型
    types = []
    if peach["peach_count"] >= 2:
        types.append("外显桃花型")
    elif peach["peach_count"] >= 1:
        types.append("有吸引力型")
    else:
        types.append("稳定伴侣型")
    if _day_zhi_clashed(chart):
        types.append("关系波动型")
    if groups["peer"] >= 3:
        types.append("慢热经营型")
    if not types:
        types.append("稳定表达型")

    # 吸引力
    attraction = []
    if peach["has_peach_blossom"]:
        attraction.append(f"桃花出现在{'、'.join(peach['positions'])}")
    if groups["output"] >= 3:
        attraction.append("表达力和感染力较强")
    if s == "身强":
        attraction.append("个人气场较明显")

    # 关系优势
    strengths = []
    sp_fav, _, sp_el = _spouse_element_relation(chart, set(favorable), set())
    if sp_fav:
        strengths.append("夫妻宫为喜用，关系对整体运势有助益")
    if groups["officer"] >= 2 and gender == "女":
        strengths.append("重视承诺和责任匹配")
    if groups["wealth"] >= 2 and gender == "男":
        strengths.append("重视现实基础和稳定性")

    # 关系风险
    risks = []
    if _day_zhi_clashed(chart):
        risks.append("夫妻宫逢冲，关系易受外部因素影响")
    sp_uf, _, _ = _spouse_element_relation(chart, set(), set(chart.get("day_master_strength", {}).get("unfavorable_elements", [])))
    if sp_uf:
        risks.append("夫妻宫为忌神，关系中需要更多包容")
    if groups["officer"] >= 3 and gender == "女":
        risks.append("官杀混杂需注意筛选感情质量")
    if groups["peer"] >= 3:
        risks.append("自我边界强，需注意双方平衡")

    # 适合的伴侣类型
    suitable = []
    if groups["wealth"] >= 2:
        suitable.append("务实稳定型")
    if groups["output"] >= 2:
        suitable.append("沟通表达型")
    if groups["resource"] >= 2:
        suitable.append("学识修养型")
    if not suitable:
        suitable.append("包容理解型")

    return {
        "romance_level": _format_level(score),
        "romance_type": " · ".join(types[:2]),
        "romance_score": score,
        "romance_summary": (
            f"感情方面{'桃花较明显' if peach['has_peach_blossom'] else '以稳定经营为主'}，"
            f"{'日支逢冲需要注意关系调整' if _day_zhi_clashed(chart) else '夫妻宫关系基本稳定'}。"
            f"评分{score}（{_format_level(score)}）。判断依据：{'、'.join(reasons[:3])}。"
        ),
        "attraction_points": attraction,
        "relationship_strengths": strengths,
        "relationship_risks": risks,
        "suitable_partner_type": suitable,
        "communication_advice": (
            "建议把感受和期待直接表达，用具体行动配合语言沟通。"
            if groups["output"] >= 2
            else "关系中以真诚陪伴为主，重要感受和想法定期沟通。"
        ),
        "evidence": [
            f"夫妻宫：{day_zhi}（{BRANCH_MAIN_ELEMENTS.get(day_zhi,'')}）",
            f"桃花：{'有' if peach['has_peach_blossom'] else '不显'}（{'、'.join(peach['positions']) if peach['has_peach_blossom'] else '需大运引动'}）",
            f"日支{'逢冲' if _day_zhi_clashed(chart) else '未逢冲'}",
        ],
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

    sensitive = []
    for e in strong_els:
        sensitive.append(f"{e}偏旺：{ELEMENT_ORGANS.get(e, '对应系统')}需养护")
    for e in weak_els:
        sensitive.append(f"{e}偏弱：{ELEMENT_ORGANS.get(e, '对应系统')}需补充")
    for e in missing:
        sensitive.append(f"{e}缺失：{ELEMENT_ORGANS.get(e, '对应系统')}需后天补足")

    tendencies = []
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
        "health_score": score,
        "health_summary": (
            f"{'五行较全，' if len(missing)<=1 else '五行缺失较多，'}"
            f"{'日主强旺基础较好' if s=='身强' else '日主偏弱需注意养护'}。"
            f"评分{score}（{_format_level(score)}）。判断依据：{'、'.join(reasons[:3])}。"
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

    # 事业类型
    types = []
    if groups["output"] >= 3:
        types.append("专业技术型")
    if groups["officer"] >= 3:
        types.append("管理规则型")
    if groups["wealth"] >= 3:
        types.append("资源经营型")
    if groups["resource"] >= 3:
        types.append("平台资质型")
    if groups["peer"] >= 3:
        types.append("自主创业型")
    if s == "身弱":
        types.append("借力成长型")
    if not types:
        types.append("稳定积累型")

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
            f"事业方面偏向{' · '.join(types[:2])}方向，"
            f"评分{score}（{_format_level(score)}）。判断依据：{'、'.join(reasons[:3])}。"
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
