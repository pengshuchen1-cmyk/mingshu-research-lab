"""紫微斗数基础报告。"""

from __future__ import annotations

from report.export_report import DISCLAIMER


KEY_PALACES = ["命宫", "身宫", "夫妻宫", "财帛宫", "官禄宫", "迁移宫", "田宅宫", "福德宫"]

LIFE_MANUAL_TOPICS = [
    {
        "title": "事业说明书",
        "palace": "官禄宫",
        "plain_name": "事业与成就方式",
        "what": "这里看一个人更适合靠什么成事：专业能力、组织平台、管理责任、表达影响，还是项目开创。",
        "reality": "现实里可以观察职业选择、上级压力、是否适合管理路线、适合稳定组织还是项目制。",
        "action": "把事业宫当作职业定位参考，再结合八字十神、大运和现实行业机会制定行动。",
    },
    {
        "title": "财富说明书",
        "palace": "财帛宫",
        "plain_name": "钱的来路与去路",
        "what": "这里看收入方式、金钱观、资源承接能力和花钱压力，不是简单判断钱多钱少。",
        "reality": "现实里可以观察更适合工资、项目、技术收费、资源变现、副业，还是长期平台积累。",
        "action": "用财帛宫提醒现金流习惯和赚钱方式，投资、借贷和合伙仍要以现实数据和风控为先。",
    },
    {
        "title": "关系说明书",
        "palace": "夫妻宫",
        "plain_name": "亲密关系与重要合作",
        "what": "这里看伴侣类型、亲密关系模式、合作边界和长期相处里的压力点。",
        "reality": "现实里可以观察自己更重视安全感还是空间感，沟通中容易卡在哪里，合作中是否容易期待落差。",
        "action": "把夫妻宫当作沟通提醒，重点改善表达、边界和期待管理。",
    },
    {
        "title": "迁移说明书",
        "palace": "迁移宫",
        "plain_name": "外部机会与环境变化",
        "what": "这里看出差、异地、换环境、对外合作和外部机会给人生带来的推动。",
        "reality": "现实里可以观察离开熟悉环境后是否更容易打开局面，以及对外沟通、客户、异地资源是否重要。",
        "action": "迁移宫较有信号时，适合主动经营外部资源；信号偏紧时，出行和换环境要多做准备。",
    },
    {
        "title": "福德说明书",
        "palace": "福德宫",
        "plain_name": "内在状态与长期幸福感",
        "what": "这里看精神电量、兴趣享受、恢复能力和长期内在满足感。",
        "reality": "现实里可以观察一个人是否容易精神紧绷，是否需要独处恢复，兴趣和生活节奏能否支撑长期状态。",
        "action": "把福德宫当作身心节奏提醒，安排稳定休息、兴趣和情绪出口。",
    },
]


def _find_palace(chart: dict, name: str) -> dict:
    """查找宫位。"""
    if name == "身宫":
        for item in chart.get("palaces", []):
            if item.get("is_body_palace"):
                return item
        return {}
    for item in chart.get("palaces", []):
        if item.get("name") == name:
            return item
    return {}


def _join(items: list[str]) -> str:
    return "、".join(items) if items else "暂未见明显信号"


def _build_life_manual_sections(chart: dict, msbp: dict, misbp: dict, fsbp: dict, sbp: dict) -> list[dict]:
    """生成普通用户可读的紫微人生说明书五大专题。"""
    from core.ziwei_constants import DETAILED_PALACE_EXPLANATIONS
    from core.ziwei_star_palace_engine import build_star_palace_explanations
    from core.ziwei_triangle_engine import get_sanfang_sizheng

    star_palace_map = build_star_palace_explanations(chart, sbp)
    sections = [{
        "title": "紫微人生说明书",
        "text": (
            "这部分先不堆术语，而是把紫微盘翻译成五个现实问题：事业怎么发力、钱如何流动、"
            "关系怎么相处、外部机会在哪里、内在状态如何维持。每一段都只作趋势参考，仍需结合现实选择。"
        ),
    }]

    for topic in LIFE_MANUAL_TOPICS:
        palace_name = topic["palace"]
        palace = _find_palace(chart, palace_name)
        detail = DETAILED_PALACE_EXPLANATIONS.get(palace_name, {})
        stars = msbp.get(palace_name, [])
        minor_stars = misbp.get(palace_name, [])
        fierce_stars = fsbp.get(palace_name, [])
        sihua = sbp.get(palace_name, [])
        star_items = star_palace_map.get(palace_name, [])
        tri = get_sanfang_sizheng(palace_name, chart)

        star_plain = "；".join(item.get("plain_text", "") for item in star_items[:2])
        if not star_plain:
            star_plain = "本宫主星信号不明显时，更适合结合对宫、三方四正和八字一起看。"
        evidence = [
            f"{palace_name}落{palace.get('branch', '待确认')}支",
            f"主星：{_join(stars)}",
            f"辅星：{_join(minor_stars)}" if minor_stars else "",
            f"煞星：{_join(fierce_stars)}" if fierce_stars else "",
            f"四化：{_join(sihua)}" if sihua else "",
            f"三方：{_join(tri.get('sanfang', []))}；对宫：{tri.get('sizheng', '待确认')}" if tri else "",
        ]
        evidence_text = "；".join(item for item in evidence if item)
        strengths = _join(detail.get("positive_tendencies", [])[:3])
        risks = _join(detail.get("risk_tendencies", [])[:3])
        advice = detail.get("advice") or topic["action"]

        text = (
            f"这代表什么：{topic['what']}\n\n"
            f"现实里怎么看：{topic['reality']} {star_plain}\n\n"
            f"优势：{strengths}。\n\n"
            f"需要注意：{risks}。\n\n"
            f"行动建议：{topic['action']} {advice}\n\n"
            f"命盘依据：{evidence_text}。\n\n"
            "边界提醒：紫微专题适合做自我观察和规划参考，不替代职业、投资、婚姻和健康等现实决策。"
        )
        sections.append({"title": topic["title"], "text": text})

    return sections


def generate_ziwei_report(chart: dict) -> dict:
    """
    生成紫微综合报告（v1.2-F 增强版）。
    包含命宫/身宫/财帛/官禄/夫妻/疾厄/福德/迁移八宫综合，
    辅星/煞星引用，四化影响摘要，三方四正联动提示，大限基础提示。
    """
    if not chart.get("available"):
        return {
            "title": "紫微斗数综合报告",
            "sections": [{"title": "提示", "text": chart.get("message", "紫微斗数基础盘暂不可用。")}],
            "advice": "请先生成基础盘。",
            "disclaimer": DISCLAIMER,
        }

    ms_ready = chart.get("main_stars_ready", False)
    msbp = chart.get("main_stars_by_palace", {}) if ms_ready else {}
    misbp = chart.get("minor_stars_by_palace", {})
    fsbp = chart.get("fierce_stars_by_palace", {})
    mis_ready = chart.get("minor_stars_ready", False)
    fs_ready = chart.get("fierce_stars_ready", False)
    daxian = chart.get("daxian", {})
    daxian_ready = daxian.get("daxian_ready", False)

    sihua_data = {}
    try:
        from core.ziwei_sihua_engine import get_sihua_by_year_gan, apply_sihua_to_chart
        from core.ziwei_star_engine import get_year_gan_from_profile
        yg = get_year_gan_from_profile(chart.get("profile", {}))
        if yg:
            sihua_data = apply_sihua_to_chart(chart, get_sihua_by_year_gan(yg))
    except Exception:
        sihua_data = {}
    sbp = sihua_data.get("sihua_by_palace", {})

    from core.ziwei_constants import DETAILED_PALACE_EXPLANATIONS
    from core.ziwei_triangle_engine import get_sanfang_sizheng
    from core.ziwei_readable_engine import build_ziwei_capability_review, build_ziwei_plain_guide

    sections = []
    sections.extend(_build_life_manual_sections(chart, msbp, misbp, fsbp, sbp))
    plain_guide = build_ziwei_plain_guide(chart, sbp)
    if plain_guide.get("available"):
        for card in plain_guide.get("focus_cards", []):
            examples = "；".join(card.get("life_examples", [])[:3])
            star_palace_text = "\n".join(
                f"- {item.get('title', '')}：{item.get('plain_text', '')} {item.get('sihua_text', '')} 边界：{item.get('boundary', '')}"
                for item in card.get("star_palace_explanations", [])
            )
            text = (
                f"一句话先懂：{card.get('one_sentence', '')}\n\n"
                f"它是什么意思：{card.get('what_it_means', '')}\n\n"
                f"生活里怎么看：{card.get('real_world_view', '')}\n\n"
                f"现实例子：{examples}\n\n"
                f"可以怎么做：{card.get('action_advice', '')}\n\n"
                f"应该注意什么：{card.get('what_to_notice', '')}\n\n"
                f"星曜组合：{card.get('star_combination_text', '')}\n\n"
                f"主星落宫怎么看：\n{star_palace_text or '本宫未见主星落宫解释，可先看宫位本身和三方四正。'}\n\n"
                f"命盘依据：{card.get('palace_focus', '')}\n\n"
                f"边界提醒：{card.get('boundary_note', '')}"
            )
            sections.append({"title": card.get("title", "紫微说明"), "text": text})

    capability_review = build_ziwei_capability_review(chart)
    capability_lines = []
    for item in capability_review.get("items", []):
        capability_lines.append(
            f"{item.get('name', '')}：{item.get('status', '')}。"
            f"{item.get('user_text', '')} 边界：{item.get('boundary', '')}"
        )
    sections.append({
        "title": capability_review.get("title", "算法完成度说明"),
        "text": "\n".join(capability_lines) + f"\n\n{capability_review.get('boundary', '')}",
    })

    for name in KEY_PALACES:
        palace = _find_palace(chart, name)
        branch = palace.get("branch", "")
        detail = DETAILED_PALACE_EXPLANATIONS.get(name, {})

        # 主星
        stars = msbp.get(name, []) if ms_ready else []
        stars_text = f"主星：{'、'.join(stars)}。" if stars else "该宫位无十四主星。"
        
        # 辅星
        minor_stars = misbp.get(name, []) if mis_ready else []
        minor_text = f"辅星：{'、'.join(minor_stars)}。" if minor_stars else ""
        
        # 煞星
        fierce_stars = fsbp.get(name, []) if fs_ready else []
        fierce_text = f"煞星：{'、'.join(fierce_stars)}。" if fierce_stars else ""
        
        # 四化
        sihua = sbp.get(name, [])
        sihua_text = f"四化：{'、'.join(sihua)}。" if sihua else ""

        # 宫位解释摘要
        explanation = palace.get("explanation", detail.get("palace_theme", ""))

        # 正向/风险
        positive = "、".join(detail.get("positive_tendencies", [])[:3]) if detail else ""
        risk = "、".join(detail.get("risk_tendencies", [])[:3]) if detail else ""
        advice = detail.get("advice", "") if detail else ""

        # 三方四正信息
        triangle_info = ""
        tri = get_sanfang_sizheng(name, chart)
        if tri:
            sanfang_str = "、".join(tri.get("sanfang", []))
            duigong_str = tri.get("sizheng", "")
            tri_summary = tri.get("summary", "")
            if sanfang_str:
                triangle_info = f"三合宫：{sanfang_str}，对宫：{duigong_str}。{tri_summary}"

        # 大限信息
        daxian_text = ""
        if daxian_ready:
            for stage in daxian.get("stages", []):
                if stage.get("palace") == name:
                    daxian_text = f"此宫对应大限{stage.get('age_range', '')}岁阶段。"
                    break

        # 组合文本
        full_text = (
            f"{name}落在{branch or '待确认'}宫。{stars_text}"
            f"{minor_text}{fierce_text}{sihua_text}"
            f"{explanation} "
            f"正：{positive}。" if positive else ""
            f"注意：{risk}。" if risk else ""
        )
        if triangle_info:
            full_text += f" [{triangle_info}]"
        if daxian_text:
            full_text += f" {daxian_text}"
        if advice:
            full_text += f" 建议：{advice}"

        sections.append({"title": f"{name}综合", "text": full_text})

    # 四化影响摘要
    sihua_summary_text = ""
    if sbp:
        parts = []
        for pn, shs in sbp.items():
            parts.append(f"{pn}：{'、'.join(shs)}")
        sihua_summary_text = "四化分布：" + " | ".join(parts) + "。"
        sections.append({"title": "四化影响摘要", "text": sihua_summary_text})

    # 大限基础提示
    if daxian_ready:
        st = daxian.get("stages", [])
        stage_detail = "; ".join([f"{s.get('age_range','')}岁 {s.get('palace','')}宫" for s in st[:6]])
        daxian_section_text = f"大限起于{daxian.get('start_age', 0)}岁，{'顺行' if daxian.get('forward') else '逆行'}。"
        daxian_section_text += f"前六阶段：{stage_detail}。{daxian.get('basis', '')}"
        sections.append({"title": "大限基础提示", "text": daxian_section_text})

    # 综合建议
    ms_note = "当前版本包含十四主星落宫、辅星落宫、煞星落宫，基于传统起星诀计算。" if ms_ready and mis_ready and fs_ready else               "当前版本包含十四主星落宫、辅星落宫（部分）、煞星落宫（部分）。" if ms_ready else               "十四主星排布暂未完成。"
    sections.append({
        "title": "综合建议",
        "text": f"紫微斗数适合与八字排盘、五行十神和年度运程交叉参考。{ms_note}",
    })

    return {
        "title": "紫微人生说明书",
        "sections": sections,
        "advice": sections[-1]["text"],
        "disclaimer": DISCLAIMER,
        "main_stars_ready": ms_ready,
        "minor_stars_ready": mis_ready,
        "fierce_stars_ready": fs_ready,
        "daxian_ready": daxian_ready,
    }
