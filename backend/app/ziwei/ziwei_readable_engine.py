"""紫微斗数白话说明书引擎。

把宫位、星曜、四化转换成普通用户更容易理解的表达。
这里只解释已有命盘数据，不新增未验证算法。
"""

from __future__ import annotations

from .ziwei_constants import DETAILED_PALACE_EXPLANATIONS, DETAILED_STAR_EXPLANATIONS
from .ziwei_fingerprint import build_ziwei_fingerprint
from .ziwei_star_combination_engine import format_star_combination, match_star_combinations
from .ziwei_star_palace_engine import build_star_palace_explanations

FOCUS_PALACES = [
    ("命宫说明", "命宫", "性格底盘"),
    ("身宫说明", "身宫", "后天用力方向"),
    ("事业宫说明", "官禄宫", "事业发力方式"),
    ("财帛宫说明", "财帛宫", "钱和资源怎么流动"),
    ("夫妻宫说明", "夫妻宫", "关系和合作怎么相处"),
]

PALACE_PLAIN_GUIDE = {
    "命宫": {
        "one_sentence": "先看你做决定的默认方式：是主动冲、稳着来，还是先观察再行动。",
        "what": "命宫像一个人的性格底盘，重点看习惯怎么选择、遇事怎么反应、人生主轴更偏向哪里。",
        "reality": "现实里可以观察一个人的自我要求、目标感、做事节奏，以及在压力下更习惯主动推进还是先观察。",
        "notice": "需要注意不要只看命宫单点，还要结合身宫、官禄宫、财帛宫和三方四正一起看。",
        "examples": ["遇到机会时更容易先判断方向", "压力来时会显出真实处事节奏", "长期目标常受命宫气质影响"],
        "action": "先用命宫判断自己的默认反应，再用身宫和事业宫判断真正适合长期用力的方向。",
        "boundary": "命宫是重点参考，不适合单独拿来决定整个人生结论。",
    },
    "身宫": {
        "one_sentence": "身宫看你成年后最愿意把力气花在哪里，也就是越做越像自己的地方。",
        "what": "身宫像后天用力方向，代表成年后更容易投入精力、反复经营、越做越有感的领域。",
        "reality": "现实里常表现为一个人真正愿意花时间打磨的方向，也可能是人生中后期越来越重视的主题。",
        "notice": "如果命宫和身宫不同，说明想法和实际用力点可能有差别，需要看身宫落在哪个宫位。",
        "examples": ["年轻时想法很多，后来会逐渐集中到身宫主题", "越投入越能累积经验和资源", "遇到人生选择时常回到身宫代表的领域"],
        "action": "把身宫当成长线经营方向看，适合用来安排学习、事业和生活重心。",
        "boundary": "身宫只提示后天用力倾向，仍需结合现实条件和八字大运参考。",
    },
    "官禄宫": {
        "one_sentence": "事业宫看你更适合靠什么成事：专业、管理、表达、资源，还是开创。",
        "what": "官禄宫不是只看职位高低，更像工作方式和成就路径，重点看适合靠专业、管理、表达还是资源整合。",
        "reality": "现实里可以观察职业选择、上级关系、工作压力来源，以及适合在组织内发展还是更适合项目制。",
        "notice": "事业判断不能只看官禄宫，还要结合八字里的官杀、食伤、财星和当前大运。",
        "examples": ["选行业时看自己适合稳定组织还是项目突破", "升职或转型时看责任压力来源", "判断适合专业路线还是管理路线"],
        "action": "把官禄宫当职业定位参考，再结合八字十神和当下大运制定现实行动。",
        "boundary": "官禄宫只是职业倾向参考，不能替代学历、经验、行业趋势和现实机会判断。",
    },
    "财帛宫": {
        "one_sentence": "财帛宫看钱的来路和去路，不是简单说钱多钱少。",
        "what": "财帛宫像金钱进出的管道，重点看收入方式、理财习惯、资源承接和花钱压力。",
        "reality": "现实里可以观察更适合稳定工资、项目收入、资源变现、技术收费，还是靠平台和长期积累。",
        "notice": "财帛宫不等于实际财富量，只能提示赚钱方式和用钱习惯，重大投资仍要用现实数据判断。",
        "examples": ["判断更适合工资收入还是项目收入", "观察花钱是否容易被人情或兴趣带动", "看资源能否沉淀成长期收益"],
        "action": "用财帛宫提醒自己的赚钱方式和现金流习惯，投资与借贷仍以现实风控为先。",
        "boundary": "财帛宫只做财务倾向参考，不作为投资、借贷、合伙决策依据。",
    },
    "夫妻宫": {
        "one_sentence": "夫妻宫看亲密关系和重要合作里，你容易被什么人吸引、又容易卡在哪里。",
        "what": "夫妻宫看亲密关系和重要合作，不只是婚姻，也包含长期搭档、合作对象和相处模式。",
        "reality": "现实里可以观察偏好什么伴侣、沟通中容易卡在哪里、关系里更需要安全感还是空间感。",
        "notice": "关系判断需要尊重现实沟通和双方选择，不能用单一宫位给感情下结论。",
        "examples": ["恋爱中更看重安全感还是独立空间", "合作时是否容易出现期待落差", "长期关系里需要怎样沟通边界"],
        "action": "把夫妻宫当关系沟通提醒，用来改善表达、边界和期待管理。",
        "boundary": "夫妻宫只是关系模式参考，不能替代双方真实沟通，也不适合直接给关系下定论。",
    },
}

PALACE_FIELD_BY_STAR = {
    "命宫": "personality_tendency",
    "身宫": "personality_tendency",
    "官禄宫": "career_tendency",
    "财帛宫": "wealth_tendency",
    "夫妻宫": "relationship_tendency",
}


def _find_palace(chart: dict, palace_name: str) -> dict:
    if palace_name == "身宫":
        for palace in chart.get("palaces", []):
            if palace.get("is_body_palace"):
                return palace
        return {}
    for palace in chart.get("palaces", []):
        if palace.get("name") == palace_name:
            return palace
    return {}


def _join(items: list[str]) -> str:
    return "、".join(items) if items else "暂无明显标记"


def _star_combination_text(palace_name: str, stars: list[str], sihua: list[str] | None = None) -> str:
    """生成星曜组合的白话解释。"""
    sihua = sihua or []
    if not stars:
        return (
            "星曜组合：当前组合怎么看：本宫没有显示十四主星时，不代表这个领域为空白，"
            "更适合先看宫位本身、对宫和三方四正，再结合八字一起判断。"
        )

    matched_combinations = match_star_combinations(stars, palace_name=palace_name)
    if matched_combinations:
        return format_star_combination(matched_combinations[0], sihua)

    field = PALACE_FIELD_BY_STAR.get(palace_name, "personality_tendency")
    star_parts = []
    keyword_pool = []
    risk_pool = []
    for star in stars:
        detail = DETAILED_STAR_EXPLANATIONS.get(star, {})
        tendency = detail.get(field) or detail.get("personality_tendency", "")
        if tendency:
            star_parts.append(f"{star}偏向{tendency}")
        keyword_pool.extend(detail.get("core_keywords", [])[:2])
        risk = detail.get("risk_tendency") or detail.get("risk_warning", "")
        if risk:
            risk_pool.append(risk)

    combo = "；".join(star_parts)
    keywords = _join(list(dict.fromkeys(keyword_pool))[:5])
    risks = _join(list(dict.fromkeys(risk_pool))[:2])
    transform_text = f"四化带来{_join(sihua)}信号，适合把对应领域作为阶段性重点观察。" if sihua else "本宫未见明显四化，宜用平常心观察长期模式。"

    return (
        f"星曜组合：当前组合怎么看：{combo}。关键词可抓住：{keywords}。"
        f"{transform_text} 需要注意：{risks}。"
    )


def build_ziwei_plain_guide(chart: dict, sihua_by_palace: dict | None = None) -> dict:
    """生成紫微斗数白话说明书。"""
    if not chart.get("available"):
        return {
            "available": False,
            "summary": chart.get("message", "紫微斗数基础盘暂不可用。"),
            "focus_cards": [],
            "boundary": "当前紫微盘暂不可用。",
        }

    fp = build_ziwei_fingerprint(chart)
    sihua_by_palace = sihua_by_palace or {}
    main_stars_by_palace = chart.get("main_stars_by_palace", {})
    star_palace_map = build_star_palace_explanations(chart, sihua_by_palace)
    focus_cards = []

    for title, palace_name, plain_title in FOCUS_PALACES:
        palace = _find_palace(chart, palace_name)
        actual_palace_name = palace.get("name", palace_name)
        branch = palace.get("branch", "")
        guide = PALACE_PLAIN_GUIDE.get(palace_name, {})
        detail = DETAILED_PALACE_EXPLANATIONS.get(actual_palace_name, {})
        stars = main_stars_by_palace.get(actual_palace_name, palace.get("main_stars", []))
        sihua = sihua_by_palace.get(actual_palace_name, [])
        focus = fp.get("key_palace_focus", {}).get(palace_name, "")
        positives = detail.get("positive_tendencies", [])
        risks = detail.get("risk_tendencies", [])

        focus_cards.append({
            "title": title,
            "palace_name": palace_name,
            "actual_palace_name": actual_palace_name,
            "plain_title": plain_title,
            "branch": branch,
            "main_stars": stars,
            "sihua": sihua,
            "one_sentence": guide.get("one_sentence", ""),
            "what_it_means": guide.get("what", ""),
            "real_world_view": guide.get("reality", ""),
            "what_to_notice": guide.get("notice", ""),
            "life_examples": guide.get("examples", []),
            "action_advice": guide.get("action", ""),
            "boundary_note": guide.get("boundary", "本项仅供趋势参考。"),
            "palace_focus": focus,
            "positive_tendencies": positives[:3],
            "risk_tendencies": risks[:3],
            "star_combination_text": _star_combination_text(palace_name, stars, sihua),
            "star_palace_explanations": star_palace_map.get(palace_name, []),
            "evidence": [
                f"{palace_name}对应宫位：{actual_palace_name}",
                f"地支：{branch or '待确认'}",
                f"主星：{_join(stars)}",
                f"四化：{_join(sihua)}",
            ],
        })

    return {
        "available": True,
        "summary": "这份紫微说明书先把命宫、身宫、事业宫、财帛宫、夫妻宫翻译成现实语言，再补充星曜组合提示。",
        "focus_cards": focus_cards,
        "boundary": (
            "当前说明只基于已生成的命宫、身宫、十二宫、十四主星、生年四化与三方四正基础资料。"
            "未确认的飞化、紫微流年流月不会包装成结论。"
        ),
        "source_ids": [
            "ziwei_doushu_quanshu",
            "ziwei_doushu_quanji",
            "traditional_ziwei_palace_system",
            "traditional_ziwei_sihua_system",
        ],
    }


def build_ziwei_capability_review(chart: dict) -> dict:
    """生成紫微模块完成度说明，避免把边界内容说成确定结论。"""
    main_ready = bool(chart.get("main_stars_ready"))
    minor_ready = bool(chart.get("minor_stars_ready"))
    fierce_ready = bool(chart.get("fierce_stars_ready"))
    daxian_ready = bool(chart.get("daxian", {}).get("daxian_ready"))

    items = [
        {
            "name": "命宫与身宫",
            "status": "已接入",
            "user_text": "可用于观察性格底盘和后天用力方向。",
            "boundary": "仍需结合十二宫、星曜和八字交叉参考。",
        },
        {
            "name": "十二宫位",
            "status": "已接入",
            "user_text": "可查看事业、财帛、夫妻、迁移、福德等生活领域。",
            "boundary": "宫位是框架，不等于单独结论。",
        },
        {
            "name": "十四主星落宫",
            "status": "已接入，需样例校验" if main_ready else "未接入",
            "user_text": "用于观察每个宫位的主要性格和事件倾向。",
            "boundary": "当前按传统起星诀生成，后续仍适合增加更多已知盘例校验。",
        },
        {
            "name": "生年四化",
            "status": "已接入",
            "user_text": "用于提示哪些宫位更容易出现机会、权责、名声或课题。",
            "boundary": "当前只做生年四化，不做复杂飞化断事。",
        },
        {
            "name": "三方四正",
            "status": "已接入",
            "user_text": "用于把单一宫位放到联动结构里看。",
            "boundary": "只做基础结构提示，不替代完整斗数盘审。",
        },
        {
            "name": "辅星落宫",
            "status": "已接入，需样例校验" if minor_ready else "结构准备",
            "user_text": "用于辅助观察文书、贵人、协助等细节。",
            "boundary": "当前只作为辅助参考，不单独下结论。",
        },
        {
            "name": "煞星落宫",
            "status": "已接入，需样例校验" if fierce_ready else "结构准备",
            "user_text": "用于提醒压力、阻滞、突发或需要谨慎的领域。",
            "boundary": "只做风险提醒，不做恐吓式判断。",
        },
        {
            "name": "大限基础结构",
            "status": "已接入，需样例校验" if daxian_ready else "结构准备",
            "user_text": "用于观察不同年龄阶段重点宫位。",
            "boundary": "当前为基础阶段提示，不做完整大限流年细断。",
        },
        {
            "name": "飞化",
            "status": "未接入",
            "user_text": "暂不生成飞化断语。",
            "boundary": "不会把未接入内容包装成结论。",
        },
        {
            "name": "紫微流年流月",
            "status": "未接入",
            "user_text": "暂不生成紫微年度和月份断事。",
            "boundary": "年度和流月目前以八字模块为主。",
        },
    ]

    return {
        "title": "算法完成度说明",
        "items": items,
        "boundary": "当前紫微内容以命宫、身宫、十二宫、主星、四化和基础结构为参考；不会把未接入内容包装成结论。",
    }
