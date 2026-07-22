"""命盘报告导出。"""

from __future__ import annotations

import os
from io import BytesIO

from core.five_elements import element_summary
from report.narrative_engine import build_luck_stage_narrative, remove_repetitive_sentences
from report.useful_god_report import generate_useful_god_explanation
from report.special_report_common import build_special_markdown
from report.sixty_jiazi_report import build_sixty_jiazi_markdown

DISCLAIMER = "本报告基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。"

PDF_FONT_CANDIDATES = [
    ("ArialUnicode", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ("Songti", "/System/Library/Fonts/Supplemental/Songti.ttc"),
    ("PingFang", "/System/Library/Fonts/PingFang.ttc"),
    ("STHeitiMedium", "/System/Library/Fonts/STHeiti Medium.ttc"),
]


def _polish_report_text(text: str) -> str:
    """减少导出报告中的低信息量重复标签。"""
    return (text or "").replace("平稳观察", "阶段校准")


def _profile_lines(profile: dict, bullet: str = "-") -> list[str]:
    """生成基础信息行。"""
    birth_time = f"{profile.get('birth_hour', 0):02d}:{profile.get('birth_minute', 0):02d}"
    return [
        f"{bullet} 姓名：{profile.get('name', '')}",
        f"{bullet} 性别：{profile.get('gender', '')}",
        f"{bullet} 出生日期：{profile.get('birth_date', '')}",
        f"{bullet} 出生时间：{birth_time}",
        f"{bullet} 出生地点：{profile.get('birth_place', '') or '未填写'}",
    ]


def _pillar_lines(chart: dict, bullet: str = "-") -> list[str]:
    """生成四柱行。"""
    pillars = chart.get("pillars", {})
    return [
        f"{bullet} 年柱：{pillars.get('year', {}).get('pillar', '')}",
        f"{bullet} 月柱：{pillars.get('month', {}).get('pillar', '')}",
        f"{bullet} 日柱：{pillars.get('day', {}).get('pillar', '')}",
        f"{bullet} 时柱：{pillars.get('hour', {}).get('pillar', '')}",
        f"{bullet} 日主：{chart.get('day_master', '')}",
    ]


def _five_element_lines(chart: dict, bullet: str = "-") -> list[str]:
    """生成五行结构行。"""
    summary = element_summary(chart.get("five_elements", {}))
    lines = []
    for element, item in summary.items():
        lines.append(f"{bullet} {element}：{item['score']}，占比 {item['ratio']}%，{item['strength']}")
    return lines


def _ten_god_lines(chart: dict, bullet: str = "-") -> list[str]:
    """生成十神结构行。"""
    counts = chart.get("ten_god_counts", {})
    if not counts:
        return [f"{bullet} 暂无十神统计。"]
    return [f"{bullet} {name}：{count}" for name, count in counts.items()]


def _strength_lines(chart: dict, bullet: str = "-") -> list[str]:
    """生成日主强弱行。"""
    strength = chart.get("day_master_strength", {})
    favorable = "、".join(strength.get("favorable_elements", [])) or "需结合大运流年进一步判断"
    unfavorable = "、".join(strength.get("unfavorable_elements", [])) or "需结合大运流年进一步判断"
    return [
        f"{bullet} 强弱：{strength.get('strength', '暂无法判断')}",
        f"{bullet} 净评分：{strength.get('net_score', 0)}",
        f"{bullet} 喜用五行：{favorable}",
        f"{bullet} 忌神五行：{unfavorable}",
    ]


def _analysis_lines(report: dict, bullet: str = "-") -> list[str]:
    """生成基础分析行。"""
    return [
        f"{bullet} 性格：{report.get('personality_text', '')}",
        f"{bullet} 事业：{report.get('career_text', '')}",
        f"{bullet} 财运：{report.get('wealth_text', '')}",
        f"{bullet} 婚恋：{report.get('love_text', '')}",
        f"{bullet} 风险提醒：{report.get('risk_text', '')}",
        f"{bullet} 行动建议：{report.get('advice', '')}",
    ]


def _paragraph(value: str, fallback: str) -> str:
    """返回段落文本。"""
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _useful_god_lines(chart: dict, report: dict, bullet: str = "-") -> list[str]:
    """生成喜用五行细化行。"""
    useful = {
        "summary": report.get("useful_god_text", ""),
        "details": report.get("useful_god_details", []),
    }
    if not useful["summary"]:
        useful = generate_useful_god_explanation(chart)
    lines = [f"{bullet} {useful.get('summary', '')}"]
    for item in useful.get("details", []):
        keywords = "、".join(item.get("keywords", []))
        lines.append(f"{bullet} 喜{item.get('element', '')}：{keywords}")
        lines.append(f"  {bullet} 事业建议：{item.get('career_advice', '')}")
        lines.append(f"  {bullet} 生活建议：{item.get('life_advice', '')}")
        lines.append(f"  {bullet} 风险提醒：{item.get('risk_advice', '')}")
    return lines


def _luck_lines(chart: dict, luck_data: dict | None, bullet: str = "-") -> list[str]:
    """生成大运流年行。"""
    if not luck_data or not luck_data.get("available"):
        return [f"{bullet} 当前暂未成功获取大运数据，可先参考八字结构、年度运程和流月分析。"]
    lines = [f"{bullet} 起运信息：{luck_data.get('start_text', '')}"]
    stage_texts = []
    for item in luck_data.get("dayun_list", [])[:12]:
        stage_texts.append(item.get("stage_text", ""))
    stage_texts = remove_repetitive_sentences(stage_texts)
    for index, item in enumerate(luck_data.get("dayun_list", [])[:12]):
        stage_text = stage_texts[index] if index < len(stage_texts) and stage_texts[index] else item.get("stage_text", "")
        if not stage_text:
            stage_text = build_luck_stage_narrative(chart, item)
        lines.extend(
            [
                f"{bullet} {item.get('start_age', '')}-{item.get('end_age', '')}岁｜"
                f"{item.get('start_year', '')}-{item.get('end_year', '')}年｜{item.get('pillar', '')}｜"
                f"{item.get('stage_level', '阶段观察')}",
                f"  {bullet} {stage_text}",
            ]
        )
    return lines


def _future_yearly_lines(luck_data: dict | None, bullet: str = "-") -> list[str]:
    """生成未来十年流年趋势。"""
    if not luck_data or not luck_data.get("yearly_list"):
        return [f"{bullet} 当前未生成未来十年流年趋势。"]
    lines = []
    for item in luck_data.get("yearly_list", []):
        keywords = "、".join(item.get("annual_keywords", item.get("keywords", []))) or item.get("relation_to_favorable", "")
        lines.append(
            f"{bullet} {item.get('year', '')}年 {item.get('pillar', '')}｜{item.get('ten_god', '')}｜{keywords}："
            f"{item.get('brief_text', item.get('overall_text', ''))}"
        )
    return lines


def _yearly_lines(yearly_data: dict | None, bullet: str = "-") -> list[str]:
    """生成年度运程行。"""
    if not yearly_data:
        return [f"{bullet} 年度运程：当前未生成年度分析。"]
    high_attention = "、".join(yearly_data.get("high_attention_months", [])) or "暂无特别高关注月份，可按月度详情观察。"
    opportunities = "、".join(yearly_data.get("opportunity_months", [])) or "暂无明显集中月份，可按现实进展选择时机。"
    suitable = "、".join(yearly_data.get("suitable_actions", [])) or "稳住主线，分阶段推进。"
    avoid = "、".join(yearly_data.get("actions_to_avoid", [])) or "避免冲动承诺和高成本试错。"
    return [
        f"{bullet} 年份：{yearly_data.get('year', '')} 年 {yearly_data.get('pillar', '')}",
        f"{bullet} 年度关键词：{'、'.join(yearly_data.get('annual_keywords', yearly_data.get('keywords', [])))}",
        f"{bullet} 喜忌关系：{yearly_data.get('relation_to_favorable', '')}",
        f"{bullet} 总体：{yearly_data.get('overall_text', '')}",
        f"{bullet} 事业：{yearly_data.get('career_text', '')}",
        f"{bullet} 财富：{yearly_data.get('wealth_text', '')}",
        f"{bullet} 关系：{yearly_data.get('relationship_text', '')}",
        f"{bullet} 身心节奏：{yearly_data.get('health_text', '')}",
        f"{bullet} 风险提醒：{yearly_data.get('risk_text', '')}",
        f"{bullet} 行动建议：{yearly_data.get('advice_text', '')}",
        f"{bullet} 高关注月份：{high_attention}",
        f"{bullet} 机会月份：{opportunities}",
        f"{bullet} 适合做：{suitable}",
        f"{bullet} 不适合做：{avoid}",
    ]


def _monthly_lines(
    monthly_data: list[dict] | None,
    bullet: str = "-",
    chart: dict | None = None,
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> list[str]:
    """生成流月分析行（含大概率事件Top 3和命理依据）。"""
    if not monthly_data:
        return [f"{bullet} 流月分析：当前未生成流月分析。"]
    lines = []
    event_results = []
    if chart:
        try:
            from core.monthly_event_activation_bridge import build_year_monthly_event_results
            event_results = build_year_monthly_event_results(chart, monthly_data, yearly_data, luck_data)
        except Exception:
            event_results = []
    for index, item in enumerate(monthly_data):
        month_events = event_results[index].get("top_events", []) if index < len(event_results) else []
        tags = "、".join(item.get("event_tags", []))
        likely_events = item.get("likely_events", [])
        suitable = "、".join(item.get("suitable_actions", [])) or "稳住主线，按计划推进。"
        avoid = "、".join(item.get("actions_to_avoid", [])) or "避免冲动决定。"
        lines.extend(
            [
                f"{bullet} {item.get('month_name', '')}｜{item.get('pillar', '')}｜{item.get('ten_god', '')}｜{tags}",
                f"  {bullet} 本月主题：{item.get('theme', '')}",
                f"  {bullet} {item.get('event_tendency', '')}",
            ]
        )
        lines.extend([f"  {bullet} 大概率事件：{event}" for event in likely_events])
        lines.extend(
            [
                f"  {bullet} {item.get('career_text', '')}",
                f"  {bullet} {item.get('wealth_text', '')}",
                f"  {bullet} {item.get('relationship_text', '')}",
                f"  {bullet} {item.get('health_text', '')}",
                f"  {bullet} {item.get('risk_text', '')}",
                f"  {bullet} {item.get('advice_text', '')}",
                f"  {bullet} 适合做：{suitable}",
                f"  {bullet} 不适合做：{avoid}",
            ]
        )
        # 大概率事件 Top 3
        if month_events:
            lines.append(f"  {bullet} 【{item.get('month_name', '')}大概率事件】")
            for e in month_events[:3]:
                prob = e.get("probability_level", "")
                lines.append(f"  {bullet}   {e.get('label','')}（{prob}）：{e.get('reason','')}")
                triggers = "、".join(e.get("trigger_factors", []) or [])
                if triggers:
                    lines.append(f"  {bullet}   触发因素：{triggers}")
                lines.append(
                    f"  {bullet}   建议（{item.get('month_name', '')}-{e.get('label', '')}）：{e.get('advice','')}"
                )
        
        # Add 命理依据 and 参考来源
        basis = item.get("basis", "")
        source_titles = item.get("source_titles", [])
        if basis:
            lines.append(f"  {bullet} 【命理依据】{basis}")
        if source_titles:
            lines.append(f"  {bullet} 【参考来源（{item.get('month_name', '')}）】{'、'.join(source_titles)}")
    return lines


def _action_advice_lines(report: dict, yearly_data: dict | None, bullet: str = "-") -> list[str]:
    """生成综合行动建议。"""
    yearly_advice = yearly_data.get("advice_text", "") if yearly_data else ""
    return [
        f"{bullet} 事业建议：{_paragraph(report.get('career_text', ''), '事业上建议先稳住主线能力，再结合年度主题选择重点突破。')}",
        f"{bullet} 财务建议：{_paragraph(report.get('wealth_text', ''), '财务上建议保持预算、现金流和风险边界，项目机会先评估再推进。')}",
        f"{bullet} 关系建议：{_paragraph(report.get('love_text', ''), '关系中建议保持清晰沟通，把期待、边界和现实安排说具体。')}",
        f"{bullet} 自我成长建议：{_paragraph(yearly_advice or report.get('advice', ''), '自我成长上建议持续复盘，把命盘提示转化为现实中的行动计划。')}",
    ]


def _life_overview_lines(report: dict, bullet: str = "-") -> list[str]:
    """生成命局总论行。"""
    text = report.get("life_overview", "")
    if text:
        return [f"{bullet} 命局总论："] + [f"  {bullet} {line}" for line in text.split("\n") if line.strip()]
    return [f"{bullet} 命局总论：暂未生成。"]


def _ziwei_life_card_lines(chart, bullet: str = "-") -> list[str]:
    """生成紫微命盘名片导出行。"""
    if not chart:
        return [f"{bullet} 紫微斗数暂无数据。"]
    try:
        from core.ziwei_life_card_engine import analyze_ziwei_life_card
        card = analyze_ziwei_life_card(chart)
        lines = [
            f"{bullet} 紫微命盘名片",
            f"  {bullet} 命盘身份：{card.get('ziwei_profile_type', '')}",
            f"  {bullet} 命宫：{card.get('ming_gong_summary', '')}",
            f"  {bullet} 身宫：{card.get('shen_gong_summary', '')}",
        ]
        for name in ["官禄宫", "财帛宫", "夫妻宫", "福德宫", "疾厄宫", "迁移宫"]:
            summary = card.get("key_palace_summaries", {}).get(name, "")
            if summary:
                lines.append(f"  {bullet} 【{name}】{summary[:80]}")
        for s in card.get("strengths", [])[:3]:
            lines.append(f"  {bullet} 优势：{s}")
        for r in card.get("risks", [])[:3]:
            lines.append(f"  {bullet} 需关注：{r}")
        lines.append(f"  {bullet} 模块边界：{card.get('module_boundary', '')}")
        sources = card.get("source_titles", [])
        if sources:
            lines.append(f"  {bullet} 【参考来源】{'、'.join(sources)}")
        return lines
    except Exception:
        return [f"{bullet} 紫微命盘名片暂未生成。"]


def _life_overview_export_lines(chart: dict, report: dict, bullet: str = "-") -> list[str]:
    """从 life_overview_engine 获取命盘总体结论。"""
    try:
        from core.life_overview_engine import analyze_life_overview
        dp = analyze_life_overview(chart)
        lines = [
            f"{bullet} 总体类型：{dp.get('overall_pattern', '')}",
            f"{bullet} {dp.get('overall_summary', '')}",
        ]
        # Wealth
        w = dp.get("wealth_overview", {})
        lines.append(f"{bullet} 【财富潜力】{w.get('wealth_summary', '')}")
        lines.append(f"  {bullet} 类型：{w.get('wealth_type', '')} | 评估：{w.get('wealth_level', '')}")
        # Romance
        r = dp.get("romance_overview", {})
        lines.append(f"{bullet} 【桃花·感情】{r.get('romance_summary', '')}")
        lines.append(f"  {bullet} 类型：{r.get('romance_type', '')} | 评估：{r.get('romance_level', '')}")
        # Health
        h = dp.get("health_overview", {})
        lines.append(f"{bullet} 【健康稳定】{h.get('health_summary', '')}")
        lines.append(f"  {bullet} 评估：{h.get('health_stability_level', '')}")
        # Career
        c = dp.get("career_overview", {})
        lines.append(f"{bullet} 【事业发展】{c.get('career_summary', '')}")
        lines.append(f"  {bullet} 类型：{c.get('career_type', '')} | 评估：{c.get('career_stability_level', '')}")
        # Strengths & Risks
        for s in dp.get("key_strengths", [])[:4]:
            lines.append(f"{bullet} 优势：{s}")
        for r in dp.get("key_risks", [])[:4]:
            lines.append(f"{bullet} 隐患：{r}")
        # Sources
        sources = dp.get("source_titles", [])
        if sources:
            lines.append(f"{bullet} 【参考来源】{'、'.join(sources)}")
        return lines
    except Exception:
        return [f"{bullet} 命盘总体结论暂未生成。"]


def _build_five_element_deep_section(chart: dict, bullet: str = "-") -> list[str]:
    """生成五行结构深度分析导出段落。"""
    try:
        from report.five_element_deep_report import generate_five_element_deep_report
        deep = generate_five_element_deep_report(chart)
        lines = [
            bullet + " 五行结构总览：" + deep.get("element_overview", ""),
            bullet + " 强弱平衡：" + deep.get("element_balance_summary", ""),
            bullet + " 强五行：" + "、".join(deep.get("strong_elements", [])) or "暂无",
            bullet + " 弱五行：" + "、".join(deep.get("weak_elements", [])) or "暂无",
            bullet + " 喜用五行：" + "、".join(deep.get("favorable_elements", [])) or "暂无",
            bullet + " 忌神五行：" + "、".join(deep.get("unfavorable_elements", [])) or "暂无",
            "",
            bullet + "【五行对主要领域的影响】",
        ]
        ci = deep.get("career_implications", "")
        wi = deep.get("wealth_implications", "")
        ri = deep.get("relationship_implications", "")
        hi = deep.get("health_implications", "")
        if ci: lines.append(bullet + " 事业影响：" + ci[:200])
        if wi: lines.append(bullet + " 财富影响：" + wi[:200])
        if ri: lines.append(bullet + " 感情影响：" + ri[:200])
        if hi: lines.append(bullet + " 健康影响：" + hi[:200])
        lines.append(bullet + "【调整建议】")
        for a in deep.get("adjustment_advice", []):
            lines.append(bullet + "  * " + a)
        sources = deep.get("source_titles", [])
        if sources:
            lines.append(bullet + "【参考来源】" + "、".join(sources))
        return lines
    except Exception:
        return [bullet + " 五行深度报告暂未生成。"]


def build_markdown_report(
    profile: dict,
    chart: dict,
    report: dict,
    luck_data: dict | None = None,
    yearly_data: dict | None = None,
    monthly_data: list[dict] | None = None,
) -> str:
    """
    生成 Markdown 格式完整命盘报告。
    """
    sections = [
        "# 命数研究室 - 命盘综合报告",
        "",
        "## 一、基础信息",
        *_profile_lines(profile),
        "",
        "## 二、命局总论",
        *_life_overview_lines(report),
        "",
        "## 三、命盘总体结论",
        *_life_overview_export_lines(chart, report),
        "",
        "## 四、八字排盘",
        *_pillar_lines(chart),
        "",
        build_sixty_jiazi_markdown(chart),
        "",
        "## 五、五行结构分析",
        *_five_element_lines(chart),
        "",
        _paragraph(report.get("five_element_text", ""), "五行结构用于观察能力、资源和状态分布，仍需结合现实经历综合判断。"),
        "",
        "## 五之二、五行结构深度分析",
        "",
        *_build_five_element_deep_section(chart),
        "",
        "## 六、十神结构分析",
        *_ten_god_lines(chart),
        "",
        _paragraph(report.get("ten_god_text", ""), "十神结构用于观察行为模式、资源关系和阶段主题，不宜单独判断结果。"),
        "",
        "## 七、日主强弱与喜忌",
        *_strength_lines(chart),
        "",
        _paragraph(report.get("strength_text", ""), "日主强弱用于观察承接力和资源需求，喜忌五行仍需结合大运流年验证。"),
        *_useful_god_lines(chart, report),
        "",
        "## 八、基础性格与行为模式",
        _paragraph(report.get("personality_text", ""), "性格与行为模式适合从日主强弱、十神和五行共同观察。"),
        "",
        "## 九、事业方向分析",
        _paragraph(report.get("career_text", ""), "事业方向建议结合能力积累、平台环境和阶段机会共同判断。"),
        "",
        "## 十、财运模式分析",
        _paragraph(report.get("wealth_text", ""), "财运模式更适合从收入来源、现金流、项目风险和长期信用观察。"),
        "",
        "## 十一、感情关系分析",
        _paragraph(report.get("love_text", ""), "感情关系建议结合沟通方式、现实责任和相处体验综合观察。"),
        "",
        "## 十二、大运阶段分析",
        *_luck_lines(chart, luck_data),
        "",
        "## 十三、未来十年流年趋势",
        *_future_yearly_lines(luck_data),
        "",
        "## 十四、年度运程详情",
        *_yearly_lines(yearly_data),
        "",
        "## 十五、十二个月流月趋势",
        *_monthly_lines(monthly_data, chart=chart, yearly_data=yearly_data, luck_data=luck_data),
        "",
        "## 十六、综合行动建议",
        *_action_advice_lines(report, yearly_data),
        "",
        "## 十八、免责声明",
        DISCLAIMER,
        "",
    ]
    return _polish_report_text("\n".join(sections))


def build_text_report(
    profile: dict,
    chart: dict,
    report: dict,
    luck_data: dict | None = None,
    yearly_data: dict | None = None,
    monthly_data: list[dict] | None = None,
) -> str:
    """
    生成纯文本格式完整命盘报告。
    """
    markdown = build_markdown_report(profile, chart, report, luck_data, yearly_data, monthly_data)
    return (
        markdown.replace("# ", "")
        .replace("## ", "")
        .replace("- ", "")
        .replace("* ", "")
    )


def build_special_text_report(special_report: dict) -> str:
    """
    生成专项报告纯文本。
    """
    markdown = build_special_markdown(special_report)
    return markdown.replace("# ", "").replace("## ", "").replace("- ", "")


def _pdf_fallback_message() -> bytes:
    """生成 PDF 不可用时的友好提示。"""
    return (
        "当前环境 PDF 导出暂不可用，请先使用 Markdown 或 TXT 导出。\n"
        "如需启用 PDF，请先运行：python -m pip install -r requirements.txt\n"
    ).encode("utf-8")


def _register_renderable_chinese_font(pdfmetrics, TTFont) -> str | None:
    """优先注册可嵌入的中文字体，避免导出的 PDF 在预览时空白或乱码。"""
    for font_name, font_path in PDF_FONT_CANDIDATES:
        if not os.path.exists(font_path):
            continue
        try:
            try:
                pdfmetrics.getFont(font_name)
            except KeyError:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception:
            continue
    return None


def build_pdf_report(
    profile: dict,
    chart: dict,
    report: dict,
    luck_data: dict | None = None,
    yearly_data: dict | None = None,
    monthly_data: list[dict] | None = None,
) -> bytes:
    """
    生成 PDF 报告。缺少 PDF 依赖时返回友好提示文本 bytes。
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:
        return _pdf_fallback_message()

    try:
        markdown = build_markdown_report(profile, chart, report, luck_data, yearly_data, monthly_data)
        font_name = _register_renderable_chinese_font(pdfmetrics, TTFont)
        if not font_name:
            return _pdf_fallback_message()
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
            title="命数研究室命盘报告",
        )
        styles = getSampleStyleSheet()
        base = ParagraphStyle(
            "ChineseBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=16,
            spaceAfter=6,
        )
        title = ParagraphStyle(
            "ChineseTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=18,
            leading=24,
            spaceAfter=12,
        )
        heading = ParagraphStyle(
            "ChineseHeading",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            spaceBefore=8,
            spaceAfter=6,
        )
        story = []
        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if line.startswith("# "):
                story.append(Paragraph(line[2:], title))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], heading))
            else:
                clean = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(clean, base))
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return _pdf_fallback_message()


def build_special_pdf_report(special_report: dict) -> bytes:
    """
    生成专项 PDF 报告。失败时返回友好提示文本 bytes。
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:
        return _pdf_fallback_message()

    try:
        markdown = build_special_markdown(special_report)
        font_name = _register_renderable_chinese_font(pdfmetrics, TTFont)
        if not font_name:
            return _pdf_fallback_message()
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        base = ParagraphStyle("ChineseBody", parent=styles["BodyText"], fontName=font_name, fontSize=10.5, leading=16)
        title = ParagraphStyle("ChineseTitle", parent=styles["Title"], fontName=font_name, fontSize=18, leading=24)
        heading = ParagraphStyle("ChineseHeading", parent=styles["Heading2"], fontName=font_name, fontSize=13, leading=18)
        story = []
        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 6))
            elif line.startswith("# "):
                story.append(Paragraph(line[2:], title))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], heading))
            else:
                clean = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(clean, base))
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return _pdf_fallback_message()
