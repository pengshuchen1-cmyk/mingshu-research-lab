"""自然语言叙事生成。"""

from __future__ import annotations

from difflib import SequenceMatcher

from core.bazi_constants import BRANCH_HIDDEN_STEMS, BRANCH_MAIN_ELEMENTS, CONTROLLING, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.ten_gods import get_ten_god


BRANCH_CLASHES = {
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
}

TEN_GOD_NARRATIVES: dict[str, dict[str, object]] = {
    "比肩": {
        "keywords": ["自我推进", "同行竞争", "同辈互动", "能力强化"],
        "theme": "自我意识、竞争意识和同辈互动会更明显，适合强化个人能力和稳定执行。",
        "career": "事业上适合建立个人作品、专业标签和稳定节奏，但团队协作中要留意摩擦与分工。",
        "wealth": "财务上需要关注竞争消耗、人情往来和合作分账，收入推进宜和成本控制同步。",
        "relationship": "关系中自我立场较强，适合把期待说清楚，避免用沉默或硬碰硬处理分歧。",
        "health": "状态上容易想自己扛住，建议安排规律休息，别把压力长期压在心里。",
        "advice": "先把个人能力做扎实，再谈合作扩张；重要合作写清规则更稳。",
    },
    "劫财": {
        "keywords": ["合作边界", "资源分配", "朋友往来", "人情支出"],
        "theme": "朋友、同行、合作和资源分配议题变多，外部互动会更活跃。",
        "career": "事业上适合借助团队与渠道，但要提前约定职责、投入和收益分配。",
        "wealth": "财务上要留意人情支出、合伙成本和临时开销，资金安排宜留缓冲。",
        "relationship": "关系中容易因为资源、时间或承诺产生拉扯，适合把边界表达得更清楚。",
        "health": "状态上容易被外界节奏带动，建议减少无效应酬，给自己留恢复时间。",
        "advice": "合作可做，但要有账目、边界和退出机制。",
    },
    "食神": {
        "keywords": ["稳定输出", "作品打磨", "技能沉淀", "生活节奏"],
        "theme": "表达、技能、作品和生活品质会成为重点，适合把能力转化成稳定成果。",
        "career": "事业上适合内容、产品、技术输出、教学分享和长期打磨型项目。",
        "wealth": "财务上适合靠技能、作品、服务和口碑逐步变现，收益宜稳扎稳打。",
        "relationship": "关系中表达更温和，适合通过陪伴、分享和具体行动增加信任。",
        "health": "状态上适合调养作息、饮食和运动，让输出能力更可持续。",
        "advice": "把灵感变成可复用的方法、作品或流程，少追短期热度。",
    },
    "伤官": {
        "keywords": ["表达突破", "创意释放", "规则摩擦", "技术输出"],
        "theme": "表达欲、创新意识和突破感增强，适合展示能力，也要处理好规则边界。",
        "career": "事业上适合创意、传播、技术方案、产品改版和表达型工作，但沟通要留余地。",
        "wealth": "财务上适合靠创意、技术和项目输出拓展收入，但不宜忽视合同与流程。",
        "relationship": "关系中容易因为话说得快或直产生误会，建议先确认对方感受再表达立场。",
        "health": "状态上思维活跃，容易睡眠不稳或情绪起伏，适合做节奏管理。",
        "advice": "可以突破，但要让表达服务于结果，而不是只释放情绪。",
    },
    "正财": {
        "keywords": ["稳定收入", "预算管理", "现实事务", "资源积累"],
        "theme": "收入、预算、现实事务和资源积累会更突出，适合把事情落到具体数字。",
        "career": "事业上适合推进稳定业务、客户维护、销售转化和可衡量的项目成果。",
        "wealth": "财务上适合做预算、现金流管理和稳定收益安排，支出宜有计划。",
        "relationship": "关系中会更重视现实承诺和生活安排，适合讨论具体责任而非空泛期待。",
        "health": "状态上容易被现实事务占满，建议避免长期焦虑账目和琐事。",
        "advice": "用清单和预算管理资源，先稳住基本盘，再看增量机会。",
    },
    "偏财": {
        "keywords": ["项目机会", "资源整合", "灵活变现", "商业判断"],
        "theme": "项目、机会、商业资源和灵活收益会更容易被看见，适合提升判断力。",
        "career": "事业上适合经营、销售、资源整合、跨界项目和客户机会开拓。",
        "wealth": "财务上可能出现更多项目型机会，也要评估投入周期、现金流和合作风险。",
        "relationship": "关系中社交资源变多，建议避免把利益、人情和亲密期待混在一起。",
        "health": "状态上容易因为机会多而分散精力，建议保留休息和复盘时间。",
        "advice": "机会可以看，但每个机会都要算成本、边界和回收节奏。",
    },
    "正官": {
        "keywords": ["责任规范", "职位目标", "秩序建设", "长期信用"],
        "theme": "责任、规则、职位和外部评价会更明显，适合建立稳定秩序。",
        "career": "事业上适合承担责任、争取职位、进入规范化体系和提升职业信用。",
        "wealth": "财务上更依赖职位、平台、制度化收入和长期稳定安排。",
        "relationship": "关系中会更看重承诺、秩序和责任，沟通上要避免只讲标准不讲感受。",
        "health": "状态上容易受到考核、上级要求或期限压力影响，适合分层处理任务。",
        "advice": "把规则变成助力，重要事项按流程推进，少用硬扛解决压力。",
    },
    "七杀": {
        "keywords": ["目标压力", "竞争挑战", "执行突破", "风险控制"],
        "theme": "目标压力、竞争挑战和执行要求提升，适合训练决断力和抗压能力。",
        "career": "事业上适合推进难题、承担关键任务和管理竞争目标，但要避免长期高压。",
        "wealth": "财务上收益更依赖执行效率和风险控制，不适合忽略成本去追速度。",
        "relationship": "关系中可能带着压力沟通，建议减少命令式表达，多说明真实需求。",
        "health": "状态上要关注紧绷、疲劳和急躁，规律运动与睡眠很重要。",
        "advice": "把压力拆成清晰目标，先处理关键矛盾，再逐步扩大成果。",
    },
    "正印": {
        "keywords": ["学习修整", "贵人支持", "系统建设", "资质提升"],
        "theme": "学习、贵人、系统、资质和休整议题增强，适合补足底层能力。",
        "career": "事业上适合学习进修、资质提升、方法体系建设和寻找稳定支持。",
        "wealth": "财务上不宜过度冒进，更适合长期积累、技能升级和稳健配置。",
        "relationship": "关系中更需要安全感和理解，适合通过稳定陪伴建立信任。",
        "health": "状态上适合休养、调节作息和恢复能量，不必把节奏拉得过满。",
        "advice": "先补系统、补方法、补认知，再把学习成果转成行动。",
    },
    "偏印": {
        "keywords": ["思考调整", "灵感研究", "内在整理", "专业深化"],
        "theme": "思考、研究、复盘和内在调整增多，适合专业深化和方向校准。",
        "career": "事业上适合研究型、策略型、咨询型或需要独立思考的工作。",
        "wealth": "财务上更适合保守评估，先完善信息和模型，再决定投入。",
        "relationship": "关系中容易想得多、说得少，建议把真实顾虑转成可沟通的话。",
        "health": "状态上要注意精神内耗和睡眠质量，适合减少信息过载。",
        "advice": "把想法写下来、做验证、定节奏，避免长期停留在脑内推演。",
    },
    "未知": {
        "keywords": ["阶段校准", "节奏管理", "资料补全"],
        "theme": "当前十神信息不完整，适合先补充资料，再结合具体经历观察阶段变化。",
        "career": "事业上以稳住主线和复盘反馈为主。",
        "wealth": "财务上优先保持预算和现金流意识。",
        "relationship": "关系中保持清晰沟通和弹性。",
        "health": "状态上重视作息和压力管理。",
        "advice": "先记录变化，再逐步校正判断。",
    },
}

MONTHLY_TEN_GOD_EVENTS: dict[str, dict[str, object]] = {
    "比肩": {
        "likely_events": [
            "同行竞争、同辈互动、朋友同事影响变强。",
            "容易想自己做决定，不太愿意被过度安排。",
            "合作中需要明确分工，避免责任边界含糊。",
        ],
        "advice": "适合强化个人能力，但不要过度硬碰硬。",
        "suitable": ["整理个人作品和能力清单", "主动推进自己负责的任务", "明确团队分工"],
        "avoid": ["情绪化竞争", "临时口头合伙", "把所有压力都自己扛住"],
    },
    "劫财": {
        "likely_events": [
            "人情支出、朋友求助、合伙资源分配更容易出现。",
            "容易遇到钱、人、资源边界不清的问题。",
            "合作关系需要提前说清楚规则。",
        ],
        "advice": "不宜轻易借钱、担保或口头合伙。",
        "suitable": ["清点合作资源", "确认分账规则", "筛选真正可靠的合作"],
        "avoid": ["冲动借贷", "替人担保", "没有边界的人情承诺"],
    },
    "食神": {
        "likely_events": [
            "稳定输出、作品打磨、内容创作更容易有成果。",
            "生活享受、饮食聚会、轻松社交可能增加。",
            "适合把技能变成可见成果。",
        ],
        "advice": "适合持续生产，不宜拖延。",
        "suitable": ["发布作品", "打磨服务流程", "安排稳定学习和输出"],
        "avoid": ["只享受不交付", "拖延关键节点", "过度松散"],
    },
    "伤官": {
        "likely_events": [
            "表达欲增强，容易提出不同意见。",
            "可能与规则、上级、制度产生摩擦。",
            "适合创意突破和公开展示。",
        ],
        "advice": "说话要留余地，避免因语气造成误会。",
        "suitable": ["做方案改版", "公开展示能力", "优化表达材料"],
        "avoid": ["在情绪高点争辩", "忽略流程规则", "过度承诺"],
    },
    "正财": {
        "likely_events": [
            "稳定收入、账目预算、现实事务会更突出。",
            "适合处理客户、订单、回款、采购。",
            "容易关注生活成本和现实安全感。",
        ],
        "advice": "适合做预算，不宜乱花钱。",
        "suitable": ["整理账目预算", "跟进回款订单", "推进稳定客户维护"],
        "avoid": ["超预算消费", "忽略合同细节", "只看收入不看成本"],
    },
    "偏财": {
        "likely_events": [
            "项目机会、资源变现、客户合作更容易被看见。",
            "容易有临时收入或临时支出。",
            "容易被新机会吸引。",
        ],
        "advice": "机会可以看，但不宜冲动投资。",
        "suitable": ["评估项目回报", "梳理资源变现路径", "拓展客户渠道"],
        "avoid": ["冲动投资", "重仓陌生项目", "只听人情介绍就投入"],
    },
    "正官": {
        "likely_events": [
            "工作责任、上级要求、制度流程会更明显。",
            "容易遇到考核、审批、职位压力。",
            "适合做规范化、长期化的事情。",
        ],
        "advice": "按规则推进，少走捷径。",
        "suitable": ["完善流程规范", "承担清晰职责", "准备考核和汇报"],
        "avoid": ["绕开流程", "逃避责任", "用情绪处理规则问题"],
    },
    "七杀": {
        "likely_events": [
            "目标压力、竞争挑战、突发任务更容易出现。",
            "容易遇到强势人物或高压场景。",
            "适合解决难题、突破瓶颈。",
        ],
        "advice": "不宜硬扛，注意节奏和身体。",
        "suitable": ["拆解高压目标", "处理关键矛盾", "做风险预案"],
        "avoid": ["长期硬扛", "仓促冒险", "把压力带进亲密沟通"],
    },
    "正印": {
        "likely_events": [
            "学习进修、贵人支持、资料整理更容易出现。",
            "适合休整、复盘、建立系统。",
            "容易得到长辈、老师、平台帮助。",
        ],
        "advice": "适合打基础，不宜急于求成。",
        "suitable": ["学习进修", "整理资料系统", "寻求专业支持"],
        "avoid": ["急于求成", "只学习不实践", "过度依赖别人保护"],
    },
    "偏印": {
        "likely_events": [
            "灵感研究、内在整理、独立思考更明显。",
            "容易想太多，节奏变慢。",
            "适合处理专业、冷门、深度内容。",
        ],
        "advice": "注意不要陷入过度内耗。",
        "suitable": ["做深度研究", "复盘旧项目", "整理专业方法"],
        "avoid": ["长期内耗", "过度收集信息", "重要沟通只在心里推演"],
    },
    "未知": {
        "likely_events": [
            "近期事件的实际进展会成为观察重点。",
            "适合先记录变化，再做判断。",
            "重要事项需要结合具体情境拆解。",
        ],
        "advice": "先记录变化，再逐步校正判断。",
        "suitable": ["记录关键变化", "整理待确认事项", "保持稳定作息"],
        "avoid": ["凭单一信息做重大决定", "把短期变化放大", "忽略现实证据"],
    },
}


def _elements(luck_item: dict) -> list[str]:
    """取天干和地支主气五行。"""
    return [item for item in [luck_item.get("gan_element", ""), luck_item.get("zhi_element", "")] if item]


def _relation(chart: dict, elements: list[str]) -> tuple[int, str]:
    """判断一组五行与喜忌的关系。"""
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    score = 0
    has_favorable = False
    has_unfavorable = False
    for element in elements:
        if element in favorable:
            score += 1
            has_favorable = True
        if element in unfavorable:
            score -= 1
            has_unfavorable = True
    if score > 0:
        return score, "喜用相关"
    if score < 0:
        return score, "忌神相关"
    if has_favorable and has_unfavorable:
        return score, "喜忌混杂"
    return score, "平稳观察"


def _relation_text(relation: str) -> str:
    """生成喜忌关系说明。"""
    if relation == "喜用相关":
        return "五行对命局有补益倾向，适合主动推进、争取资源或把计划落地"
    if relation == "忌神相关":
        return "这一阶段更容易出现压力、消耗或反复，需要控制节奏，避免过度冒进"
    if relation == "喜忌混杂":
        return "机会和压力并存，适合边推进边修正，重要决定多做验证"
    return "趋势不宜简单看好坏，适合结合具体进展稳妥推进"


def _branch_clash_text(chart: dict, branch: str) -> str:
    """生成基础地支冲提示。"""
    if not branch:
        return ""
    relations = analyze_year_branch_relations(chart, branch)
    if not relations:
        branch_focus = {
            "子": "子水阶段可多看信息流动、沟通节奏和休息恢复。",
            "丑": "丑土阶段可多看资料整理、预算安排和现实事务收口。",
            "寅": "寅木阶段可多看学习成长、计划启动和新方向铺垫。",
            "卯": "卯木阶段可多看协作沟通、审美表达和关系互动。",
            "辰": "辰土阶段可多看旧事整合、资源沉淀和计划校准。",
            "巳": "巳火阶段可多看表达展示、行动效率和情绪热度。",
            "午": "午火阶段可多看曝光表达、执行强度和作息节制。",
            "未": "未土阶段可多看团队协调、长期积累和家庭事务。",
            "申": "申金阶段可多看规则执行、技术细节和边界管理。",
            "酉": "酉金阶段可多看合同文书、审美精修和成果验收。",
            "戌": "戌土阶段可多看责任承接、项目复盘和安全感建设。",
            "亥": "亥水阶段可多看信息整合、出行变化和内在恢复。",
        }
        return branch_focus.get(branch, "此阶段未见明显六冲，重点可回到五行和十神主题细看。")
    labels = "、".join(item["label"] for item in relations)
    details = " ".join(item["text"] for item in relations)
    return f"此阶段地支{branch}与原局形成{labels}，变化、迁动或节奏调整感会更明显。{details}"


def _main_branch_ten_god(chart: dict, branch: str) -> str:
    """根据地支主气推导地支十神。"""
    hidden_stems = BRANCH_HIDDEN_STEMS.get(branch, [])
    if hidden_stems:
        return get_ten_god(chart.get("day_master", ""), hidden_stems[0])
    main_element = BRANCH_MAIN_ELEMENTS.get(branch, "")
    day_master = chart.get("day_master", "")
    for gan, element in STEM_ELEMENTS.items():
        if element == main_element:
            return get_ten_god(day_master, gan)
    return "未知"


def _relation_event_text(relation: str) -> str:
    """生成喜忌事件倾向说明。"""
    if relation == "喜用相关":
        return "这个月的五行对命局有补益倾向，事件更偏向机会、补充资源、推进计划和能力成长。"
    if relation == "忌神相关":
        return "这个月更容易出现消耗、压力或反复，适合控制节奏，重要决定尽量多验证。"
    if relation == "喜忌混杂":
        return "这个月机会和压力并存，适合边推进边修正，不宜因为短期变化过度乐观或悲观。"
    return "这个月更适合把关键变化记录清楚，再根据具体进展调整节奏。"


def _unique(items: list[str], limit: int | None = None) -> list[str]:
    """保持顺序去重。"""
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result if limit is None else result[:limit]


def _actions_for_relation(relation: str) -> tuple[list[str], list[str]]:
    """根据喜忌关系给出动作。"""
    if relation == "喜用相关":
        return (
            ["主动争取资源", "推进已经验证过的计划", "把能力成果公开展示"],
            ["过度扩张", "忽略成本", "因为进展顺利就省略复盘"],
        )
    if relation == "忌神相关":
        return (
            ["收紧节奏", "复核合同和预算", "为重要决定设置观察期"],
            ["冲动投资", "高压硬扛", "在人情压力下仓促承诺"],
        )
    if relation == "喜忌混杂":
        return (
            ["分阶段推进", "边做边复盘", "把风险和机会分开评估"],
            ["过度乐观", "过度悲观", "把所有资源押在单一方向"],
        )
    return (
        ["稳定主线", "记录关键变化", "先处理确定性事务"],
        ["频繁改方向", "用短期情绪做长期决定", "忽略基础作息"],
    )


def build_luck_stage_narrative(chart: dict, luck_item: dict) -> str:
    """
    根据大运天干、地支、五行、十神、喜忌关系生成大运阶段解释。
    """
    ten_god = luck_item.get("ten_god") or get_ten_god(chart.get("day_master", ""), luck_item.get("gan", ""))
    info = TEN_GOD_NARRATIVES.get(ten_god, TEN_GOD_NARRATIVES["未知"])
    elements = _elements(luck_item)
    _, relation = _relation(chart, elements)
    branch_ten_god = _main_branch_ten_god(chart, luck_item.get("zhi", ""))
    strength = chart.get("day_master_strength", {}).get("strength", "暂无法判断")
    element_text = "、".join(elements) or "五行信息暂不完整"
    clash_text = _branch_clash_text(chart, luck_item.get("zhi", ""))
    return (
        f"阶段总览：{luck_item.get('pillar', '')}大运以{element_text}为主要气息，"
        f"天干十神为{ten_god}，地支主气可参考{branch_ten_god}，日主强弱为{strength}，"
        f"{_relation_text(relation)}。{clash_text}"
        f" 事业重点：{info['career']}"
        f" 财运重点：{info['wealth']}"
        f" 关系提醒：{info['relationship']}"
        f" 风险与状态：{info['health']}"
        f" 行动建议：{info['advice']}"
    )


def build_luck_stage_sections(chart: dict, luck_item: dict) -> dict:
    """生成大运阶段分段解释。"""
    ten_god = luck_item.get("ten_god") or get_ten_god(chart.get("day_master", ""), luck_item.get("gan", ""))
    info = TEN_GOD_NARRATIVES.get(ten_god, TEN_GOD_NARRATIVES["未知"])
    elements = _elements(luck_item)
    _, relation = _relation(chart, elements)
    element_text = "、".join(elements) or "五行信息暂不完整"
    return {
        "stage_summary": f"{luck_item.get('pillar', '')}大运以{element_text}为主要气息，{info['theme']}结合{ten_god}主题，{_relation_text(relation)}。",
        "career_focus": str(info["career"]),
        "wealth_focus": str(info["wealth"]),
        "relationship_focus": str(info["relationship"]),
        "risk_focus": f"{info['health']}{_branch_clash_text(chart, luck_item.get('zhi', ''))}",
        "action_advice": str(info["advice"]),
    }


def build_yearly_narrative(chart: dict, yearly_item: dict) -> dict:
    """
    根据流年五行、十神、喜忌关系生成年度细分解释。
    """
    ten_god = yearly_item.get("ten_god", "未知")
    info = TEN_GOD_NARRATIVES.get(ten_god, TEN_GOD_NARRATIVES["未知"])
    elements = _elements(yearly_item)
    _, relation = _relation(chart, elements)
    pillar = yearly_item.get("pillar", "")
    year = yearly_item.get("year", "")
    element_text = "、".join(elements) or "五行信息暂不完整"
    branch_ten_god = yearly_item.get("branch_ten_god") or _main_branch_ten_god(chart, yearly_item.get("zhi", ""))
    branch_relations = yearly_item.get("branch_relations")
    if branch_relations is None:
        branch_relations = analyze_year_branch_relations(chart, yearly_item.get("zhi", ""))
    relation_note = f"结合天干{ten_god}与地支主气{branch_ten_god}，{_relation_text(relation)}。"
    branch_text = (
        " ".join(item.get("text", "") for item in branch_relations)
        if branch_relations
        else "原局四支未见明显六冲，年度重点更多落在五行喜忌与十神主题。"
    )
    keywords = _unique(list(info["keywords"]) + [branch_ten_god, relation] + [item.get("label", "") for item in branch_relations], 8)
    suitable, avoid = _actions_for_relation(relation)
    return {
        "keywords": keywords,
        "annual_keywords": keywords,
        "overall_text": (
            f"{year}年流年为{pillar}，五行侧重{element_text}，天干十神为{ten_god}，"
            f"地支主气可参考{branch_ten_god}。{info['theme']}{relation_note}{branch_text}"
        ),
        "career_text": (
            f"{info['career']}若年度节奏与现实条件配合，适合围绕"
            f"{'、'.join(keywords[:3])}推进；同时要把目标、职责和交付边界写清楚。"
        ),
        "wealth_text": (
            f"{info['wealth']}这一年更适合关注收入来源、现金流、投入成本和回收周期，"
            "涉及合作收益时建议保留记录。"
        ),
        "relationship_text": (
            f"{info['relationship']}如果出现节奏不一致，建议先沟通现实安排和情绪需求，"
            "再讨论承诺或合作。"
        ),
        "health_text": (
            f"{info['health']}结合{element_text}气息，需要关注作息、情绪、压力和身体恢复，"
            "不宜长期透支。"
        ),
        "risk_text": f"风险提醒：{_branch_clash_text(chart, yearly_item.get('zhi', ''))}",
        "advice_text": f"行动建议：{info['advice']}年度策略上建议：{'；'.join(suitable)}。",
        "brief_text": (
            f"{year}年{pillar}以{ten_god}和{branch_ten_god}为主线，"
            f"{relation}，关键词为{'、'.join(keywords[:4])}，适合{'、'.join(suitable[:2])}。"
        ),
        "suitable_actions": _unique(list(suitable) + list(MONTHLY_TEN_GOD_EVENTS.get(ten_god, MONTHLY_TEN_GOD_EVENTS["未知"])["suitable"]), 6),
        "actions_to_avoid": _unique(list(avoid) + list(MONTHLY_TEN_GOD_EVENTS.get(ten_god, MONTHLY_TEN_GOD_EVENTS["未知"])["avoid"]), 6),
    }


def build_monthly_narrative(chart: dict, monthly_item: dict) -> dict:
    """
    根据流月五行、十神、喜忌关系生成月度细分解释。
    """
    ten_god = monthly_item.get("ten_god", "未知")
    info = TEN_GOD_NARRATIVES.get(ten_god, TEN_GOD_NARRATIVES["未知"])
    event_info = MONTHLY_TEN_GOD_EVENTS.get(ten_god, MONTHLY_TEN_GOD_EVENTS["未知"])
    elements = _elements(monthly_item)
    _, relation = _relation(chart, elements)
    month_name = monthly_item.get("month_name", "")
    pillar = monthly_item.get("pillar", "")
    event_tags = monthly_item.get("event_tags", [])
    raw_likely_events = _unique(list(event_info["likely_events"]) + monthly_item.get("rule_events", []), 6)
    likely_events = [f"{month_name}{pillar}：{event}" for event in raw_likely_events]
    suitable, avoid = _actions_for_relation(relation)
    suitable_actions = _unique(list(event_info["suitable"]) + suitable + monthly_item.get("rule_advices", [])[:1], 6)
    actions_to_avoid = _unique(list(event_info["avoid"]) + avoid, 6)
    tag_text = "、".join(event_tags[:4]) or "阶段校准"
    return {
        "theme": f"{month_name}{pillar}：{tag_text}并行，重点看{ten_god}带来的{info['keywords'][0]}。",
        "event_tendency": (
            f"大概率事件倾向：{month_name}{pillar}的五行关系显示，"
            f"{_relation_event_text(relation)}本月事件多围绕{tag_text}展开。"
        ),
        "likely_events": likely_events,
        "career_text": f"事业提醒：{info['career']}本月可重点处理{tag_text}相关事项，推进前先确认优先级。",
        "wealth_text": (
            f"财务提醒：{info['wealth']}{month_name}若涉及{tag_text}中的费用、回款或投入，"
            "建议提前做预算和记录。"
        ),
        "relationship_text": (
            f"关系提醒：{info['relationship']}{month_name}围绕{tag_text}沟通时，"
            f"建议把期待、责任和边界说具体，尤其要留意{ten_god}带来的互动方式。"
        ),
        "health_text": f"健康/状态提醒：{info['health']}结合{month_name}{pillar}节奏，建议留出恢复时间。",
        "risk_text": (
            f"风险提醒：{month_name}{pillar}遇到{tag_text}时，{_relation_event_text(relation)}"
            f"{month_name}处理相关事项时，不宜只凭一时情绪判断。"
        ),
        "advice_text": f"行动建议：{event_info['advice']}同时建议：{'；'.join(suitable_actions[:3])}。",
        "suitable_actions": suitable_actions,
        "actions_to_avoid": actions_to_avoid,
    }


def remove_repetitive_sentences(texts: list[str]) -> list[str]:
    """
    简单去重复机制：如果连续文本高度相似，则替换为更具体的表达。
    """
    result: list[str] = []
    alternatives = [
        "这一段建议结合具体十神主题拆解行动，不要只看表面顺逆。",
        "这里更适合回到事业、财务、关系和状态四个维度分别观察。",
        "如果感到判断相近，可以先记录关键变化，再调整下一步节奏。",
    ]
    repeated = 0
    for text in texts:
        if result and SequenceMatcher(None, result[-1], text).ratio() > 0.86:
            repeated += 1
            result.append(alternatives[repeated % len(alternatives)])
        else:
            repeated = 0
            result.append(text)
    return result
