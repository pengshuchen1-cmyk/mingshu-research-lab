"""事业专项报告。"""

from __future__ import annotations

from core.chart_fingerprint import build_chart_fingerprint
from core.report_diversity import build_chart_signature_text
from report.export_report import DISCLAIMER
from report.special_report_common import _section


ELEMENT_INDUSTRIES = {
    "木": ["教育培训", "文化策划", "成长咨询", "内容规划"],
    "火": ["品牌传播", "媒体表达", "审美设计", "公开展示"],
    "土": ["运营管理", "组织协调", "地产空间", "餐饮供应"],
    "金": ["技术执行", "金融规则", "流程管理", "审美精修"],
    "水": ["信息咨询", "贸易流通", "资源调度", "跨域沟通"],
}


def _evidence(fp: dict) -> list[str]:
    """生成事业命盘依据。"""
    evidence = [
        f"日主为{fp['day_master']}{fp['day_master_element']}，强弱初判为{fp['strength']}。",
        f"命局较突出的十神为：{'、'.join(fp['top_ten_gods']) or '暂无明显单一十神'}。",
        f"五行较明显的是：{'、'.join(fp['top_elements']) or '暂无'}；相对不足的是：{'、'.join(fp['weak_elements']) or '暂无'}。",
    ]
    if fp["has_strong_output"]:
        evidence.append(f"食伤星数量为{fp['output_star_count']}，事业上更容易通过表达、技术输出、作品和方法被看见。")
    if fp["has_strong_wealth"]:
        evidence.append(f"财星数量为{fp['wealth_star_count']}，事业议题容易和客户、项目、资源、收益转化有关。")
    if fp["has_strong_officer_killing"]:
        evidence.append(f"官杀数量为{fp['officer_star_count']}，规则、职位、目标压力和组织责任感较容易成为事业主轴。")
    if fp["has_strong_resource"]:
        evidence.append(f"印星数量为{fp['resource_star_count']}，学习、资质、平台、系统方法和专业壁垒较重要。")
    if fp["has_strong_peer"]:
        evidence.append(f"比劫数量为{fp['peer_star_count']}，自主性、竞争意识、同辈合作和合伙边界会更突出。")
    if fp["favorable_elements"]:
        evidence.append(f"当前喜用五行为{'、'.join(fp['favorable_elements'])}，事业发力宜优先贴合这些五行代表的能力场景。")
    return evidence


def _career_portrait(fp: dict) -> str:
    """生成更细的事业画像。"""
    top = "、".join(fp["top_elements"][:2]) or "五行"
    weak = "、".join(fp["weak_elements"][:2]) or "短板"
    tags = "、".join(fp["career_pattern_tags"][:4])
    if fp["day_master_element"] == "火":
        style = "更适合把表达、行动、可见度和节奏感转成事业识别度"
    elif fp["day_master_element"] == "土":
        style = "更适合把承载、组织、资源沉淀和稳定交付转成事业信用"
    elif fp["day_master_element"] == "木":
        style = "更适合把学习成长、规划、教育和创意生发转成事业路径"
    elif fp["day_master_element"] == "金":
        style = "更适合把规则、结构、技术、审美和执行精度转成事业优势"
    else:
        style = "更适合把信息、沟通、流动资源和策略调度转成事业机会"
    return (
        f"此盘事业画像不是单纯的通用职业建议：{fp['day_master']}{fp['day_master_element']}日主，"
        f"{fp['strength']}，{top}较突出、{weak}相对不足，事业标签为{tags}。"
        f"因此{style}，同时需要围绕喜用{'、'.join(fp['favorable_elements']) or '阶段平衡'}选择发力场景。"
    )


def _career_differentiator(fp: dict) -> str:
    """根据命盘指纹生成更明确的差异化事业策略。"""
    absent = "、".join(fp["weak_ten_gods"][:4]) or "暂无明显空缺"
    counts = (
        f"财星{fp['wealth_star_count']}、官杀{fp['officer_star_count']}、"
        f"食伤{fp['output_star_count']}、印星{fp['resource_star_count']}、比劫{fp['peer_star_count']}"
    )
    if fp["has_strong_wealth"] and fp["has_strong_officer_killing"]:
        strategy = (
            "财星与官杀同时明显，事业常把收益、客户、责任和管理捆在一起。"
            "现实策略是把商业机会放进制度化流程中管理，重视合同、交付、回款和团队责任。"
            "适合项目管理、客户经营、商务运营、资源整合型岗位；不适合只谈机会、不管履约和现金流的模式。"
        )
    elif fp["has_strong_officer_killing"] and fp["has_strong_peer"]:
        strategy = (
            "官杀强而比劫也明显，事业里容易同时出现外部规则压力和同辈竞争意识。"
            "现实策略不是单纯服从制度，而是先借平台获得秩序和资源，再把职责边界、协作分工、署名成果说清楚。"
            "适合在有明确流程的团队中做项目负责人、执行协调或专业骨干，不适合长期处在权责模糊的合伙局。"
        )
    elif fp["has_strong_officer_killing"] and fp["strength"] in {"身弱", "从弱"}:
        strategy = (
            "官杀强而日主承接力偏弱或从弱，事业压力多来自目标、考核、制度和外界期待。"
            "现实策略应以稳定组织、清晰流程、可量化目标为主，先把压力转成职位信用和专业履历。"
            "适合走合规、管理、运营、职能、项目推进等路径，不建议在资源不足时独自承接高压创业。"
        )
    elif fp["has_strong_output"] and fp["has_strong_peer"]:
        strategy = (
            "食伤与比劫同时明显，事业更像靠个人表达、技术作品和同辈互动打开局面。"
            "现实策略是建立可展示成果，同时把合作边界、报价和交付标准提前写清楚。"
        )
    else:
        strategy = (
            "此盘事业更适合从最突出的十神组合出发，先形成一个清晰主轴，再用喜用五行选择发力场景。"
            "现实中要少做频繁换方向的尝试，多做可复盘、可积累、可被看见的成果。"
        )
    return (
        f"差异化判断依据：{counts}；较少或未见的十神为{absent}；"
        f"夫妻宫地支为{fp['day_branch']}，五行为{fp['spouse_palace_element']}。{strategy}"
    )


def _career_identity(fp: dict) -> str:
    """事业定位。"""
    if fp["has_strong_wealth"] and fp["has_strong_officer_killing"]:
        return "财官并行的项目经营型：适合把客户收益、项目交付、流程责任和团队管理放在同一条事业线上。"
    if fp["has_strong_officer_killing"] and fp["has_strong_peer"]:
        return "平台规则中的竞争协调型：适合在明确制度下承担项目、协调资源和处理同辈竞争边界。"
    if fp["has_strong_officer_killing"] and fp["strength"] in {"身弱", "从弱"}:
        return "制度压力转信用型：适合把考核、流程、责任和目标压力转化成职位信用与专业履历。"
    if fp["has_strong_output"] and fp["has_strong_wealth"]:
        return "技能输出带动商业转化型：适合用作品、技术、内容或方案连接客户与收益。"
    if fp["has_strong_officer_killing"] and fp["has_strong_resource"]:
        return "专业体系内的责任承担型：适合在规范平台中建立资质、职位和长期信用。"
    if fp["has_strong_wealth"]:
        return "客户资源经营型：事业重点在项目机会、销售经营、资源整合和回款节奏。"
    if fp["has_strong_officer_killing"]:
        return "规则管理执行型：适合围绕目标、流程、考核、职位和团队责任发展。"
    if fp["has_strong_output"]:
        return "表达作品驱动型：适合靠内容、技术输出、创意表达和可见成果建立影响力。"
    if fp["has_strong_resource"]:
        return "知识资质沉淀型：适合通过学习研究、专业壁垒和平台支持积累事业势能。"
    if fp["has_strong_peer"]:
        return "自主竞争开拓型：适合建立个人标签，但合作和分工边界要清楚。"
    return "稳健能力积累型：适合先稳定主业能力，再按阶段寻找外部机会。"


def _work_modes(fp: dict) -> list[str]:
    """适合工作模式。"""
    modes: list[str] = []
    if fp["has_strong_output"]:
        modes.extend(["专业技术型", "创意表达型", "内容产品型"])
    if fp["has_strong_wealth"]:
        modes.extend(["销售经营型", "客户项目型", "资源整合型"])
    if fp["has_strong_officer_killing"]:
        modes.extend(["稳定组织型", "管理执行型", "制度责任型"])
    if fp["has_strong_resource"]:
        modes.extend(["平台借力型", "研究顾问型", "资质专业型"])
    if fp["has_strong_peer"]:
        modes.extend(["自主开拓型", "个人品牌型"])
    if fp["strength"] == "身弱":
        modes.append("平台支持型")
    if fp["strength"] == "身强":
        modes.append("主动主导型")
    return list(dict.fromkeys(modes))[:6] or ["长期积累型"]


def _industries(fp: dict) -> list[str]:
    """行业方向。"""
    industries: list[str] = []
    for element in fp["favorable_elements"][:3] or fp["top_elements"][:3]:
        industries.extend(ELEMENT_INDUSTRIES.get(element, []))
    if fp["has_strong_output"]:
        industries.extend(["培训咨询", "内容制作", "产品方案"])
    if fp["has_strong_wealth"]:
        industries.extend(["客户经营", "项目商务", "渠道销售"])
    if fp["has_strong_officer_killing"]:
        industries.extend(["组织管理", "流程合规", "项目执行"])
    return list(dict.fromkeys(industries))[:8] or ["专业服务", "运营管理", "长期主业"]


def _unsuitable(fp: dict) -> list[str]:
    """不适合的事业模式。"""
    items = []
    if fp["strength"] == "身弱":
        items.append("长期脱离平台支持、独自硬扛高压和高成本试错")
    if fp["has_strong_peer"]:
        items.append("分工不清、账目不清、只靠情义维系的合伙")
    if fp["has_strong_output"]:
        items.append("只强调表达突破却忽略交付、合同和复盘")
    if fp["has_strong_wealth"]:
        items.append("只追项目机会但忽视现金流与回款周期")
    if fp["has_strong_officer_killing"]:
        items.append("长期处在高考核压力下却没有恢复机制")
    return items[:5] or ["频繁换方向、缺少长期能力沉淀的工作模式"]


def _risks(fp: dict) -> list[str]:
    """事业风险。"""
    risks = []
    if fp["has_strong_output"]:
        risks.append("表达和创意强时，容易和流程、上级或交付标准产生摩擦。")
    if fp["has_strong_wealth"]:
        risks.append("项目和客户机会多时，需要防止报价、合同、回款和成本核算不清。")
    if fp["has_strong_officer_killing"]:
        risks.append("责任与目标压力较强时，要避免长期紧绷和把外部评价看得过重。")
    if fp["has_strong_resource"]:
        risks.append("学习和系统建设强时，要避免只研究不落地。")
    if fp["has_strong_peer"]:
        risks.append("自主和竞争意识强时，合伙关系需要提前约定权责。")
    return risks or ["事业风险主要在于节奏不稳和阶段目标不够清晰。"]


def _action_plan(fp: dict) -> list[str]:
    """事业行动计划。"""
    actions = [
        f"围绕{'、'.join(fp['career_pattern_tags'][:3])}确定一个主事业标签。",
        f"优先选择能放大{'、'.join(fp['favorable_elements'][:2]) or '核心能力'}的岗位、项目或客户类型。",
    ]
    if fp["has_strong_output"]:
        actions.append("建立可展示的作品、方案、课程、案例或技术成果。")
    if fp["has_strong_wealth"]:
        actions.append("建立客户、报价、合同、回款和复盘表，避免机会来了却留不住收益。")
    if fp["has_strong_officer_killing"]:
        actions.append("把职责、流程、考核目标拆成可执行节点，减少无形压力。")
    if fp["has_strong_officer_killing"] and fp["has_strong_peer"]:
        actions.append("对内先明确权责、署名、分工和资源边界，再承接团队任务。")
    elif fp["has_strong_officer_killing"] and fp["strength"] in {"身弱", "从弱"}:
        actions.append("优先选择流程清晰、评价标准明确、能沉淀履历的平台。")
    if fp["strength"] == "身弱":
        actions.append("优先借助平台、导师、团队和制度支持，不急着单点硬冲。")
    return actions[:6]


def generate_career_report(chart: dict) -> dict:
    """
    生成事业专项报告。
    """
    fp = build_chart_fingerprint(chart)
    signature = build_chart_signature_text(chart, "事业专项差异依据")
    evidence = _evidence(fp)
    portrait = _career_portrait(fp)
    differentiator = _career_differentiator(fp)
    career_identity = _career_identity(fp)
    suitable_work_modes = _work_modes(fp)
    suitable_industries = _industries(fp)
    unsuitable_patterns = _unsuitable(fp)
    career_risks = _risks(fp)
    action_plan = _action_plan(fp)
    next_3_years = [
        f"第一阶段先验证{'、'.join(suitable_work_modes[:2])}是否能带来稳定成果。",
        f"第二阶段围绕{'、'.join(suitable_industries[:3])}筛选岗位、客户或项目。",
        f"第三阶段重点观察流年是否引动{'、'.join(fp['top_ten_gods'][:3])}，并顺着喜用五行{'、'.join(fp['favorable_elements']) or '阶段需要'}发力。",
    ]
    sections = [
        _section("事业专项差异依据", signature),
        _section("命盘依据", " ".join(evidence)),
        _section("事业命盘画像", portrait),
        _section("差异化事业策略", differentiator),
        _section("事业核心定位", career_identity),
        _section("适合工作模式", "、".join(suitable_work_modes)),
        _section("适合行业方向", "、".join(suitable_industries)),
        _section("不适合的事业模式", "；".join(unsuitable_patterns)),
        _section("事业风险", " ".join(career_risks)),
        _section("未来三年事业趋势", " ".join(next_3_years)),
        _section("行动建议", " ".join(action_plan)),
    ]
    return {
        "title": "事业专项报告",
        "evidence": evidence,
        "career_identity": career_identity,
        "career_portrait": portrait,
        "career_differentiator": differentiator,
        "chart_signature": signature,
        "career_evidence": evidence,
        "suitable_work_modes": suitable_work_modes,
        "suitable_industries": suitable_industries,
        "unsuitable_patterns": unsuitable_patterns,
        "career_risks": career_risks,
        "next_3_years": next_3_years,
        "action_plan": action_plan,
        "sections": sections,
        "advice": " ".join(action_plan),
        "disclaimer": DISCLAIMER,
        "public_summary": chart.get("public_summary", {}),
    }
