"""
命局总论 — 综合性命理评价。

基于四柱、五行、十神、藏干、日主强弱、命局类型等信息，
为算命者提供关于财富格局、桃花/感情趋势、健康长寿潜力的综合判断。
"""

from __future__ import annotations

from core.bazi_constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_MAIN_ELEMENTS,
    EARTHLY_BRANCHES,
    STEM_ELEMENTS,
)
from core.chart_type import classify_chart


# ============================================================
# 辅助函数
# ============================================================

def _get_element_strength_labels(five_elements: dict) -> dict[str, str]:
    """返回五行强弱标签。"""
    if not five_elements:
        return {}
    total = sum(float(v) for v in five_elements.values()) or 1
    result = {}
    for elem, score in five_elements.items():
        pct = float(score) / total * 100
        if pct >= 35:
            result[elem] = "偏旺"
        elif pct < 10:
            result[elem] = "偏弱"
        else:
            result[elem] = "适中"
    return result


def _get_ten_god_groups(ten_god_counts: dict) -> dict[str, int]:
    """汇总十神类别。"""
    return {
        "wealth": ten_god_counts.get("正财", 0) + ten_god_counts.get("偏财", 0),
        "output": ten_god_counts.get("食神", 0) + ten_god_counts.get("伤官", 0),
        "authority": ten_god_counts.get("正官", 0) + ten_god_counts.get("七杀", 0),
        "resource": ten_god_counts.get("正印", 0) + ten_god_counts.get("偏印", 0),
        "peer": ten_god_counts.get("比肩", 0) + ten_god_counts.get("劫财", 0),
    }


def _has_ta_hua(branch: str) -> bool:
    """判断是否为桃花星（子午卯酉）。"""
    return branch in ("子", "午", "卯", "酉")


def _count_branch_in_pillars(pillars: dict, target: str) -> int:
    """统计地支在四柱中出现次数。"""
    count = 0
    for key in ("year", "month", "day", "hour"):
        zhi = pillars.get(key, {}).get("zhi", "")
        if zhi == target:
            count += 1
    return count


def _get_peach_blossoms(pillars: dict) -> list[str]:
    """
    查找命局桃花。
    以日支查：申子辰在酉，巳酉丑在午，寅午戌在卯，亥卯未在子。
    """
    day_zhi = pillars.get("day", {}).get("zhi", "")
    if not day_zhi:
        return []
    peach_rule = {
        "申": "酉", "子": "酉", "辰": "酉",
        "巳": "午", "酉": "午", "丑": "午",
        "寅": "卯", "午": "卯", "戌": "卯",
        "亥": "子", "卯": "子", "未": "子",
    }
    peach_zhi = peach_rule.get(day_zhi, "")
    if not peach_zhi:
        return []

    found = []
    for key in ("year", "month", "day", "hour"):
        zhi = pillars.get(key, {}).get("zhi", "")
        if zhi == peach_zhi:
            found.append(f"{key}支{zhi}")
    return found


# ============================================================
# 财富评断
# ============================================================

def assess_wealth(chart: dict) -> dict:
    """
    综合评断命局财富格局。

    参考来源：渊海子平（十神财星）、三命通会（财星旺衰）、子平真诠（用神格局）、穷通宝鉴（调候对财的影响）。
    """
    ten_god_counts = chart.get("ten_god_counts", {})
    strength = chart.get("day_master_strength", {})
    pillars = chart.get("pillars", {})
    five_elements = chart.get("five_elements", {})
    chart_type_result = classify_chart(chart)

    day_master = chart.get("day_master", "")
    day_master_element = STEM_ELEMENTS.get(day_master, "")

    groups = _get_ten_god_groups(ten_god_counts)
    wealth_stars = groups["wealth"]
    favorable = strength.get("favorable_elements", [])
    unfavorable = strength.get("unfavorable_elements", [])
    strength_label = strength.get("strength", "中和")

    # 财星所在的元素
    wealth_elements = set()
    # 财星在五行上属于日主所克之元素（正财偏财同五行）
    # 甲/乙(木)→土, 丙/丁(火)→金, 戊/己(土)→水, 庚/辛(金)→木, 壬/癸(水)→火
    wealth_el_map = {"甲": "土", "乙": "土", "丙": "金", "丁": "金",
                      "戊": "水", "己": "水", "庚": "木", "辛": "木",
                      "壬": "火", "癸": "火"}
    wealth_el = wealth_el_map.get(day_master, "")
    if ten_god_counts.get("正财", 0) > 0:
        wealth_elements.add(wealth_el)
    if ten_god_counts.get("偏财", 0) > 0:
        wealth_elements.add(wealth_el)

    # 财星是否喜用
    wealth_is_favorable = bool(wealth_elements & set(favorable))
    wealth_is_unfavorable = bool(wealth_elements & set(unfavorable))

    # 判断财星强度
    total_scored = sum(ten_god_counts.values()) or 1
    wealth_ratio = wealth_stars / total_scored

    # 财星在四柱的位置
    wealth_positions = []
    for key in ("year", "month", "day", "hour"):
        tg = chart.get("ten_gods", {}).get(key, {}).get("gan", "")
        if tg in ("正财", "偏财"):
            wealth_positions.append(key)

    # 判断特殊组合
    specials = chart_type_result.get("special_combinations", [])
    has_shi_sheng_cai = "食神生财" in specials

    # ===== 生成评估 =====
    level = "普通"
    reasons = []
    strengths_parts = []
    weaknesses_parts = []
    advice_parts = []

    # 财星数量判断
    if wealth_stars >= 3:
        strengths_parts.append("命局财星数量较多，对财富机会较敏感，容易发现收益型资源。")
        if strength_label == "身强":
            level = "中上"
            strengths_parts.append("日主强旺能担财，有能力承接和运营较大规模的财富资源。")
        elif strength_label == "身弱":
            level = "波动"
            weaknesses_parts.append("但日主偏弱，财多身弱容易出现'富屋贫人'的情况——机会虽多但实际承担困难。")
            advice_parts.append("建议借力平台、合作或等待扶身大运再发力，不宜独自重仓。")
    elif wealth_stars == 2:
        strengths_parts.append("命局有财星透出，对财务管理和资源运营有一定敏感度。")
        level = "中等偏上" if strength_label == "身强" else "中等"
    elif wealth_stars == 1:
        strengths_parts.append("命局有财星但数量不多，财富更适合以稳定收入为主。")
        level = "中等"
    else:
        strengths_parts.append("命局财星不显，财富来源更依赖技能输出、专业服务和长期积累型路径。")
        level = "技能型"

    # 财星喜忌判断
    if wealth_is_favorable:
        strengths_parts.append("财星五行属于命局喜用，求财过程中能量补充和外部支持较明显。")
        if level == "普通":
            level = "中等"
    elif wealth_is_unfavorable:
        weaknesses_parts.append("财星五行属于命局忌神，求财过程容易伴随消耗、压力或额外风险。")
        advice_parts.append("涉及投资、合作或大额支出时建议多评估几轮再做决定。")
        if level == "中上":
            level = "波动"
        elif level == "普通":
            level = "挑战型"

    # 财星位置判断
    if "day" in wealth_positions:
        strengths_parts.append("财星在日柱，中年阶段财富积累能力较强，适合长期经营。")
    if "month" in wealth_positions:
        strengths_parts.append("财星在月柱，青年阶段就有理财意识或通过工作积累财富基础。")
    if "hour" in wealth_positions:
        strengths_parts.append("财星在时柱，晚年或子女运中财富有积累潜力。")

    # 特殊组合
    if has_shi_sheng_cai:
        strengths_parts.append("命局有食神生财组合，才华和技能可直接转化为财富，适合靠专业能力和服务质量变现。")
        if "中" in level:
            level = "中等偏上"

    # 五行调候对财的影响
    element_labels = _get_element_strength_labels(five_elements)
    wealth_element = "土"  # 财星五行通常为土（对于木日主是土，对于火日主是金，等等）
    wealth_el = wealth_el_map.get(day_master, "")
    if wealth_el and element_labels.get(wealth_el) == "偏旺":
        strengths_parts.append(f"{wealth_el}五行偏旺（财星所属），财的势能较强。")
        if strength_label != "身强":
            weaknesses_parts.append(f"但{wealth_el}旺而日主不旺，需注意承受力和现金流节奏。")

    # 综合评级
    if level == "中上":
        summary = "中等偏上。命局具备较好的财富承接条件和资源敏感度，适合在稳定经营和专业积累中持续扩大财源。"
    elif level == "中等偏上":
        summary = "中等偏上。命局有不错的财富基础，结合特长和能力可以在积累中创造稳定收益。"
    elif level == "中等":
        summary = "中等。命局财富能量在正常范围，适合以稳定收入为主、副业尝试为辅的财务策略。"
    elif level == "波动":
        summary = "波动型。财富机会存在但承接难度较大，建议以保守稳健为主，等待扶身运势再行发力。"
    elif level == "技能型":
        summary = "技能型。命局财星不显但食伤有力，更适合通过专业输出、技术服务和内容价值创造财富。"
    elif level == "挑战型":
        summary = "挑战型。求财过程容易伴随额外压力和消耗，建议放慢节奏，多评估项目周期和风险边界。"
    else:
        summary = "需结合大运流年进一步判断。当前命局财富格局未呈现明显倾向。"
    reasons = strengths_parts + weaknesses_parts

    return {
        "level": level,
        "summary": summary,
        "strengths": strengths_parts,
        "weaknesses": weaknesses_parts,
        "advice": advice_parts if advice_parts else ["财富策略建议以稳健积累为主，避免孤注一掷式的投入。"],
        "basis": "基于渊海子平财星理论、三命通会财星旺衰判断和子平真诠用神格局，结合日主强弱与财星的匹配度进行评估。",
        "source_titles": ["渊海子平", "三命通会", "子平真诠"],
    }


# ============================================================
# 桃花/感情评断
# ============================================================

def assess_romance(chart: dict) -> dict:
    """
    综合评断命局桃花和感情趋势。

    参考来源：渊海子平（配偶星、桃花）、三命通会（感情结构）、子平真诠（用神与配偶）。
    """
    ten_god_counts = chart.get("ten_god_counts", {})
    strength = chart.get("day_master_strength", {})
    pillars = chart.get("pillars", {})
    profile = chart.get("profile", {})
    groups = _get_ten_god_groups(ten_god_counts)
    day_master = chart.get("day_master", "")

    gender = profile.get("gender", "")
    favorable = strength.get("favorable_elements", [])
    unfavorable = strength.get("unfavorable_elements", [])

    # ---- 桃花星 ----
    peaches = _get_peach_blossoms(pillars)
    peach_count = len(peaches)
    day_zhi = pillars.get("day", {}).get("zhi", "")

    # ---- 配偶星 ----
    # 男命以正财为妻星，偏财为偏妻/情人
    # 女命以正官为夫星，七杀为偏夫/情人
    spousal_stars = 0
    if gender == "女":
        spousal_stars = ten_god_counts.get("正官", 0) + ten_god_counts.get("七杀", 0)
    else:
        spousal_stars = ten_god_counts.get("正财", 0) + ten_god_counts.get("偏财", 0)

    # ---- 感情表达力 ----
    expression_stars = groups["output"]

    # ---- 日支与配偶宫 ----
    # 日支是配偶宫
    spouse_palace = day_zhi
    spouse_element = BRANCH_MAIN_ELEMENTS.get(spouse_palace, "")

    # 日支是否为喜用
    spouse_is_favorable = spouse_element in favorable
    spouse_is_unfavorable = spouse_element in unfavorable

    # 日支是否为桃花
    day_is_peach = _has_ta_hua(spouse_palace)

    # 日支是否逢冲
    day_zhi_clash_map = {
        "子": "午", "丑": "未", "寅": "申", "卯": "酉",
        "辰": "戌", "巳": "亥", "午": "子", "未": "丑",
        "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳",
    }
    day_clash_zhi = day_zhi_clash_map.get(spouse_palace, "")
    day_has_clash = any(
        pillars.get(k, {}).get("zhi", "") == day_clash_zhi
        for k in ("year", "month", "hour")
    )

    # ===== 生成评估 =====
    level = "普通"
    strengths_parts = []
    weaknesses_parts = []
    advice_parts = []
    detail_parts = []

    # 桃花星判断
    if peach_count >= 3:
        level = "丰富"
        strengths_parts.append("命局桃花星较多，异性缘较好，容易在不同阶段遇到感情缘分。")
        weaknesses_parts.append("桃花多也意味着感情选择面广，需要留意对稳定关系的影响。")
        advice_parts.append("建议在感情中尽早确认自己的核心需求，不要被表面吸引力带着走。")
        detail_parts.append(f"命中桃花出现在{'、'.join(peaches)}。")
    elif peach_count == 2:
        strengths_parts.append("命局有桃花星，感情缘分和质量在适婚年龄段有较好体现。")
        level = "良好"
        detail_parts.append(f"桃花出现在{'、'.join(peaches)}。")
    elif peach_count == 1:
        strengths_parts.append("命局有桃花星但不泛滥，感情缘分较为清新。")
        level = "中等"
        detail_parts.append(f"桃花在{peaches[0]}。")
    else:
        strengths_parts.append("命局不以桃花星见长，感情更注重内在契合度和现实磨合。")
        level = "踏实型"

    # 配偶星判断
    if spousal_stars >= 3:
        strengths_parts.append("配偶星较明显，对感情和婚姻的重视程度较高。")
        if gender == "女":
            strengths_parts.append("官杀多现时，需要注意区分喜欢的人与适合的人之间的差异。")
            advice_parts.append("选择伴侣时建议综合考量责任匹配、性格契合和现实条件。")
        else:
            strengths_parts.append("财星多现时，在择偶中会自然考虑实际条件和匹配度。")
            advice_parts.append("宜把感情承诺和现实计划同步推进。")
        if level == "普通":
            level = "有缘型"
    elif spousal_stars == 0:
        weaknesses_parts.append("配偶星不显于四柱天干（藏支需结合大运流年引动），感情缘分更依赖运势阶段推动。")
        advice_parts.append("适合在社会活动和人际拓展中主动创造机会，配偶星静待大运引动。")
        if level == "普通":
            level = "稳重型"
    else:
        if level == "普通":
            level = "中等"

    # 日支配偶宫判断
    if spouse_is_favorable:
        strengths_parts.append("配偶宫五行属于命局喜用，夫妻关系对整体运势有积极助益。")
    elif spouse_is_unfavorable:
        weaknesses_parts.append("配偶宫五行属于命局忌神，亲密关系中需要更多耐心和沟通来化解分歧。")
        advice_parts.append("婚后需要更多经营关系的心态，建议把期待和分歧尽早摊开沟通。")

    if day_is_peach:
        strengths_parts.append("日支坐桃花，个人魅力较强，在亲密关系中容易吸引对方注意。")
        advice_parts.append("桃花坐日支者，建议在关系进入稳定期后有意识增加责任沟通，减少表面吸引的依赖。")

    if day_has_clash:
        weaknesses_parts.append(f"日支{spouse_palace}与命局其他地支相冲，感情关系容易受到外部因素（如工作变动、家庭意见、居住调整）的干扰。")
        advice_parts.append("感情中建议保持独立判断，减少外界干扰对核心关系的影响。")

    # 感情表达力
    if expression_stars >= 3:
        strengths_parts.append("食伤充足，善于表达情感和制造浪漫，也容易在关系中展现真实自己。")
        advice_parts.append("注意把表达和行动统一起来，避免只说不做或情绪化表达影响关系稳定性。")
    elif expression_stars == 0:
        strengths_parts.append("感情表达偏内敛，更适合以实际行动和长期陪伴来建立信任。")
        advice_parts.append("建议在关系中主动练习用语言表达感受和需求，避免完全期待对方猜。")

    # 综合评级
    level_parts = {
        "丰富": "丰富。命局桃花能量较活跃，感情缘分较容易到来，同时需要留意选择和沉淀。",
        "良好": "良好。桃花与配偶星搭配得当，感情缘分属于质量较高的类型。",
        "中等": "中等。感情节奏以稳为主，缘分到来时用心经营即可。",
        "踏实型": "踏实型。不以桃花见长，但感情真诚持久，适合长期稳定关系。",
        "有缘型": "有缘型。配偶星较明显，婚姻缘分在命中较受重视。",
        "稳重型": "稳重型。配偶星不显，需要运势引动，感情节奏较慢但更踏实。",
    }
    summary = level_parts.get(level, "需结合大运流年具体引动来进一步判断感情走势。")

    return {
        "level": level,
        "summary": summary,
        "strengths": strengths_parts,
        "weaknesses": weaknesses_parts,
        "advice": advice_parts if advice_parts else ["感情方面建议以真诚沟通和稳定陪伴为基础，避免因表面吸引忽略长期兼容性。"],
        "detail": detail_parts,
        "basis": "基于渊海子平配偶星和桃花理论、三命通会感情结构判断、子平真诠用神与配偶关系，结合日支配偶宫五行喜忌进行评估。",
        "source_titles": ["渊海子平", "三命通会", "子平真诠"],
    }


# ============================================================
# 健康长寿评断
# ============================================================

def assess_health(chart: dict) -> dict:
    """
    综合评断命局健康与长寿潜力。

    参考来源：穷通宝鉴（五行调候、寒暖燥湿）、三命通会（五行与脏腑对应）、渊海子平（五行过不及）。
    """
    five_elements = chart.get("five_elements", {})
    strength = chart.get("day_master_strength", {})
    pillars = chart.get("pillars", {})
    day_master = chart.get("day_master", "")

    favorable = strength.get("favorable_elements", [])
    unfavorable = strength.get("unfavorable_elements", [])
    strength_label = strength.get("strength", "中和")

    element_labels = _get_element_strength_labels(five_elements)

    # 五行与脏腑对应关系
    ELEMENT_ORGANS = {
        "木": {"organs": ["肝胆", "筋骨", "眼睛"], "excess": "容易肝胆火旺、头痛、肩颈紧张", "deficiency": "容易疲劳乏力、视力下降、筋腱不适"},
        "火": {"organs": ["心脏", "小肠", "血液循环"], "excess": "容易心火偏旺、焦虑、失眠、口腔溃疡", "deficiency": "容易气血不足、畏寒、精神不振"},
        "土": {"organs": ["脾胃", "肌肉", "皮肤"], "excess": "容易消化不良、腹胀、血糖波动、皮肤油腻", "deficiency": "容易食欲不振、消瘦、免疫力偏低"},
        "金": {"organs": ["肺", "大肠", "呼吸系统", "皮肤"], "excess": "容易皮肤敏感、呼吸系统紧张、便秘", "deficiency": "容易气虚、感冒频繁、皮肤干燥"},
        "水": {"organs": ["肾脏", "膀胱", "内分泌"], "excess": "容易水肿、腰膝酸软、代谢偏慢", "deficiency": "容易精力不足、记忆力下降、水液代谢紊乱"},
    }

    element_status = _get_element_strength_labels(five_elements)
    total = sum(float(v) for v in five_elements.values()) or 1
    elements_present = [e for e, s in five_elements.items() if float(s) > 0]
    elements_strong = [e for e in elements_present if element_status.get(e) == "偏旺"]
    elements_weak = [e for e in elements_present if element_status.get(e) == "偏弱"]

    # ===== 生成评估 =====
    level = "普通"
    strengths_parts = []
    weaknesses_parts = []
    advice_parts = []
    organ_attention = []

    # 五行完整度判断
    missing_elements = [e for e in ["木", "火", "土", "金", "水"] if e not in elements_present]
    if len(missing_elements) <= 1:
        strengths_parts.append("五行格局较为完整，先天身体素质基础较好。")
        level = "良好"
    elif len(missing_elements) >= 3:
        weaknesses_parts.append("五行缺三行及以上，体内能量分布不够均衡，需要通过后天的饮食、作息和运动来主动调养。")
        level = "挑战型"
        advice_parts.append("建议定期体检，针对性地调整生活方式来补足五行偏弱对应的脏腑。")
    else:
        strengths_parts.append("五行基本齐全，整体健康基础在正常范围。")

    # 五行过旺判断
    for elem in elements_strong:
        organ_info = ELEMENT_ORGANS.get(elem, {})
        organ_attention.append(f"{elem}偏旺：{organ_info.get('excess', '需注意对应脏腑')}")
        weaknesses_parts.append(f"{elem}五行偏旺，{organ_info.get('excess', '需要留意对应脏腑过度消耗')}。")
        advice_parts.append(f"{elem}偏旺时建议减少对应脏腑的额外消耗，增加克制五行的生活习惯。")

    # 五行偏弱判断
    for elem in elements_weak:
        organ_info = ELEMENT_ORGANS.get(elem, {})
        organ_attention.append(f"{elem}偏弱：{organ_info.get('deficiency', '需注意养护')}")
        weaknesses_parts.append(f"{elem}五行偏弱，{organ_info.get('deficiency', '需要加强对应脏腑的养护')}。")
        advice_parts.append(f"{elem}偏弱时建议通过饮食、作息和环境来补充对应能量。")

    # 日主强弱判断
    if strength_label == "身强":
        strengths_parts.append("日主强旺，先天承受力和恢复力较好，不易被环境压力击倒。")
        if "良好" not in level:
            level = "良好"
    elif strength_label == "身弱":
        weaknesses_parts.append("日主偏弱，需要注意精力和免疫力的维护，避免长期透支和高压环境。")
        advice_parts.append("建议建立规律作息，避免熬夜和高强度持续消耗。")
        if "良好" not in level:
            level = "注意调养"

    # 调候判断（季节寒暖）
    month_zhi = pillars.get("month", {}).get("zhi", "")
    is_winter = month_zhi in ("亥", "子", "丑")
    is_summer = month_zhi in ("巳", "午", "未")
    if is_winter and day_master in ("壬", "癸", "庚", "辛"):
        weaknesses_parts.append("出生在冬季且日主偏寒，阳气不足时需要特别注意手脚冰凉、循环系统和季节性情绪管理。")
        advice_parts.append("建议多接触阳光，增加温性饮食，冬季注意保暖和运动。")
        if level == "普通":
            level = "注意调养"
    elif is_summer and day_master in ("丙", "丁", "戊", "己"):
        weaknesses_parts.append("出生在夏季且日主偏热，阳气过旺时容易心火亢盛、情绪急躁、睡眠质量偏低。")
        advice_parts.append("建议适当增加水性和凉性调节，注意补水、避暑和情绪管理。")
        if level == "普通":
            level = "注意调养"

    # 长寿相关判断
    longevity_notes = []
    if len(missing_elements) <= 1 and strength_label == "身强":
        longevity_notes.append("五行较全且日主强旺，从命理趋势看有较好的健康基础支撑长寿潜力。")
    elif len(missing_elements) >= 3 and strength_label == "身弱":
        longevity_notes.append("五行欠缺较多且日主偏弱，长寿潜力更依赖后天持续调养和规律作息。")
    else:
        longevity_notes.append("长寿潜力处于中常范围，健康的长期走势更取决于后天生活习惯和心态调整。")

    # 综合评级
    level_map = {
        "良好": "良好。五行格局较完整，日主承接力强，先天健康基础良好。注意日常作息规律和定期保养。",
        "普通": "普通。健康状态在正常范围，个别脏腑需要针对性调养，建议保持规律体检和生活节奏。",
        "注意调养": "需调养。命局有偏旺或偏弱的五行，对应脏腑和系统需要重点养护。有意识地调整饮食、作息和运动可以显著改善。",
        "挑战型": "挑战型。五行失衡较多，需要系统性地进行健康管理和调理。建议定期体检、合理安排作息、注重情绪调节。",
    }
    summary = level_map.get(level, "需结合大运流年进一步判断健康走势。")

    return {
        "level": level,
        "summary": summary,
        "strengths": strengths_parts,
        "weaknesses": weaknesses_parts,
        "advice": advice_parts if advice_parts else ["建议保持规律作息、适度运动和定期体检。"],
        "organ_attention": organ_attention,
        "longevity": longevity_notes,
        "basis": "基于穷通宝鉴五行调候理论、三命通会五行与脏腑对应关系、渊海子平五行过不及判断，结合季节寒暖和日主强弱进行评估。",
        "source_titles": ["穷通宝鉴", "三命通会", "渊海子平"],
    }


# ============================================================
# 命局总论 — 综合三方面评估
# ============================================================

def life_overview(chart: dict) -> dict:
    """
    综合生成命局总论。

    返回财富、桃花/感情、健康长寿三个维度的评估。
    """
    wealth = assess_wealth(chart)
    romance = assess_romance(chart)
    health = assess_health(chart)

    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {}).get("strength", "中和")

    opening = (
        f"此命局日主为{day_master}，命局强弱初判为{strength}。"
        "以下从财富格局、感情趋势、健康基础三个维度进行综合评价，"
        "适合作为自我观察、人生规划和后续深入分析的参考。"
    )

    return {
        "opening": opening,
        "wealth": wealth,
        "romance": romance,
        "health": health,
    }
