"""
五行结构深度报告 — v1.2-F

为五行喜忌页面提供深度五行解释，涵盖：
- 五行强弱排序
- 喜用五行和忌神五行
- 每个五行的详细解释（事业、财运、感情、健康）
- 过旺过弱表现
- 现实调整建议

来源：《渊海子平》《三命通会》《滴天髓》《穷通宝鉴》
"""

from __future__ import annotations

from ..bazi.bazi_constants import FIVE_ELEMENT_ORDER
from ..bazi.five_elements import element_summary

# 每个五行的详细解释
ELEMENT_DEEP_DETAILS = {

    "木": {
        "basic_meaning": "木主生发，代表生长、规划、学习、仁心、扩展、策划和肝胆疏泄。",
        "career_meaning": "喜木时，事业适合教育、文化、内容创意、设计、策划、品牌建设、成长型行业。",
        "wealth_meaning": "财富靠长期成长、计划、资源培育、品牌积累，不适合短期投机和急功近利。",
        "relationship_meaning": "感情重成长感、沟通深度、理想共鸣、关系舒展；过旺时容易理想化或期望过高。",
        "health_tendency": "对应肝胆、筋骨、眼睛、情绪疏泄。木弱时容易疲劳、关节不适、情绪疏泄不畅。",
        "when_too_strong": "容易急躁、生发过度、计划多执行散、情绪郁结、容易理想化与现实的落差。",
        "when_too_weak": "决断不足、成长动力弱、规划感不足、舒展不够、容易缺乏方向感和突破力。",
        "if_favorable": "适合通过阅读、课程、规律运动、亲近自然和长期计划增加木的能量。",
        "if_unfavorable": "不宜过度扩张、频繁变换方向、过度追求成长速度，建议先稳住核心能力再扩展。",
        "real_life_advice": [
            "建议建立长期学习计划，保持阅读和知识更新习惯",
            "适合通过户外活动、自然接触增加木的生发感",
            "不宜同时启动过多新项目，建议先完成再开启",
            "肝胆健康需关注，避免熬夜和过度疲劳",
        ],
    },

    "火": {
        "basic_meaning": "火主表达，代表热度、名气、传播、礼仪、光明、心神和行动力。",
        "career_meaning": "喜火时，事业适合表达、传播、媒体、品牌曝光、销售、演讲、互联网展示、创意输出。",
        "wealth_meaning": "财富靠曝光、表达、传播、流量、影响力和品牌价值，适合知识付费和内容变现。",
        "relationship_meaning": "感情热情主动、吸引力强、表达欲旺盛；过旺时容易情绪波动或关系节奏过快。",
        "health_tendency": "对应心火、睡眠、眼睛、血压、焦虑。火弱时容易动力不足、畏难退缩。",
        "when_too_strong": "容易急躁冲动、睡眠不稳、情绪外放、行动力过强忽略细节反馈。",
        "when_too_weak": "表达不足、热情不够、曝光不足、行动动力弱、容易缺乏存在感和被忽视感。",
        "if_favorable": "适合增加规律社交、适度运动、写作表达和审美训练，让行动力更稳定。",
        "if_unfavorable": "不宜过度曝光、情绪化表达或急于证明自己，重要决策宜留冷静期。",
        "real_life_advice": [
            "适合通过写作、演讲、分享建立个人影响力",
            "重要决定留出冷静期，避免情绪驱动决策",
            "睡眠和心血管健康需特别关注",
            "适度运动有助于稳定火能量，避免过亢",
        ],
    },

    "土": {
        "basic_meaning": "土主承载，代表稳定、现实、资源、信用、积累、组织和脾胃健康。",
        "career_meaning": "喜土时，事业适合管理、地产、供应链、服务、运营、组织建设、后勤、资源整合。",
        "wealth_meaning": "财富靠稳定积累、资产、土地房产、组织资源和长期沉淀，适合实体和平台型业务。",
        "relationship_meaning": "感情重稳定感、责任担当、现实基础和安全感；过旺时容易保守或缺乏新鲜感。",
        "health_tendency": "对应脾胃、消化、湿气、代谢和压力堆积。土弱时容易消化吸收不良。",
        "when_too_strong": "容易保守迟缓、压力积累、湿气重、行动偏慢、缺乏灵活应变。",
        "when_too_weak": "缺乏稳定性、难以沉淀积累、现实承载不足、容易缺乏安全感和根基。",
        "if_favorable": "适合建立稳定作息、预算习惯、收纳体系和可持续的家庭支持系统。",
        "if_unfavorable": "不宜过度囤积、保守抗拒变化或陷入琐事管理，建议保留适度弹性。",
        "real_life_advice": [
            "建议建立稳定的作息和财务预算习惯",
            "适合从事长期积累型工作方向",
            "脾胃健康需关注，注意饮食规律",
            "稳定之外也要给成长留空间，避免过于保守",
        ],
    },

    "金": {
        "basic_meaning": "金主收敛，代表规则、判断、执行、审美、技术、标准化和肺皮毛系统。",
        "career_meaning": "喜金时，事业适合金融、法律、管理、技术研发、机械、审计、决策、标准化、精修方向。",
        "wealth_meaning": "财富靠规则制度、专业能力、金融工具、技术标准和执行力创造，适合专业服务类行业。",
        "relationship_meaning": "感情重边界感、原则、理性和审美匹配；过旺时容易关系冷感或要求过高。",
        "health_tendency": "对应呼吸系统、皮肤、鼻喉、紧绷感。金弱时容易免疫力不足、气血循环弱。",
        "when_too_strong": "容易刚硬挑剔、关系表达偏冷、压力内收、完美主义导致行动卡顿。",
        "when_too_weak": "边界不足、规则感弱、执行力不足、审美和专业技能积累慢。",
        "if_favorable": "适合通过清晰边界、任务清单、技能训练和财务纪律增强金的秩序感。",
        "if_unfavorable": "不宜过度追求完美、苛责他人或自己，沟通时保留弹性。",
        "real_life_advice": [
            "建议培养专业技能和标准化工作习惯",
            "与人沟通时注意语气和边界软硬适度",
            "呼吸和皮肤健康需关注，注意保暖和防护",
            "压力管理很重要，避免长期紧绷状态",
        ],
    },

    "水": {
        "basic_meaning": "水主流动，代表智慧、信息、关系、适应力、资源流动和肾水系统。",
        "career_meaning": "喜水时，事业适合咨询、信息处理、贸易、物流、传播、酒水、流动型行业、跨地域发展。",
        "wealth_meaning": "财富靠信息差、流动资源、渠道、贸易和跨界连接，适合信息整合和资源配置。",
        "relationship_meaning": "感情灵活重沟通、情绪流动、适应力强；过旺时容易漂浮不定、缺乏稳定边界。",
        "health_tendency": "对应腰肾、泌尿、睡眠恢复、精力储备和寒湿倾向。水弱时容易恢复力不足。",
        "when_too_strong": "容易犹豫漂浮、情绪波动、行动力分散、缺乏定力和持久专注。",
        "when_too_weak": "适应力不足、资源流动不畅、恢复力弱、信息整合能力不足。",
        "if_favorable": "适合保持信息流动、复盘记录、旅行学习和弹性安排，让连接更顺畅。",
        "if_unfavorable": "不宜过度分散注意力、频繁切换方向或情绪化决策，需配合明确计划执行。",
        "real_life_advice": [
            "建议保持信息输入和复盘记录的习惯",
            "适合跨地域、跨领域发展，但每次专注一个方向",
            "腰肾和泌尿健康需关注，避免熬夜和过度消耗",
            "需要明确目标和执行计划，避免行动过于分散",
        ],
    },
}


def generate_five_element_deep_report(chart: dict, luck_data: dict | None = None) -> dict:
    """
    生成五行结构深度报告。
    """
    five_elements = chart.get("five_elements", {})
    if not five_elements:
        return {
            "element_overview": "五行数据暂不可用。",
            "element_balance_summary": "",
            "strong_elements": [],
            "weak_elements": [],
            "favorable_elements": [],
            "unfavorable_elements": [],
            "element_details": {},
            "source_ids": [],
            "source_titles": [],
        }

    summary = element_summary(five_elements)
    strength = chart.get("day_master_strength", {})
    favorable = strength.get("favorable_elements", []) or []
    unfavorable = strength.get("unfavorable_elements", []) or []

    # 强弱排序
    sorted_by_score = sorted(summary.items(), key=lambda x: -x[1]["score"])
    strong_elements = [e for e, s in sorted_by_score if s["strength"] == "偏旺"]
    weak_elements = [e for e, s in sorted_by_score if s["strength"] == "偏弱"]
    if not strong_elements and sorted_by_score:
        strong_elements = [sorted_by_score[0][0]]
    if not weak_elements and len(sorted_by_score) > 1:
        weak_elements = [sorted_by_score[-1][0]]

    # 五行齐全判断
    all_elements_present = all(
        float(five_elements.get(e, 0)) > 0 for e in FIVE_ELEMENT_ORDER
    )

    # 偏枯判断
    scores = [float(five_elements.get(e, 0)) for e in FIVE_ELEMENT_ORDER]
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    is_biased = (max_score - min_score) > 20 if max_score > 0 else False

    # 总体描述
    strongest = strong_elements[0] if strong_elements else "无明显偏旺"
    weakest = weak_elements[0] if weak_elements else "无明显偏弱"
    element_overview = (
        f"当前命局五行{'齐全' if all_elements_present else '不够齐全（部分五行偏弱或缺少）'}，"
        f"整体结构{'偏枯' if is_biased else '相对平衡'}。"
        f"最强五行为「{strongest}」，最弱五行为「{weakest}」。"
    )

    # 初始化大运流年影响

    # 每个五行的详细数据
    element_details = {}
    for element in FIVE_ELEMENT_ORDER:
        detail = ELEMENT_DEEP_DETAILS.get(element, {})
        score = float(five_elements.get(element, 0))
        total = sum(float(v) for v in five_elements.values()) or 1
        ratio = round(score / total * 100, 1)
        level = summary.get(element, {}).get("strength", "中等")
        element_details[element] = {
            "element": element,
            "score": score,
            "ratio": ratio,
            "level": level,
            "is_favorable": element in favorable,
            "is_unfavorable": element in unfavorable,
            "basic_meaning": detail.get("basic_meaning", ""),
            "in_this_chart": f"当前命局{level}，分数为{score}，占比{ratio}%。"
                             f"{'为喜用五行，适合后天加强。' if element in favorable else ''}"
                             f"{'为忌神五行，后天需谨慎应对。' if element in unfavorable else ''}"
                             f"{'整体偏旺。' if level == '偏旺' else ''}"
                             f"{'整体偏弱。' if level == '偏弱' else ''}",
            "career_meaning": detail.get("career_meaning", ""),
            "wealth_meaning": detail.get("wealth_meaning", ""),
            "relationship_meaning": detail.get("relationship_meaning", ""),
            "health_tendency": detail.get("health_tendency", ""),
            "when_too_strong": detail.get("when_too_strong", ""),
            "when_too_weak": detail.get("when_too_weak", ""),
            "if_favorable": detail.get("if_favorable", ""),
            "if_unfavorable": detail.get("if_unfavorable", ""),
            "real_life_advice": detail.get("real_life_advice", []),
            "source_ids": ["yuanhai_ziping", "sanming_tonghui", "ditiansui", "qiongtong_baojian"],
        }

    # 大运流年影响
    luck_influence = ""
    if luck_data and luck_data.get("available"):
        dayun_list = luck_data.get("dayun_list", [])
        if dayun_list:
            current = dayun_list[0] if len(dayun_list) > 0 else {}
            current_pillar = current.get("pillar", "")
            if current_pillar:
                current_gan = current_pillar[0] if current_pillar else ""
                current_zhi = current_pillar[1] if len(current_pillar) > 1 else ""
                from ..bazi.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
                ce = STEM_ELEMENTS.get(current_gan, "")
                ze = BRANCH_MAIN_ELEMENTS.get(current_zhi, "")
                focus = ce or ze
                if focus and focus in favorable:
                    luck_influence = f"当前大运{current_pillar}强化了{focus}五行，"
                    "是喜用五行的有利阶段。"
                elif focus and focus in unfavorable:
                    luck_influence = f"当前大运{current_pillar}引动了{focus}五行，"
                    "该阶段该五行并非喜用，建议适当规避。"
                else:
                    luck_influence = f"当前大运{current_pillar}涉及的五行{focus}，"
                    "建议结合具体月份判断喜忌影响。"

    # 平衡摘要
    _bp = [
        "命局五行整体" + ("偏旺于" if strongest else "") + strongest,
        ("，偏弱于" if weakest else "") + weakest + "。",
        "五行齐全，结构相对完整。" if all_elements_present else "某些五行偏弱或缺少，在相应领域需后天补足。",
        "整体结构偏枯，在某领域容易出现极端倾向。" if is_biased else "整体结构较为平衡。",
    ]
    if luck_influence:
        _bp.append(" " + luck_influence)
    element_balance_summary = "".join(_bp)

    evidence = [
        "五行强弱基于四柱天干、地支、藏干计分",
        "喜忌判断基于日主得令、得地、得势综合分析",
        "五行解释参考《渊海子平》《三命通会》《滴天髓》《穷通宝鉴》",
    ]
    source_titles = ["《渊海子平》", "《三命通会》", "《滴天髓》", "《穷通宝鉴》"]

    return {
        "element_overview": element_overview,
        "element_balance_summary": element_balance_summary,
        "strong_elements": strong_elements,
        "weak_elements": weak_elements,
        "favorable_elements": favorable,
        "unfavorable_elements": unfavorable,
        "element_details": element_details,
        "career_implications": _combine_implications(element_details, "career_meaning"),
        "wealth_implications": _combine_implications(element_details, "wealth_meaning"),
        "relationship_implications": _combine_implications(element_details, "relationship_meaning"),
        "health_implications": _combine_implications(element_details, "health_tendency"),
        "adjustment_advice": _build_adjustment_advice(element_details, favorable, unfavorable),
        "evidence": evidence,
        "source_ids": ["yuanhai_ziping", "sanming_tonghui", "ditiansui", "qiongton_baojian"],
        "source_titles": source_titles,
    }


def _combine_implications(element_details: dict, field: str) -> str:
    """组合多个五行的意义到一段文字。"""
    parts = []
    for elem, detail in element_details.items():
        text = detail.get(field, "")
        if text:
            level = detail.get("level", "")
            is_fav = detail.get("is_favorable", False)
            prefix = f"【{elem}（{level}，{'喜用' if is_fav else '忌神'}）】"
            parts.append(f"{prefix}{text}")
    return "\n\n".join(parts)


def _build_adjustment_advice(element_details: dict, favorable: list[str], unfavorable: list[str]) -> list[str]:
    """生成调整建议列表。"""
    advices = []
    for elem, detail in element_details.items():
        is_fav = detail.get("is_favorable", False)
        advice_list = detail.get("real_life_advice", [])
        if is_fav and advice_list:
            for a in advice_list:
                advices.append(f"【{elem}·喜用】{a}")
        if not is_fav and advice_list:
            risk_advices = advice_list[-2:] if len(advice_list) > 2 else advice_list
            for a in risk_advices:
                advices.append(f"【{elem}·忌神】{a}")

    if not advices:
        advices.append("命局五行相对平衡，建议保持当前节奏，结合现实阶段灵活调整。")
    return advices[:8]
