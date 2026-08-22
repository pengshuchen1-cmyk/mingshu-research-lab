# ruff: noqa  # Frozen compatibility port; protected by migration contracts.
"""大运阶段倾向分析。"""

from __future__ import annotations

from .narrative_engine import build_luck_stage_narrative, build_luck_stage_sections


def analyze_luck_stage(chart: dict, luck_item: dict) -> dict:
    """
    根据命盘喜忌五行和某一步大运，分析该阶段倾向。
    """
    try:
        strength_info = chart.get("day_master_strength", {})
        favorable_elements = set(strength_info.get("favorable_elements", []))
        unfavorable_elements = set(strength_info.get("unfavorable_elements", []))
        gan_element = luck_item.get("gan_element", "")
        zhi_element = luck_item.get("zhi_element", "")

        score = 0
        if gan_element in favorable_elements:
            score += 2
        if zhi_element in favorable_elements:
            score += 2
        if gan_element in unfavorable_elements:
            score -= 2
        if zhi_element in unfavorable_elements:
            score -= 2

        if score >= 3:
            level = "偏助力"
        elif 1 <= score < 3:
            level = "小有助力"
        elif -1 <= score <= 0:
            level = "平稳观察"
        elif -3 < score < -1:
            level = "略有压力"
        else:
            level = "压力较明显"
        text = build_luck_stage_narrative(chart, luck_item)
        sections = build_luck_stage_sections(chart, luck_item)

        return {"stage_score": score, "stage_level": level, "stage_text": text, **sections}
    except Exception as exc:
        return {
            "stage_score": 0,
            "stage_level": "平稳观察",
            "stage_text": f"阶段倾向暂无法分析：{exc}",
        }
