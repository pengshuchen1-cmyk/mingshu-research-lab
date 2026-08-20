"""日主强弱和喜忌初判。"""

from __future__ import annotations

from .bazi_constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_MAIN_ELEMENTS,
    CONTROLLING,
    FIVE_ELEMENT_ORDER,
    GENERATING,
    STEM_ELEMENTS,
)
from .seasonal_adjustment import analyze_seasonal_adjustment

HIDDEN_STEM_WEIGHTS: list[float] = [1.0, 0.5, 0.3]


def _parent_element(element: str) -> str:
    """返回生扶当前五行的五行。"""
    for source, target in GENERATING.items():
        if target == element:
            return source
    return ""


def _controlling_element(element: str) -> str:
    """返回克制当前五行的五行。"""
    for source, target in CONTROLLING.items():
        if target == element:
            return source
    return ""


def _score_month_command(day_element: str, month_element: str) -> tuple[float, str]:
    """计算得令分数和说明。"""
    if month_element == day_element:
        return 3.0, "月令主气与日主同五行，日主得令较明显。"
    if GENERATING.get(month_element) == day_element:
        return 2.0, "月令主气生日主，日主得到季节层面的助力。"
    if GENERATING.get(day_element) == month_element:
        return -1.0, "日主生月令主气，力量存在外泄。"
    if CONTROLLING.get(day_element) == month_element:
        return -1.0, "日主克月令主气，力量存在消耗。"
    if CONTROLLING.get(month_element) == day_element:
        return -3.0, "月令对日主形成克制，日主得令不足。"
    return 0.0, "月令与日主关系不明显，得令影响较平。"


def _score_branch_roots(day_master: str, day_element: str, chart: dict) -> tuple[float, str]:
    """计算地支根气和得地说明。"""
    score = 0.0
    root_count = 0
    same_main_count = 0
    supportive_main_count = 0
    pressure_main_count = 0

    for pillar in chart.get("pillars", {}).values():
        branch = pillar.get("zhi", "")
        hidden_stems = BRANCH_HIDDEN_STEMS.get(branch, [])
        root_count += hidden_stems.count(day_master)
        score += hidden_stems.count(day_master)

        main_element = BRANCH_MAIN_ELEMENTS.get(branch, "")
        if main_element == day_element:
            score += 1.0
            same_main_count += 1
        elif GENERATING.get(main_element) == day_element:
            score += 0.5
            supportive_main_count += 1
        elif CONTROLLING.get(main_element) == day_element:
            score -= 1.0
            pressure_main_count += 1

    if score >= 3:
        text = "地支中根气较明显，日主有较稳定的承接力量。"
    elif score > 0:
        text = "地支中有部分根气，但力量不算特别稳定。"
    elif pressure_main_count:
        text = "地支主气中克制日主的力量较明显，得地不足。"
    else:
        text = "地支对日主的直接支撑不明显，需要结合整体结构观察。"

    detail = f"藏干见日主{root_count}次，同气主气{same_main_count}处，生扶主气{supportive_main_count}处。"
    return round(score, 2), f"{text}{detail}"


def _classify_element_relation(day_element: str, target_element: str) -> str:
    """判断目标五行相对日主的关系类型。"""
    if target_element == day_element:
        return "生扶"
    if GENERATING.get(target_element) == day_element:
        return "生扶"
    if GENERATING.get(day_element) == target_element:
        return "泄"
    if CONTROLLING.get(day_element) == target_element:
        return "耗"
    if CONTROLLING.get(target_element) == day_element:
        return "克"
    return "平"


def _score_influence(day_element: str, chart: dict) -> tuple[float, float, str]:
    """统计天干和藏干中的生扶、克泄耗力量。"""
    support_score = 0.0
    pressure_score = 0.0
    detail_counts = {"生扶": 0.0, "克": 0.0, "泄": 0.0, "耗": 0.0}

    for pillar in chart.get("pillars", {}).values():
        gan = pillar.get("gan", "")
        gan_element = STEM_ELEMENTS.get(gan, "")
        relation = _classify_element_relation(day_element, gan_element)
        if relation == "生扶":
            support_score += 1.0
            detail_counts["生扶"] += 1.0
        elif relation in {"克", "泄", "耗"}:
            pressure_score += 1.0
            detail_counts[relation] += 1.0

        branch = pillar.get("zhi", "")
        for index, hidden_gan in enumerate(BRANCH_HIDDEN_STEMS.get(branch, [])):
            weight = HIDDEN_STEM_WEIGHTS[index] if index < len(HIDDEN_STEM_WEIGHTS) else 0.3
            hidden_element = STEM_ELEMENTS.get(hidden_gan, "")
            relation = _classify_element_relation(day_element, hidden_element)
            if relation == "生扶":
                support_score += weight
                detail_counts["生扶"] += weight
            elif relation in {"克", "泄", "耗"}:
                pressure_score += weight
                detail_counts[relation] += weight

    if support_score > pressure_score:
        text = "命局中生扶日主的力量相对明显。"
    elif pressure_score > support_score:
        text = "命局中克泄耗力量相对明显。"
    else:
        text = "命局中生扶与克泄耗力量大致接近。"

    detail = (
        f"生扶约{round(detail_counts['生扶'], 2)}，"
        f"克约{round(detail_counts['克'], 2)}，"
        f"泄约{round(detail_counts['泄'], 2)}，"
        f"耗约{round(detail_counts['耗'], 2)}。"
    )
    return round(support_score, 2), round(pressure_score, 2), f"{text}{detail}"


def _judge_strength(
    net_score: float,
    *,
    season_score: float = 0.0,
    root_score: float = 0.0,
    support_score: float = 0.0,
    pressure_score: float = 0.0,
) -> str:
    """综合月令、根气和生克力量判断，净分只作为明显失衡的兜底。"""
    if season_score > 0 and root_score > 0 and support_score >= pressure_score:
        return "身强"
    if season_score < 0 and root_score <= 0 and pressure_score > support_score:
        return "身弱"
    if net_score >= 3:
        return "身强"
    if net_score <= -2:
        return "身弱"
    return "中和"


def _element_preferences(day_element: str, strength: str) -> tuple[list[str], list[str], str]:
    """根据日主强弱给出喜忌五行初判。"""
    parent = _parent_element(day_element)
    output = GENERATING.get(day_element, "")
    wealth = CONTROLLING.get(day_element, "")
    authority = _controlling_element(day_element)

    if strength == "身强":
        favorable = [item for item in [output, wealth, authority] if item]
        unfavorable = [item for item in [parent, day_element] if item]
        explanation = "日主偏强时，通常更适合通过泄、耗、克来疏通力量，避免生扶过重。"
    elif strength == "身弱":
        favorable = [item for item in [parent, day_element] if item]
        unfavorable = [item for item in [authority, output, wealth] if item]
        explanation = "日主偏弱时，通常更需要印星和比劫来帮助，也就是生扶日主的五行更有利。"
    else:
        favorable = []
        unfavorable = []
        explanation = "整体较平衡，喜忌不宜说死，需结合大运流年进一步判断。"

    return _dedupe_elements(favorable), _dedupe_elements(unfavorable), explanation


def _dedupe_elements(elements: list[str]) -> list[str]:
    """按五行顺序去重。"""
    return [element for element in FIVE_ELEMENT_ORDER if element in set(elements)]


def _detect_special_pattern(pillars: dict, day_element: str) -> str:
    """检测是否构成特殊格局：从旺格或从弱格。

    从旺格：全局日主五行占比 >= 70%，宜顺其旺势。
    从弱格：全局日主五行占比 <= 15%，宜顺其弱势。

    Returns:
        "从旺", "从弱", 或 "无"
    """
    element_count: dict[str, float] = {}
    same_element_root_count = 0
    for pillar in pillars.values():
        gan = pillar.get("gan", "")
        zhi = pillar.get("zhi", "")
        gan_el = STEM_ELEMENTS.get(gan, "")
        if gan_el:
            element_count[gan_el] = element_count.get(gan_el, 0) + 1.0
        hidden = BRANCH_HIDDEN_STEMS.get(zhi, [])
        for i, h_gan in enumerate(hidden[:3]):
            h_el = STEM_ELEMENTS.get(h_gan, "")
            if h_el:
                weight = HIDDEN_STEM_WEIGHTS[i] if i < len(HIDDEN_STEM_WEIGHTS) else 0.3
                element_count[h_el] = element_count.get(h_el, 0) + weight
                if h_el == day_element:
                    same_element_root_count += 1

    total = sum(element_count.values())
    if total <= 0:
        return "无"

    day_el_ratio = element_count.get(day_element, 0) / total
    resource_ratio = element_count.get(_parent_element(day_element), 0) / total
    controller_ratio = element_count.get(_controlling_element(day_element), 0) / total
    if day_el_ratio >= 0.7 and controller_ratio <= 0.1:
        return "从旺"
    if day_el_ratio <= 0.15 and same_element_root_count == 0 and resource_ratio <= 0.2:
        return "从弱"
    return "无"




def _season_adjustment_explanation(day_element: str, month_branch: str) -> dict:
    """生成调候解释层，不改变原强弱评分。"""
    return analyze_seasonal_adjustment({
        "day_master": day_element and next((stem for stem, element in STEM_ELEMENTS.items() if element == day_element), ""),
        "pillars": {"month": {"zhi": month_branch}},
    })

def analyze_day_master_strength(chart: dict) -> dict:
    """
    根据八字 chart 分析日主强弱。
    返回日主强弱、得令、得地、得势、生扶力量、克泄耗力量、喜忌五行初判。
    """
    try:
        day_master = chart.get("day_master", "")
        day_element = STEM_ELEMENTS.get(day_master, "")
        month_branch = chart.get("pillars", {}).get("month", {}).get("zhi", "")
        month_element = BRANCH_MAIN_ELEMENTS.get(month_branch, "")

        if not day_master or not day_element:
            raise ValueError("日主信息不完整，暂无法分析强弱。")

        de_ling_score, de_ling_text = _score_month_command(day_element, month_element)
        de_di_score, de_di_text = _score_branch_roots(day_master, day_element, chart)
        de_shi_support, de_shi_pressure, de_shi_text = _score_influence(day_element, chart)

        support_score = round(de_ling_score + de_di_score + de_shi_support, 2)
        pressure_score = round(de_shi_pressure, 2)
        net_score = round(support_score - pressure_score, 2)
        strength = _judge_strength(
            net_score,
            season_score=de_ling_score,
            root_score=de_di_score,
            support_score=support_score,
            pressure_score=pressure_score,
        )
        special_pattern = _detect_special_pattern(chart.get("pillars", {}), day_element)

        season_adjustment = analyze_seasonal_adjustment(chart)

        if special_pattern == "从旺":
            favorable = _dedupe_elements([day_element] + [_parent_element(day_element)])
            unfavorable = _dedupe_elements(
                [CONTROLLING.get(day_element, ""), GENERATING.get(day_element, ""), _controlling_element(day_element)]
            )
            explanation = "从旺格：全局日主五行极旺，宜顺其势，喜生扶，忌克泄耗。"
            strength = "从旺"
        elif special_pattern == "从弱":
            favorable = _dedupe_elements(
                [CONTROLLING.get(day_element, ""), GENERATING.get(day_element, ""), _controlling_element(day_element)]
            )
            unfavorable = _dedupe_elements([day_element] + [_parent_element(day_element)])
            explanation = "从弱格：全局日主五行极弱，宜顺其势，喜克泄耗，忌生扶。"
            strength = "从弱"
        else:
            favorable, unfavorable, explanation = _element_preferences(day_element, strength)

        evidence = [
            {
                "dimension": "得令",
                "rule_id": "STRENGTH-SEASON",
                "polarity": "support" if de_ling_score > 0 else "pressure" if de_ling_score < 0 else "mixed",
                "weight": float(de_ling_score),
                "fact": f"月支{month_branch}主气为{month_element}",
                "explanation": de_ling_text,
            },
            {
                "dimension": "得地",
                "rule_id": "STRENGTH-ROOT",
                "polarity": "support" if de_di_score > 0 else "pressure" if de_di_score < 0 else "mixed",
                "weight": float(de_di_score),
                "fact": "逐支检查本气、中气、余气中的同类根和生扶根",
                "explanation": de_di_text,
            },
            {
                "dimension": "得助",
                "rule_id": "STRENGTH-SUPPORT-DRAIN",
                "polarity": "support" if de_shi_support > 0 else "mixed",
                "weight": float(de_shi_support),
                "fact": f"印比生扶合计约{de_shi_support}",
                "explanation": de_shi_text,
            },
            {
                "dimension": "泄耗克制",
                "rule_id": "STRENGTH-SUPPORT-DRAIN",
                "polarity": "pressure" if de_shi_pressure > 0 else "mixed",
                "weight": float(-de_shi_pressure),
                "fact": f"食伤、财、官杀压力合计约{de_shi_pressure}",
                "explanation": de_shi_text,
            },
            {
                "dimension": "合冲有效性",
                "rule_id": "STRENGTH-SUPPORT-DRAIN",
                "polarity": "mixed",
                "weight": 0.0,
                "fact": "合冲只改变已识别根气的有效性，不单独替代月令和通根",
                "explanation": "当前强弱结论以月令、通根和透藏生克为主，合冲作为复核项。",
            },
        ]
        uncertainty: list[str] = []
        if not chart.get("pillars", {}).get("hour", {}).get("pillar"):
            uncertainty.append("时辰不详，时柱可能改变部分通根、透干和生克证据。")
            evidence.append(
                {
                    "dimension": "时辰不确定性",
                    "rule_id": "STRENGTH-UNCERTAINTY",
                    "polarity": "uncertain",
                    "weight": 0.0,
                    "fact": "时柱缺失",
                    "explanation": uncertainty[0],
                }
            )

        return {
            "day_master": day_master,
            "day_master_element": day_element,
            "strength": strength,
            "net_score": net_score,
            "support_score": support_score,
            "pressure_score": pressure_score,
            "de_ling": {"score": de_ling_score, "text": de_ling_text},
            "de_di": {"score": de_di_score, "text": de_di_text},
            "de_shi": {
                "support_score": de_shi_support,
                "pressure_score": de_shi_pressure,
                "text": de_shi_text,
            },
            "favorable_elements": favorable,
            "unfavorable_elements": unfavorable,
            "explanation": explanation,
            "special_pattern": special_pattern,
            "season_adjustment": season_adjustment,
            "evidence": evidence,
            "public_evidence": [item["explanation"] for item in evidence],
            "uncertainty": uncertainty,
            "rule_ids": [
                "STRENGTH-SEASON",
                "STRENGTH-ROOT",
                "STRENGTH-SUPPORT-DRAIN",
                "STRENGTH-UNCERTAINTY",
            ],
        }
    except Exception as exc:  # noqa: BLE001 - conservative domain fallback
        return {
            "day_master": chart.get("day_master", ""),
            "day_master_element": STEM_ELEMENTS.get(chart.get("day_master", ""), ""),
            "strength": "暂无法判断",
            "net_score": 0.0,
            "support_score": 0.0,
            "pressure_score": 0.0,
            "de_ling": {"score": 0.0, "text": "得令信息暂无法计算。"},
            "de_di": {"score": 0.0, "text": "得地信息暂无法计算。"},
            "de_shi": {"support_score": 0.0, "pressure_score": 0.0, "text": "得势信息暂无法计算。"},
            "favorable_elements": [],
            "unfavorable_elements": [],
            "explanation": f"日主强弱初判暂不可用：{exc}",
            "season_adjustment": {"plain_text": "调候解释暂无法生成。"},
            "evidence": [],
            "public_evidence": [],
            "uncertainty": ["强弱证据计算未完成。"],
            "rule_ids": [],
        }
