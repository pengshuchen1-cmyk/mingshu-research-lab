"""八字格局判定引擎。

以月令为核心，结合透干、十神组合、日主强弱和喜忌，生成可解释的格局初判。
当前版本不做绝对化高低断语，只输出趋势、依据和后续需要观察的点。
"""

from __future__ import annotations

from core.bazi_constants import BRANCH_HIDDEN_STEMS, STEM_ELEMENTS
from core.ten_gods import get_ten_god

TEN_GOD_TO_PATTERN = {
    "正官": "正官格",
    "七杀": "七杀格",
    "正财": "正财格",
    "偏财": "偏财格",
    "正印": "正印格",
    "偏印": "偏印格",
    "食神": "食神格",
    "伤官": "伤官格",
    "比肩": "建禄格",
    "劫财": "月刃格",
}

PATTERN_MEANINGS = {
    "正官格": "重规则、责任、职位和稳定秩序，现实里常对应组织、制度、管理和长期信用。",
    "七杀格": "重压力、竞争、执行和突破，现实里常对应高压任务、管理挑战、攻坚项目。",
    "正财格": "重稳定收入、预算、客户和现实经营，适合把资源沉淀成可持续收益。",
    "偏财格": "重机会资源、项目收益、灵活经营和人脉调度，适合看机会但要控风险。",
    "正印格": "重学习、资质、保护、系统和贵人支持，适合借助平台、专业和证照成长。",
    "偏印格": "重研究、灵感、专业深度和非标准路径，适合深挖冷门技能但要避免想太多。",
    "食神格": "重稳定输出、作品、技能、服务和生活品质，现实里常对应靠专业与口碑生财。",
    "伤官格": "重表达、创意、突破和规则摩擦，适合展示能力，也要注意说法和边界。",
    "建禄格": "日主在月令得根，行动力和自我驱动较强，适合靠能力与责任感立身。",
    "月刃格": "月令比劫气重，竞争心和承压性较强，适合攻坚，但要注意合伙和情绪边界。",
    "从旺格": "日主旺势达到严格条件，取顺势生扶为主，同时持续复核是否出现足以破格的反向力量。",
    "从弱格": "日主弱势达到严格条件，取顺势克泄耗为主，同时持续复核是否出现足以破格的根气或印比。",
    "格局未明": "月令和透干信号暂不集中，宜先看日主强弱、五行流通和大运流年。",
}

GOOD_COMBOS = {
    "正官格": [("正印", "官印相生"), ("正财", "财官相生")],
    "七杀格": [("正印", "杀印相生"), ("食神", "食神制杀")],
    "正财格": [("食神", "食伤生财"), ("正官", "财官相生")],
    "偏财格": [("食神", "食伤生财"), ("正官", "财官相生")],
    "食神格": [("正财", "食神生财"), ("偏财", "食神生财")],
    "伤官格": [("正印", "伤官配印"), ("偏印", "伤官配印"), ("正财", "伤官生财")],
    "正印格": [("正官", "官印相生"), ("七杀", "杀印相生")],
    "偏印格": [("七杀", "杀印相生"), ("比肩", "印比相承")],
}

RISK_COMBOS = {
    "正官格": [("伤官", "伤官见官，表达与规则容易顶住")],
    "七杀格": [("正官", "官杀混杂，压力来源容易变多")],
    "正财格": [("劫财", "比劫争财，合伙和分账要清楚")],
    "偏财格": [("劫财", "比劫争财，机会背后要看成本")],
    "食神格": [("偏印", "枭神夺食，输出容易被打断")],
    "伤官格": [("正官", "伤官见官，规则和表达需协调")],
    "正印格": [("正财", "财印相碍，现实收益与学习资质需平衡")],
    "偏印格": [("食神", "枭神夺食，想法多时输出节奏易受扰")],
}


def _visible_stems(chart: dict) -> list[str]:
    return [p.get("gan", "") for p in chart.get("pillars", {}).values() if p.get("gan")]


def _all_ten_gods(chart: dict) -> list[str]:
    day_master = chart.get("day_master", "")
    gods: list[str] = []
    for p in chart.get("pillars", {}).values():
        gan = p.get("gan", "")
        if gan:
            gods.append(get_ten_god(day_master, gan))
        for h in BRANCH_HIDDEN_STEMS.get(p.get("zhi", ""), []):
            gods.append(get_ten_god(day_master, h))
    return [g for g in gods if g and g != "未知"]


def _month_command_god(chart: dict) -> tuple[str, str]:
    day_master = chart.get("day_master", "")
    month_zhi = chart.get("pillars", {}).get("month", {}).get("zhi", "")
    hidden = BRANCH_HIDDEN_STEMS.get(month_zhi, [])
    main_gan = hidden[0] if hidden else ""
    return main_gan, get_ten_god(day_master, main_gan) if main_gan else "未知"


def _select_pattern(chart: dict) -> tuple[str, str, list[str]]:
    day_master = chart.get("day_master", "")
    month_zhi = chart.get("pillars", {}).get("month", {}).get("zhi", "")
    hidden = BRANCH_HIDDEN_STEMS.get(month_zhi, [])
    visible = set(_visible_stems(chart))
    evidence: list[str] = []

    main_gan, main_god = _month_command_god(chart)
    if main_gan:
        evidence.append(f"月令{month_zhi}以{main_gan}为主气，对日主为{main_god}。")

    # 月令主气若为比劫，优先看月支藏干是否透出成事之神。
    for gan in hidden[1:] if main_god in {"比肩", "劫财"} else hidden[:1]:
        if gan in visible and gan != day_master:
            tg = get_ten_god(day_master, gan)
            pattern = TEN_GOD_TO_PATTERN.get(tg, "格局未明")
            evidence.append(f"月令藏干{gan}透出天干，取{tg}为格局主线。")
            return pattern, "月令透干", evidence

    pattern = TEN_GOD_TO_PATTERN.get(main_god, "格局未明")
    source = "月令主气" if pattern != "格局未明" else "综合观察"
    if pattern != "格局未明":
        evidence.append(f"以月令主气{main_god}定为{pattern}。")
    return pattern, source, evidence


def _quality(pattern: str, gods: list[str], strength: dict, favorable: set[str], exposed_gods: list[str]) -> tuple[str, list[str], list[str]]:
    good: list[str] = []
    risks: list[str] = []
    for god, text in GOOD_COMBOS.get(pattern, []):
        if god in gods:
            good.append(text)
    for god, text in RISK_COMBOS.get(pattern, []):
        if god in gods:
            risks.append(text)

    pattern_key = pattern.replace("格", "")
    if pattern_key in exposed_gods:
        good.append("格局主气透出，主题较容易被现实看见")

    fav_hit = False
    for god in exposed_gods:
        if god in {"正财", "偏财", "正官", "七杀", "食神", "伤官", "正印", "偏印"}:
            fav_hit = True
            break
    if fav_hit and strength.get("strength") in {"身强", "身弱", "中和", "从旺", "从弱"}:
        good.append("能和日主强弱一起观察，不是孤立断格")

    if len(good) >= 2 and not risks:
        return "较成", good, risks
    if good and risks:
        return "成中有待", good, risks
    if risks and not good:
        return "需经营", good, risks
    if pattern == "格局未明":
        return "格局未明", good, risks
    return "成中有待", good, risks


def analyze_pattern(chart: dict) -> dict:
    """分析命局格局，返回普通用户能读懂的判定结果。"""
    try:
        day_master = chart.get("day_master", "")
        day_element = STEM_ELEMENTS.get(day_master, "")
        main_gan, month_command_ten_god = _month_command_god(chart)
        pattern, source, evidence = _select_pattern(chart)
        visible = _visible_stems(chart)
        exposed_stems = [s for s in visible if s != day_master]
        exposed_gods = [get_ten_god(day_master, s) for s in exposed_stems]
        gods = _all_ten_gods(chart)
        strength = chart.get("day_master_strength", {})
        favorable = set(strength.get("favorable_elements", []))
        quality, supports, risks = _quality(pattern, gods, strength, favorable, exposed_gods)
        meaning = PATTERN_MEANINGS.get(pattern, PATTERN_MEANINGS["格局未明"])
        plain = (
            f"格局初判为{pattern}，来源是{source}。"
            f"它的白话意思是：{meaning}"
            f"当前更适合把它当成命盘主线之一，后面还要结合大运、流年和现实选择来验证。"
        )
        if supports:
            evidence.append("有利配合：" + "、".join(dict.fromkeys(supports[:4])))
        if risks:
            evidence.append("需要经营：" + "、".join(dict.fromkeys(risks[:4])))
        special_pattern = strength.get("special_pattern", "无")
        if special_pattern in {"从旺", "从弱"}:
            pattern = f"{special_pattern}格"
            source = "特殊格局严格复核"
            quality = "特殊格局"
            meaning = PATTERN_MEANINGS[pattern]
            evidence.append(f"特殊格局严格复核通过，统一以{pattern}作为规范格局结论。")
            plain = (
                f"格局初判为{pattern}，来源是{source}。"
                f"它的白话意思是：{meaning}"
                "后续仍需结合大运、流年和现实反馈复核是否保持成格条件。"
            )
            special_review = {
                "considered": True,
                "accepted": True,
                "result": special_pattern,
                "reason": "强弱证据达到特殊格局阈值，仍需结合反向根气复核。",
            }
        else:
            special_review = {
                "considered": True,
                "accepted": False,
                "result": "普通格局",
                "reason": "命局仍见双向生克和根气，优先按月令普通格局分析。",
            }
        return {
            "day_master": day_master,
            "day_master_element": day_element,
            "pattern": pattern,
            "pattern_source": source,
            "quality": quality,
            "month_command_gan": main_gan,
            "month_command_ten_god": month_command_ten_god,
            "exposed_stems": exposed_stems,
            "exposed_ten_gods": exposed_gods,
            "supporting_combinations": list(dict.fromkeys(supports)),
            "risk_combinations": list(dict.fromkeys(risks)),
            "plain_text": plain,
            "evidence": evidence,
            "basis": "参考《子平真诠》以月令取格、《三命通会》格局分类，并结合十神透干与成败配合做趋势化判断。",
            "formation_evidence": list(evidence),
            "damage_factors": list(dict.fromkeys(risks)),
            "rescue_factors": list(dict.fromkeys(supports)),
            "special_pattern_review": special_review,
            "rule_ids": [
                "PATTERN-MONTH-QI",
                "PATTERN-SUCCESS-FAILURE",
                "PATTERN-SPECIAL-STRICT",
            ],
            "public_text": plain,
        }
    except Exception as exc:
        return {
            "pattern": "格局暂无法判断",
            "quality": "格局未明",
            "plain_text": f"格局判定暂不可用：{exc}",
            "evidence": [],
            "basis": "格局判定暂未完成。",
            "formation_evidence": [],
            "damage_factors": [],
            "rescue_factors": [],
            "special_pattern_review": {
                "considered": False,
                "accepted": False,
                "result": "未完成",
                "reason": str(exc),
            },
            "rule_ids": [],
            "public_text": f"格局判定暂不可用：{exc}",
        }
