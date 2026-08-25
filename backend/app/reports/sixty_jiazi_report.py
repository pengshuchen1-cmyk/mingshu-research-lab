"""六十甲子说明书。

把六十甲子与纳音转成用户能读懂的四柱名片和报告章节。
纳音只作为传统象意解释层，不替代日主强弱、十神、喜忌和大运流年。
"""

from __future__ import annotations

from collections import Counter

from ..analysis.sixty_jiazi import get_jiazi_by_pillar

PILLAR_LIFE_AREAS = {
    "year": {
        "label": "年柱",
        "life_area": "早年环境、家族背景、外部圈层",
        "focus": "这一柱更像一个人的外部底色，常用来理解早年环境、长辈氛围和社会圈层的起点。",
    },
    "month": {
        "label": "月柱",
        "life_area": "事业环境、社会位置、工作节奏",
        "focus": "这一柱和月令关系最密，常用来观察一个人进入社会后的主环境、工作节奏和资源平台。",
    },
    "day": {
        "label": "日柱",
        "life_area": "自己、伴侣关系、核心底色",
        "focus": "这一柱贴近日主和夫妻宫，更适合观察自己的核心底色、一对一关系和亲密相处方式。",
    },
    "hour": {
        "label": "时柱",
        "life_area": "长期规划、子女副业、晚年趋势",
        "focus": "这一柱更偏长期结果，常用来理解未来规划、副业成果、子女议题和后半程节奏。",
    },
}

ELEMENT_REALITY_HINTS = {
    "木": {
        "keywords": ["成长", "规划", "学习", "生发"],
        "reality": "现实里更容易和学习成长、规划扩展、审美创意、人际生发有关。",
        "advice": "适合把想法写成计划，循序推进，避免只想扩张而忽略落地。",
    },
    "火": {
        "keywords": ["表达", "行动", "曝光", "热度"],
        "reality": "现实里更容易和表达展示、行动推进、传播曝光、情绪热度有关。",
        "advice": "适合主动表达和推进事项，也要注意节奏，避免过急过耗。",
    },
    "土": {
        "keywords": ["稳定", "承载", "资源", "积累"],
        "reality": "现实里更容易和稳定积累、组织承载、土地房产、现实责任有关。",
        "advice": "适合建立秩序和长期积累，也要避免过度保守或压力堆积。",
    },
    "金": {
        "keywords": ["规则", "结构", "执行", "收束"],
        "reality": "现实里更容易和规则制度、技术结构、执行标准、边界收束有关。",
        "advice": "适合做清晰规范和专业精修，也要注意表达不要过硬。",
    },
    "水": {
        "keywords": ["流动", "信息", "沟通", "调度"],
        "reality": "现实里更容易和信息流动、沟通咨询、资源调度、出行变化有关。",
        "advice": "适合保持弹性和信息敏感度，也要避免想太多、落地太慢。",
    },
}


def _normalize_pillar_key(key: str, pillar: dict) -> str:
    name = pillar.get("name", "")
    if key in PILLAR_LIFE_AREAS:
        return key
    mapping = {"年柱": "year", "月柱": "month", "日柱": "day", "时柱": "hour"}
    return mapping.get(name, key)


def build_four_pillar_jiazi_cards(chart: dict) -> list[dict]:
    """基于 chart 生成四柱甲子名片。"""
    cards: list[dict] = []
    pillars = chart.get("pillars", {}) or {}
    for key in ["year", "month", "day", "hour"]:
        pillar = pillars.get(key, {}) or {}
        pillar_name = pillar.get("pillar", "")
        entry = get_jiazi_by_pillar(pillar_name)
        if not entry:
            continue
        area = PILLAR_LIFE_AREAS.get(_normalize_pillar_key(key, pillar), PILLAR_LIFE_AREAS[key])
        element_hint = ELEMENT_REALITY_HINTS.get(entry.get("nayin_element", ""), {})
        user_explanation = (
            f"{area['label']}代表{area['life_area']}。{area['focus']}"
            f"{entry['pillar']}由{entry['gan']}干与{entry['zhi']}支组成，"
            f"纳音为{entry['nayin']}，可作为这一柱的传统象意参考。"
        )
        cards.append(
            {
                "position": key,
                "label": area["label"],
                "pillar": entry["pillar"],
                "gan": entry["gan"],
                "zhi": entry["zhi"],
                "gan_element": entry["gan_element"],
                "zhi_element": entry["zhi_element"],
                "nayin": entry["nayin"],
                "nayin_element": entry["nayin_element"],
                "life_area": area["life_area"],
                "user_explanation": user_explanation,
                "reality_hint": entry.get("reality_mapping") or element_hint.get("reality", "现实里可作为这一柱气质的辅助说明。"),
                "advice": entry.get("user_advice") or element_hint.get("advice", "建议结合日主、十神、喜忌和现实经历综合理解。"),
                "keywords": entry.get("symbolic_keywords") or element_hint.get("keywords", []),
                "boundary_note": "纳音用于辅助理解四柱气质，不单独判断吉凶，也不作为断事核心。",
                "source_ids": entry.get("source_ids", []),
                "basis": entry.get("basis", ""),
            }
        )
    return cards


def compare_nayin_with_chart_elements(chart: dict) -> dict:
    """对比纳音五行与原局真实五行分布。"""
    cards = build_four_pillar_jiazi_cards(chart)
    nayin_counter = Counter(card.get("nayin_element", "") for card in cards if card.get("nayin_element"))
    nayin_distribution = {element: int(nayin_counter.get(element, 0)) for element in ["木", "火", "土", "金", "水"]}
    raw_elements = chart.get("five_elements", {}) or {}
    total = sum(float(v) for v in raw_elements.values()) or 1.0
    chart_distribution = {
        element: {
            "score": round(float(raw_elements.get(element, 0)), 2),
            "ratio": round(float(raw_elements.get(element, 0)) / total * 100, 1),
        }
        for element in ["木", "火", "土", "金", "水"]
    }
    dominant_nayin = [k for k, v in nayin_distribution.items() if v == max(nayin_distribution.values(), default=0) and v > 0]
    dominant_chart = sorted(chart_distribution.items(), key=lambda item: -item[1]["score"])
    return {
        "nayin_distribution": nayin_distribution,
        "chart_distribution": chart_distribution,
        "dominant_nayin_elements": dominant_nayin,
        "dominant_chart_elements": [item[0] for item in dominant_chart[:2] if item[1]["score"] > 0],
        "explanation": (
            "纳音五行像四柱的传统象意标签，适合帮助用户理解每一柱的文化气质；"
            "原局五行来自天干、地支、藏干和月令权重，更适合判断真实命局结构。"
            "实际分析以原局五行为主，纳音作为辅助说明。"
        ),
    }


def _format_distribution(distribution: dict) -> str:
    return "｜".join(f"{element}{distribution.get(element, 0)}" for element in ["木", "火", "土", "金", "水"])


def build_sixty_jiazi_markdown(chart: dict) -> str:
    """生成可并入完整报告的六十甲子说明书章节。"""
    cards = build_four_pillar_jiazi_cards(chart)
    comparison = compare_nayin_with_chart_elements(chart)
    lines = [
        "## 六十甲子说明书",
        "- 本节把四柱干支转成用户能看懂的甲子名片，帮助理解年柱、月柱、日柱、时柱各自的传统象意。",
        "- 说明边界：六十甲子与纳音是知识层和解释层，不作为断事核心；具体判断仍以日主强弱、十神、喜忌、大运流年为主。",
        "",
        "### 四柱甲子名片",
    ]
    for card in cards:
        keywords = "、".join(card.get("keywords", [])) or "传统象意"
        lines.extend(
            [
                f"- {card['label']}：{card['pillar']}｜纳音：{card['nayin']}｜对应：{card['life_area']}",
                f"  - 这是什么意思：{card['user_explanation']}",
                f"  - 现实里怎么看：{card['reality_hint']}",
                f"  - 关键词：{keywords}",
                f"  - 建议：{card['advice']}",
            ]
        )
    lines.extend(
        [
            "",
            "### 纳音与原局五行对比",
            f"- 纳音五行分布：{_format_distribution(comparison['nayin_distribution'])}",
            "- 原局五行分布："
        ]
    )
    for element, item in comparison["chart_distribution"].items():
        lines.append(f"  - {element}：{item['score']}，占比 {item['ratio']}%")
    lines.extend(
        [
            f"- 如何理解：{comparison['explanation']}",
            "- 立春边界：八字年柱通常以立春为换年点，不是简单按公历1月1日切换；2月初出生尤其需要复核。",
        ]
    )
    return "\n".join(lines)
