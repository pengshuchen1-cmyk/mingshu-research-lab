"""桃花星检测引擎。

基于传统命理中的桃花星（咸池）规则：
  申子辰见酉  巳酉丑见午
  寅午戌见卯  亥卯未见子

参考来源：《渊海子平》神煞篇、《三命通会》神煞体系。
"""

from __future__ import annotations


PEACH_BLOSSOM_RULES: dict[str, tuple[str, str]] = {
    # (day_group_zhi_pattern, peach_zhi)
    # 以日支所属的三合局来判断桃花星位置
    "申": ("申子辰", "酉"),
    "子": ("申子辰", "酉"),
    "辰": ("申子辰", "酉"),
    "巳": ("巳酉丑", "午"),
    "酉": ("巳酉丑", "午"),
    "丑": ("巳酉丑", "午"),
    "寅": ("寅午戌", "卯"),
    "午": ("寅午戌", "卯"),
    "戌": ("寅午戌", "卯"),
    "亥": ("亥卯未", "子"),
    "卯": ("亥卯未", "子"),
    "未": ("亥卯未", "子"),
}

DATE_BRANCH_GROUPS = {
    "申": "申子辰", "子": "申子辰", "辰": "申子辰",
    "巳": "巳酉丑", "酉": "巳酉丑", "丑": "巳酉丑",
    "寅": "寅午戌", "午": "寅午戌", "戌": "寅午戌",
    "亥": "亥卯未", "卯": "亥卯未", "未": "亥卯未",
}

PEACH_COLORS = {
    "年": "#D4A843",
    "月": "#C49A3C",
    "日": "#B8860B",
    "时": "#A07830",
}

PEACH_MEANINGS = {
    "年": "年支带桃花：早年异性缘较早出现，可能在长辈、家庭圈层中有桃花机缘。",
    "月": "月支带桃花：青年阶段感情机会较活跃，桃花出现在成长环境、学习和早期社交中。",
    "日": "日支带桃花（墙内桃花）：个人魅力和吸引力较强，亲密关系中对伴侣有较深的情感连接。",
    "时": "时支带桃花（墙外桃花）：晚年生缘或偏缘机会较多，也代表艺术、审美、创作方面的天赋和吸引力。",
}


def detect_peach_blossom_stars(chart: dict) -> dict:
    """
    检测八字是否带子午卯酉桃花星。

    以日支查属于哪个三合局，再查该局桃花星出现在年、月、日、时支中。
    """
    pillars = chart.get("pillars", {})
    day_zhi = pillars.get("day", {}).get("zhi", "")

    if not day_zhi or day_zhi not in PEACH_BLOSSOM_RULES:
        return {
            "has_peach_blossom": False,
            "peach_blossoms": [],
            "peach_zhi": "",
            "source_branch_group": "",
            "day_zhi": day_zhi,
            "peach_count": 0,
            "positions": [],
            "meaning": "",
        }

    source_group, peach_zhi = PEACH_BLOSSOM_RULES[day_zhi]
    branch_group_name = DATE_BRANCH_GROUPS.get(day_zhi, "")

    # 检查四柱中是否有桃花星地支
    peach_positions: list[dict] = []
    for key in ("year", "month", "day", "hour"):
        zhi = pillars.get(key, {}).get("zhi", "")
        if zhi == peach_zhi:
            label = {"year": "年支", "month": "月支", "day": "日支", "hour": "时支"}.get(key, "")
            peach_positions.append({
                "pillar": key,
                "label": label,
                "zhi": zhi,
                "meaning": PEACH_MEANINGS.get(key, ""),
            })

    # 综合解读
    if not peach_positions:
        meaning = f"命局日支为{day_zhi}，桃花星为{peach_zhi}，但四柱中未见{peach_zhi}透出。桃花需要大运流年引动才会出现。"
    else:
        position_texts = [p["label"] for p in peach_positions]
        position_meanings = [p["meaning"] for p in peach_positions]
        meaning_parts = [f"命局日支为{day_zhi}（{branch_group_name}局），桃花星为{peach_zhi}。"]
        meaning_parts.append(f"桃花出现在{'、'.join(position_texts)}。")
        meaning_parts.extend(position_meanings)

        if len(peach_positions) >= 2:
            meaning_parts.append("多柱带桃花，异性缘和社会吸引力整体较明显。")
        elif len(peach_positions) == 1:
            meaning_parts.append("桃花在单个柱位，感情缘分在特定人生阶段较容易到来。")
        meaning = "".join(meaning_parts)

    return {
        "has_peach_blossom": bool(peach_positions),
        "peach_blossoms": peach_positions,
        "peach_zhi": peach_zhi,
        "source_branch_group": branch_group_name,
        "day_zhi": day_zhi,
        "peach_count": len(peach_positions),
        "positions": [p["pillar"] for p in peach_positions],
        "meaning": meaning,
        "basis": "基于渊海子平神煞篇之桃花星（咸池）规则，以日支查三合局对宫之桃花。",
        "source_titles": ["渊海子平", "三命通会"],
    }
