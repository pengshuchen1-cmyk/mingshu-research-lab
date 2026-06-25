"""基础八字报告生成。"""

from __future__ import annotations

from core.five_elements import element_summary
from report.useful_god_report import generate_useful_god_explanation

FAVORABLE_ELEMENT_TEXT: dict[str, str] = {
    "木": "喜木时，适合学习、成长、规划、文化、教育、创意、生发类方向。",
    "火": "喜火时，适合表达、曝光、传播、品牌、审美、行动力、影响力建设。",
    "土": "喜土时，适合稳定积累、管理、地产、餐饮、组织、承载类方向。",
    "金": "喜金时，适合规则、金融、结构、技术、执行、管理、审美精修类方向。",
    "水": "喜水时，适合流动、沟通、贸易、信息、咨询、旅行、智慧、资源调度类方向。",
}


def _element_text(chart: dict) -> str:
    """生成五行解释文本。"""
    summary = element_summary(chart.get("five_elements", {}))
    parts = []
    for element, item in summary.items():
        if item["strength"] == "偏旺":
            parts.append(f"你的命局中{element}能量较明显，代表相关特质较容易被放大。")
        elif item["strength"] == "偏弱":
            parts.append(f"你的命局中{element}能量相对不足，相关能力需要通过后天环境、习惯和选择来补足。")
    return " ".join(parts) if parts else "五行分布整体较为平稳，可结合具体柱位继续观察。"


def _ten_god_text(ten_god_counts: dict) -> str:
    """生成十神解释文本。"""
    parts = []
    wealth = ten_god_counts.get("正财", 0) + ten_god_counts.get("偏财", 0)
    output = ten_god_counts.get("食神", 0) + ten_god_counts.get("伤官", 0)
    authority = ten_god_counts.get("正官", 0) + ten_god_counts.get("七杀", 0)
    resource = ten_god_counts.get("正印", 0) + ten_god_counts.get("偏印", 0)
    peer = ten_god_counts.get("比肩", 0) + ten_god_counts.get("劫财", 0)

    if wealth >= 3:
        parts.append("你的命局中财星较明显，说明你对现实资源、收益机会和商业回报较敏感。")
    if output >= 3:
        parts.append("食伤较明显的人通常适合通过表达、技术、内容、创意、项目输出创造价值。")
    if authority >= 3:
        parts.append("官杀较明显的人容易面对规则、责任、目标和外部压力，也适合在组织、管理、标准化领域发展。")
    if resource >= 3:
        parts.append("印星较明显的人通常重视学习、系统、知识、安全感和精神支撑。")
    if peer >= 3:
        parts.append("比劫较明显的人独立性较强，竞争意识和自我驱动力较明显，但也要注意合伙边界。")
    return " ".join(parts) if parts else "十神结构目前未呈现单一特别突出的倾向，可结合大运流年进一步观察。"


def _strength_text(strength_info: dict) -> str:
    """生成日主强弱解释。"""
    strength = strength_info.get("strength", "暂无法判断")
    if strength == "身强":
        return "日主偏强时，自我驱动力、承压能力和主动性较明显，但也需要注意固执、竞争感过强以及人际边界。"
    if strength == "身弱":
        return "日主偏弱时，更需要环境、资源、贵人和系统支持，适合借助平台、专业学习与合作资源逐步成长。"
    if strength == "中和":
        return "日主整体承接力较平衡，但阶段变化仍需结合大运流年进一步判断。"
    return strength_info.get("explanation", "日主强弱暂无法判断，可先参考五行和十神基础结构。")


def _favorable_text(strength_info: dict) -> str:
    """根据喜用五行生成解释。"""
    favorable = strength_info.get("favorable_elements", [])
    if not favorable:
        return "整体较平衡，喜忌不宜说死，需结合大运流年进一步判断。"
    parts = [FAVORABLE_ELEMENT_TEXT[element] for element in favorable if element in FAVORABLE_ELEMENT_TEXT]
    return " ".join(parts) if parts else "喜用五行暂无法明确，可结合大运流年进一步观察。"


def _ten_god_groups(ten_god_counts: dict) -> dict:
    """汇总十神类别数量。"""
    return {
        "wealth": ten_god_counts.get("正财", 0) + ten_god_counts.get("偏财", 0),
        "output": ten_god_counts.get("食神", 0) + ten_god_counts.get("伤官", 0),
        "authority": ten_god_counts.get("正官", 0) + ten_god_counts.get("七杀", 0),
        "resource": ten_god_counts.get("正印", 0) + ten_god_counts.get("偏印", 0),
        "peer": ten_god_counts.get("比肩", 0) + ten_god_counts.get("劫财", 0),
    }


def _career_text(groups: dict) -> str:
    """生成事业倾向文本。"""
    parts = ["事业方面，建议优先选择能长期积累能力和信用的路径。"]
    if groups["authority"] >= 3:
        parts.append("官杀较明显，容易面对规则、责任、职位目标和外部压力，也适合在组织、管理、标准化领域发展。")
    if groups["output"] >= 3:
        parts.append("食伤较明显，适合通过表达、技术输出、内容、创意和传播创造价值。")
    if groups["resource"] >= 3:
        parts.append("印星较明显，学习、证书、系统方法、贵人资源和专业背景会更有帮助。")
    if groups["peer"] >= 3:
        parts.append("比劫较明显，独立性和竞争意识较强，适合明确分工和合伙边界。")
    return " ".join(parts)


def _wealth_text(groups: dict) -> str:
    """生成财富倾向文本。"""
    if groups["wealth"] >= 3:
        return "财富方面，财星较明显，说明你对现实资源、收益机会和商业回报较敏感，但仍建议重视风险边界和现金流节奏。"
    if groups["output"] >= 3:
        return "财富方面，适合通过技术、内容、项目输出或专业服务逐步创造收益。"
    return "财富方面，更适合通过稳定能力、长期信用、预算意识和持续积累来推进。"


def _love_text(groups: dict) -> str:
    """生成关系倾向文本。"""
    if groups["peer"] >= 3:
        return "关系方面，自我意识和边界感较明显，建议在亲密关系和合作关系中提前说清期待。"
    if groups["authority"] >= 3:
        return "关系方面，容易重视承诺、责任和秩序，也需要给彼此保留弹性与沟通空间。"
    if groups["output"] >= 3:
        return "关系方面，表达欲和感受力较明显，建议避免情绪化表达，重要决定宜多沟通。"
    return "关系方面，建议在表达自我和理解对方之间保持平衡，重要决定宜多留沟通空间。"


def _risk_text(groups: dict, strength_info: dict) -> str:
    """生成风险提醒文本。"""
    risks = []
    if strength_info.get("strength") == "身强":
        risks.append("日主偏强时，需要注意过度坚持己见、竞争感偏强或不易借力。")
    elif strength_info.get("strength") == "身弱":
        risks.append("日主偏弱时，需要注意环境压力过大、资源不足或节奏被外界牵动。")
    if groups["wealth"] >= 3:
        risks.append("财星明显时，对机会较敏感，但投资、合伙和现金流仍建议保守评估。")
    if groups["authority"] >= 3:
        risks.append("官杀明显时，责任和压力容易集中，建议建立稳定作息和可执行计划。")
    if groups["peer"] >= 3:
        risks.append("比劫明显时，朋友、同业和合伙议题需要提前明确边界。")
    return " ".join(risks) if risks else "目前基础结构未显示单一特别突出的风险点，仍建议结合现实选择谨慎判断。"


def generate_basic_bazi_report(chart: dict) -> dict:
    """
    根据 chart 生成基础中文解释。
    """
    if chart.get("error"):
        message = chart["error"]
        return {
            "summary": message,
            "day_master": "",
            "five_element_text": message,
            "ten_god_text": message,
            "strength_text": message,
            "favorable_text": message,
            "useful_god_text": message,
            "useful_god_details": [],
            "personality_text": "命盘生成成功后可查看性格倾向。",
            "career_text": "命盘生成成功后可查看事业倾向。",
            "wealth_text": "命盘生成成功后可查看财富倾向。",
            "love_text": "命盘生成成功后可查看关系倾向。",
            "risk_text": "命盘生成成功后可查看风险提醒。",
            "advice": "请检查出生信息后重新生成命盘。",
        }

    day_master = chart.get("day_master", "")
    strength_info = chart.get("day_master_strength", {})
    five_element_text = _element_text(chart)
    ten_god_text = _ten_god_text(chart.get("ten_god_counts", {}))
    counts = chart.get("ten_god_counts", {})
    groups = _ten_god_groups(counts)
    strength_text = _strength_text(strength_info)
    favorable_text = _favorable_text(strength_info)
    useful_god = generate_useful_god_explanation(chart)

    summary = (
        f"此命盘日主为{day_master}，日主强弱初判为{strength_info.get('strength', '暂无法判断')}。"
        "以下解读基于四柱、藏干、五行、十神和日主强弱的基础统计，"
        "适合作为自我观察和后续深入分析的参考。"
    )
    personality_text = strength_text
    career_text = _career_text(groups)
    wealth_text = _wealth_text(groups)
    love_text = _love_text(groups)
    risk_text = _risk_text(groups, strength_info)
    advice = (
        "建议把命盘作为观察工具，结合现实环境、教育背景、职业选择和长期习惯一起判断。"
        "当前喜忌仍属于初判，后续需要结合大运、流年和个人经历验证阶段变化。"
    )

    return {
        "summary": summary,
        "day_master": day_master,
        "five_element_text": five_element_text,
        "ten_god_text": ten_god_text,
        "strength_text": strength_text,
        "favorable_text": favorable_text,
        "useful_god_text": useful_god.get("summary", ""),
        "useful_god_details": useful_god.get("details", []),
        "personality_text": personality_text,
        "career_text": career_text,
        "wealth_text": wealth_text,
        "love_text": love_text,
        "risk_text": risk_text,
        "advice": advice,
    }
