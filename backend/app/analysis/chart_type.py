"""命盘类型分类 —— 基于日主强弱、五行分布、十神统计做规则分类。"""

from __future__ import annotations

from ..fortune.report_diversity import build_chart_signature_text

TEN_GOD_GROUPS = {
    "财旺格": ["正财", "偏财"],
    "官杀格": ["正官", "七杀"],
    "印旺格": ["正印", "偏印"],
    "食伤格": ["食神", "伤官"],
    "比劫格": ["比肩", "劫财"],
}

COMBINATION_EXPLANATIONS = {
    "杀印相生": {
        "meaning": "七杀与正印/偏印同时出现，形成'杀印相生'的贵格。",
        "effect": "七杀代表压力、竞争和魄力，印星代表学识、贵人和庇护。杀印相生意味着你能将压力和竞争转化为学习和成长的动力，在困境中得到贵人相助。",
        "career": "适合管理、军警、法律、工程、医疗等需要承受压力并持续学习的职业。杀印相生格局的人往往能在高压环境中脱颖而出。",
        "advice": "善用压力转化为学习动力，遇到困难时主动寻求贵人帮助。杀印相生贵在'转化'，将挑战视为提升自己的机会。",
    },
    "食神生财": {
        "meaning": "食神与正财/偏财同时出现，形成'食神生财'的富格。",
        "effect": "食神代表才华、创意和口福，财星代表财富和资源。食神生财意味着你的才华和创意可以直接转化为财富，通过技术、艺术或服务获得收益。",
        "career": "适合创意、设计、咨询、教育培训、餐饮、娱乐等用才华换取财富的职业。",
        "advice": "发挥专业技能和创意能力，将它们变成可持续的收入来源。注意保护知识产权，善用个人品牌。",
    },
    "伤官配印": {
        "meaning": "伤官与正印/偏印同时出现，形成'伤官配印'的聪慧格。",
        "effect": "伤官代表才华、叛逆和非凡创意，印星代表学识和修养。伤官有印制，才华不会泛滥无度，而是变得有深度和系统性。这种格局的人聪明且有独到见解。",
        "career": "适合科研、学术、写作、传媒、艺术、设计等需要创造力和深度思考的职业。",
        "advice": "发挥创意和才华的同时，注意用学识和修养来约束锋芒。伤官配印贵在'平衡'，既要有创新也要有沉淀。",
    },
    "官杀混杂": {
        "meaning": "正官与七杀同时出现，形成'官杀混杂'的格局。",
        "effect": "正官代表规则和正统的约束，七杀代表竞争和非常规的压力。官杀混杂意味着你会同时面对多种压力和挑战，容易感到无所适从，但也说明你的人生经历丰富。",
        "career": "需要在工作和生活中找到平衡，适合多元发展。注意不要同时给自己太多目标。",
        "advice": "梳理优先级，不要让多种压力同时分散精力。建议明确人生主线，其他方面作为辅助。官杀混杂贵在'取舍'。",
    },
}


def get_combination_html(name: str) -> str:
    """返回特殊组合的详细解释 HTML。"""
    info = COMBINATION_EXPLANATIONS.get(name, {})
    if not info:
        return ""
    return (
        f'<div style="background:#FAF7F4;border-radius:10px;padding:14px 16px;'
        f'margin:8px 0;box-shadow:0 1px 2px rgba(0,0,0,0.04);'
        f'border-left:4px solid #B8860B;">'
        f'<div style="font-weight:600;color:#3D2B1A;font-size:15px;margin-bottom:6px;">{name}</div>'
        f'<div style="font-size:13px;color:#3D2B1A;line-height:1.7;margin-bottom:6px;">'
        f'<strong>含义：</strong>{info["meaning"]}</div>'
        f'<div style="font-size:13px;color:#5C4A32;line-height:1.7;margin-bottom:4px;">'
        f'<strong>作用：</strong>{info["effect"]}</div>'
        f'<div style="font-size:12px;color:#5C4A32;line-height:1.7;margin-bottom:4px;">'
        f'<strong>建议：</strong>{info["advice"]}</div>'
        f'</div>'
    )


PATTERN_DESCRIPTIONS = {
    "身强财旺": "日主强而财星旺，有能力承担财富，适合求财发展。",
    "身强官杀": "日主强而官杀有力，适合管理、领导、规则型工作。",
    "身强印旺": "日主强而印星旺，学习能力强，但需注意行动力。",
    "身强食伤": "日主强而食伤旺，才华横溢，适合创意和表达。",
    "身强比劫": "日主强而比劫旺，独立性强，注意合作分寸。",
    "身弱财旺": "财多身弱，富屋贫人，需借力发展或待运扶身。",
    "身弱官杀": "官杀攻身，压力较大，需印星化解或比劫相助。",
    "身弱印旺": "身弱印旺可补，有贵人运和学习能力。",
    "身弱食伤": "身弱而食伤泄身过重，注意精力管理。",
    "身弱比劫": "身弱比劫相助，需借团队之力。",
}


def classify_chart(chart: dict) -> dict:
    """根据八字数据返回命盘类型分类结果。"""
    strength = chart.get("day_master_strength", {})
    strength_label = strength.get("strength", "中和")
    five_elements = chart.get("five_elements", {})
    ten_god_counts = chart.get("ten_god_counts", {})
    pillars = chart.get("pillars", {})

    # 1. 基本格局
    basic_pattern = f"{strength_label}格"

    # 2. 五行格局
    element_pattern = _classify_elements(five_elements)

    # 3. 十神格局
    tg_pattern = _classify_ten_gods(ten_god_counts)

    # 4. 特殊组合
    special_combinations = _find_special_combinations(pillars, ten_god_counts)

    # 5. 综合总结
    summary_key = f"{strength_label}{tg_pattern}" if tg_pattern else strength_label
    summary_desc = PATTERN_DESCRIPTIONS.get(summary_key, "")
    signature = build_chart_signature_text(chart, "命盘类型依据")
    if summary_desc:
        summary_desc = f"类型结论：{summary_key}。{summary_desc}\n{signature}"
    else:
        summary_desc = signature

    return {
        "basic_pattern": basic_pattern,
        "element_pattern": element_pattern,
        "ten_god_pattern": tg_pattern,
        "special_combinations": special_combinations,
        "summary": summary_desc,
    }


def _classify_elements(five_elements: dict) -> str:
    """分析五行分布。"""
    if not five_elements:
        return "暂无法判断"
    sorted_els = sorted(five_elements.items(), key=lambda x: -float(x[1]))
    total = sum(float(v) for v in five_elements.values())
    if total == 0:
        return "暂无法判断"

    present = [(e, float(s) / total * 100) for e, s in sorted_els if float(s) > 0]
    weak = [e for e, p in present if p < 10]
    strong = [e for e, p in present if p > 30]

    parts = []
    if len(present) >= 4:
        parts.append("五行俱全")
    if weak:
        parts.append(f"缺{'、'.join(weak)}")
    if strong:
        parts.append(f"{'、'.join(strong)}偏旺")
    return " · ".join(parts) if parts else "分布均衡"


def _classify_ten_gods(ten_god_counts: dict) -> str:
    """找出最突出的十神格局。"""
    if not ten_god_counts:
        return ""
    group_scores = {}
    for pattern_name, tg_list in TEN_GOD_GROUPS.items():
        score = sum(ten_god_counts.get(tg, 0) for tg in tg_list)
        if score > 0:
            group_scores[pattern_name] = score
    if not group_scores:
        return ""
    top = max(group_scores, key=group_scores.get)
    if group_scores[top] >= 3:
        return top.replace("格", "")
    return ""


def _find_special_combinations(pillars: dict, ten_god_counts: dict) -> list[str]:
    """查找特殊十神组合。"""
    if not pillars:
        return []
    gan_gods = set()
    for key in ["year", "month", "day", "hour"]:
        p = pillars.get(key, {})
        day_master = list(pillars.values())[0].get("gan", "")
        # This is a simplified approach - we'll check ten_god_counts instead
    combinations = []
    has_sha = ten_god_counts.get("七杀", 0) > 0
    has_yin = ten_god_counts.get("正印", 0) > 0 or ten_god_counts.get("偏印", 0) > 0
    has_shi_shen = ten_god_counts.get("食神", 0) > 0
    has_cai = ten_god_counts.get("正财", 0) > 0 or ten_god_counts.get("偏财", 0) > 0
    has_shang_guan = ten_god_counts.get("伤官", 0) > 0
    has_guan = ten_god_counts.get("正官", 0) > 0

    if has_sha and has_yin:
        combinations.append("杀印相生")
    if has_shi_shen and has_cai:
        combinations.append("食神生财")
    if has_shang_guan and has_yin:
        combinations.append("伤官配印")
    if has_guan and has_sha:
        combinations.append("官杀混杂")
    return combinations
