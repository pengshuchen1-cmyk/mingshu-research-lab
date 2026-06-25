"""财运专项报告。"""

from __future__ import annotations

from core.chart_fingerprint import build_chart_fingerprint
from report.export_report import DISCLAIMER
from report.special_report_common import _section


def _evidence(fp: dict) -> list[str]:
    """生成财运命盘依据。"""
    evidence = [
        f"日主为{fp['day_master']}{fp['day_master_element']}，强弱初判为{fp['strength']}。",
        f"财星数量为{fp['wealth_star_count']}，食伤数量为{fp['output_star_count']}，比劫数量为{fp['peer_star_count']}。",
        f"当前喜用五行为{'、'.join(fp['favorable_elements']) or '暂不明确'}，忌神五行为{'、'.join(fp['unfavorable_elements']) or '暂不明确'}。",
    ]
    if fp["has_strong_wealth"]:
        evidence.append("财星较明显，说明命盘对客户、资源、项目收益和现实回报较敏感。")
    if fp["has_strong_output"]:
        evidence.append("食伤较明显，具备通过技能、内容、技术方案或服务输出带动收益的倾向。")
    if fp["has_strong_peer"]:
        evidence.append("比劫较明显，朋友、合伙、同业竞争和分账边界会影响财务稳定。")
    if fp["has_strong_officer_killing"]:
        evidence.append("官杀较明显，职位收入、制度收入、责任绩效和组织平台对财运有影响。")
    if fp["has_strong_resource"]:
        evidence.append("印星较明显，知识、资质、证书、专业壁垒和平台支持可转化为收入基础。")
    return evidence


def _wealth_identity(fp: dict) -> str:
    """财运定位。"""
    if fp["has_strong_output"] and fp["has_strong_wealth"]:
        return "技能项目变现型：更适合用专业输出、方案能力和客户项目形成收入。"
    if fp["has_strong_wealth"] and fp["has_strong_peer"]:
        return "资源经营但分账敏感型：能看到机会，也要管好合伙、人情和现金流边界。"
    if fp["has_strong_officer_killing"]:
        return "职位制度收入型：更适合依托岗位、平台、责任绩效和长期信用获得收入。"
    if fp["has_strong_resource"]:
        return "知识资质积累型：适合通过学习、证书、研究、顾问和平台背书提升收入。"
    if fp["has_strong_wealth"]:
        return "客户资源经营型：更适合围绕销售、客户、渠道和项目回报布局。"
    if fp["has_strong_output"]:
        return "技能作品收入型：适合靠技术、内容、产品、课程或服务持续变现。"
    return "稳健现金流积累型：适合先稳定主业和预算，再逐步探索副业或项目收入。"


def _main_income_modes(fp: dict) -> list[str]:
    """主要收入方式。"""
    modes: list[str] = []
    if fp["has_strong_officer_killing"]:
        modes.extend(["工资", "职位绩效", "平台制度收入"])
    if fp["has_strong_wealth"]:
        modes.extend(["项目", "销售", "客户经营", "资源整合"])
    if fp["has_strong_output"]:
        modes.extend(["技能", "内容产品", "技术服务", "品牌输出"])
    if fp["has_strong_resource"]:
        modes.extend(["知识服务", "证书资质", "顾问咨询", "平台背书"])
    if fp["has_strong_peer"]:
        modes.append("合伙副业需谨慎筛选")
    return list(dict.fromkeys(modes))[:7] or ["稳定工资", "长期技能积累"]


def _secondary_income_modes(fp: dict) -> list[str]:
    """辅助收入方式。"""
    modes: list[str] = []
    if "火" in fp["favorable_elements"]:
        modes.extend(["品牌曝光", "传播表达", "审美内容"])
    if "木" in fp["favorable_elements"]:
        modes.extend(["教育成长", "规划咨询", "文化创意"])
    if "土" in fp["favorable_elements"]:
        modes.extend(["稳定管理", "组织运营", "空间餐饮"])
    if "金" in fp["favorable_elements"]:
        modes.extend(["技术结构", "规则金融", "流程优化"])
    if "水" in fp["favorable_elements"]:
        modes.extend(["信息咨询", "贸易流通", "资源调度"])
    return list(dict.fromkeys(modes))[:6] or ["低成本副业", "长期复利型技能"]


def _money_risks(fp: dict) -> list[str]:
    """财务风险。"""
    risks = []
    if fp["has_strong_peer"]:
        risks.append("合伙分账、人情支出、朋友借贷和同业竞争容易影响现金流。")
    if fp["has_strong_wealth"]:
        risks.append("机会感强时，容易高估回报周期，需要重视合同、回款和成本。")
    if fp["has_strong_output"]:
        risks.append("靠输出变现时，要避免只重作品表达，不重报价、交付和复购。")
    if fp["has_strong_officer_killing"]:
        risks.append("职位收入型财运要注意压力换钱，避免长期透支身心。")
    if fp["strength"] == "身弱":
        risks.append("身弱时不宜承接超出资源和体力的高杠杆财务压力。")
    return risks or ["财务风险重点在预算松散、现金流记录不足和短期冲动消费。"]


def _investment_attitude(fp: dict) -> str:
    """投资倾向。"""
    if fp["has_strong_wealth"] and not fp["has_strong_peer"]:
        return "可以关注项目和资源机会，但仍建议小比例验证、分散风险，不把单一机会当成长期依靠。"
    if fp["has_strong_peer"]:
        return "投资和合伙需要格外谨慎，尤其要避免人情驱动、口头承诺和分账不清。"
    if fp["has_strong_resource"]:
        return "更适合先做信息研究和长期配置，少做情绪化短线判断。"
    return "以稳健为主，先建立储蓄、预算和风险缓冲，再考虑更复杂的投资。"


def _action_plan(fp: dict) -> list[str]:
    """财务行动计划。"""
    actions = [
        f"把主要收入路径聚焦在{'、'.join(_main_income_modes(fp)[:3])}。",
        "建立收入、支出、合同、回款和项目复盘表。",
    ]
    if fp["has_strong_wealth"]:
        actions.append("每个项目先评估投入周期、回款节点和最坏情况。")
    if fp["has_strong_output"]:
        actions.append("把技能或作品包装成可报价、可交付、可复购的服务。")
    if fp["has_strong_peer"]:
        actions.append("涉及朋友、合伙或人情支出时，先写清规则再投入。")
    if fp["strength"] == "身弱":
        actions.append("优先保留现金流缓冲，不急着承担高杠杆机会。")
    return actions[:6]


def generate_wealth_report(chart: dict) -> dict:
    """
    生成财运专项报告。
    """
    fp = build_chart_fingerprint(chart)
    evidence = _evidence(fp)
    wealth_identity = _wealth_identity(fp)
    main_income_modes = _main_income_modes(fp)
    secondary_income_modes = _secondary_income_modes(fp)
    money_risks = _money_risks(fp)
    investment_attitude = _investment_attitude(fp)
    cashflow_advice = "现金流比短期收益更重要，建议保留生活、事业和突发支出的缓冲。"
    next_3_years = [
        f"第一阶段先把{'、'.join(main_income_modes[:3])}做成稳定现金流。",
        f"第二阶段再评估{'、'.join(secondary_income_modes[:3])}是否适合作为副线收入。",
        f"第三阶段重点观察流年是否引动{'、'.join(fp['wealth_pattern_tags'][:3])}，再决定扩张或收缩。",
    ]
    action_plan = _action_plan(fp)
    sections = [
        _section("命盘依据", " ".join(evidence)),
        _section("财运核心定位", wealth_identity),
        _section("主要收入方式", "、".join(main_income_modes)),
        _section("辅助收入方式", "、".join(secondary_income_modes)),
        _section("财务风险", " ".join(money_risks)),
        _section("投资倾向", investment_attitude),
        _section("现金流提醒", cashflow_advice),
        _section("未来三年财运趋势", " ".join(next_3_years)),
        _section("行动建议", " ".join(action_plan)),
    ]
    return {
        "title": "财运专项报告",
        "evidence": evidence,
        "wealth_identity": wealth_identity,
        "wealth_evidence": evidence,
        "main_income_modes": main_income_modes,
        "secondary_income_modes": secondary_income_modes,
        "money_risks": money_risks,
        "investment_attitude": investment_attitude,
        "cashflow_advice": cashflow_advice,
        "next_3_years": next_3_years,
        "action_plan": action_plan,
        "sections": sections,
        "advice": " ".join(action_plan),
        "disclaimer": DISCLAIMER,
    }
