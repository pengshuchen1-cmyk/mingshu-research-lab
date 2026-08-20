"""十神计算。"""

from __future__ import annotations

from .bazi_constants import (
    BRANCH_HIDDEN_STEMS,
    CONTROLLING,
    GENERATING,
    STEM_ELEMENTS,
    STEM_YIN_YANG,
)


def get_ten_god(day_master: str, target_gan: str) -> str:
    """
    根据日主天干和目标天干，返回十神。
    """
    if day_master not in STEM_ELEMENTS or target_gan not in STEM_ELEMENTS:
        return "未知"

    day_element = STEM_ELEMENTS[day_master]
    target_element = STEM_ELEMENTS[target_gan]
    same_yin_yang = STEM_YIN_YANG[day_master] == STEM_YIN_YANG[target_gan]

    if day_element == target_element:
        return "比肩" if same_yin_yang else "劫财"
    if GENERATING[day_element] == target_element:
        return "食神" if same_yin_yang else "伤官"
    if CONTROLLING[day_element] == target_element:
        return "偏财" if same_yin_yang else "正财"
    if CONTROLLING[target_element] == day_element:
        return "七杀" if same_yin_yang else "正官"
    if GENERATING[target_element] == day_element:
        return "偏印" if same_yin_yang else "正印"
    return "未知"


def get_hidden_stem_ten_gods(day_master: str, branch: str) -> list[dict]:
    """
    返回某个地支藏干对应的十神列表。
    """
    return [
        {"gan": gan, "ten_god": get_ten_god(day_master, gan)}
        for gan in BRANCH_HIDDEN_STEMS.get(branch, [])
    ]


def count_ten_gods(chart: dict) -> dict:
    """
    统计四柱天干、地支藏干中的十神数量。
    """
    counts = {
        "比肩": 0,
        "劫财": 0,
        "食神": 0,
        "伤官": 0,
        "偏财": 0,
        "正财": 0,
        "七杀": 0,
        "正官": 0,
        "偏印": 0,
        "正印": 0,
        "未知": 0,
    }
    day_master = chart.get("day_master", "")
    for pillar in chart.get("pillars", {}).values():
        gan = pillar.get("gan", "")
        counts[get_ten_god(day_master, gan)] = counts.get(get_ten_god(day_master, gan), 0) + 1
        for hidden_gan in BRANCH_HIDDEN_STEMS.get(pillar.get("zhi", ""), []):
            ten_god = get_ten_god(day_master, hidden_gan)
            counts[ten_god] = counts.get(ten_god, 0) + 1
    return {key: value for key, value in counts.items() if value > 0}
