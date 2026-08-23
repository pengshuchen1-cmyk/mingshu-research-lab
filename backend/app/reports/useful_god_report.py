"""喜用五行解释。"""

from __future__ import annotations

ELEMENT_DETAILS: dict[str, dict[str, object]] = {
    "木": {
        "keywords": ["学习成长", "规划", "创意", "教育", "生发"],
        "career_advice": "喜木时，事业上适合重视学习、规划、内容创意、教育文化、产品生长和长期能力建设。",
        "life_advice": "生活中可以通过阅读、课程、规律运动、亲近自然和长期计划来增加木的生发感。",
        "risk_advice": "需要注意计划过多但落地不足，成长节奏宜循序渐进。",
    },
    "火": {
        "keywords": ["表达", "传播", "品牌", "审美", "行动力"],
        "career_advice": "喜火时，事业上适合表达、展示、传播、品牌建设、审美相关和需要影响力的方向。",
        "life_advice": "生活中可以增加规律社交、舞台表达、审美训练和适度运动，让行动力更稳定。",
        "risk_advice": "需要注意情绪过热、急于表现或节奏过快，重要决定宜留出冷静期。",
    },
    "土": {
        "keywords": ["稳定", "管理", "承载", "积累", "组织"],
        "career_advice": "喜土时，事业上适合管理、运营、地产、餐饮、组织建设、流程承载和长期积累型工作。",
        "life_advice": "生活中适合建立稳定作息、预算习惯、收纳秩序和可持续的家庭支持系统。",
        "risk_advice": "需要注意过度保守、拖延或被琐事困住，稳定之外也要给成长留空间。",
    },
    "金": {
        "keywords": ["规则", "技术", "结构", "执行", "精修"],
        "career_advice": "喜金时，事业上适合规则、金融、技术、审美精修、执行管理、标准化和结构化能力。",
        "life_advice": "生活中适合通过清晰边界、任务清单、技能训练和财务纪律来增强金的秩序感。",
        "risk_advice": "需要注意过度挑剔、关系表达偏硬或压力内收，沟通时宜保留弹性。",
    },
    "水": {
        "keywords": ["流动", "沟通", "信息", "资源", "智慧"],
        "career_advice": "喜水时，事业上适合沟通、贸易、咨询、信息整合、旅行流动、资源调度和智慧型工作。",
        "life_advice": "生活中适合保持信息流动、复盘记录、旅行学习和弹性安排，让资源连接更顺畅。",
        "risk_advice": "需要注意想法分散、行动拖延或情绪受环境牵动，最好配合明确计划执行。",
    },
}


def generate_useful_god_explanation(chart: dict) -> dict:
    """
    根据命盘喜用五行生成更细的解释。
    """
    strength = chart.get("day_master_strength", {})
    favorable = strength.get("favorable_elements", []) or []
    if not favorable:
        return {
            "favorable_elements": [],
            "summary": "当前命局整体较平衡，喜用五行不宜说死，建议结合大运、流年和现实阶段继续观察。",
            "details": [],
        }

    details = []
    for element in favorable:
        source = ELEMENT_DETAILS.get(element)
        if not source:
            continue
        details.append(
            {
                "element": element,
                "keywords": source["keywords"],
                "career_advice": source["career_advice"],
                "life_advice": source["life_advice"],
                "risk_advice": source["risk_advice"],
            }
        )
    element_text = "、".join(favorable)
    return {
        "favorable_elements": favorable,
        "summary": f"此命盘初判喜用五行为{element_text}。这些方向更适合作为后天选择、职业规划和生活习惯的参考。",
        "details": details,
    }
