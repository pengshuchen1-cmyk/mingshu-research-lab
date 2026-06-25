"""五行统计。"""

from __future__ import annotations

from core.bazi_constants import BRANCH_HIDDEN_STEMS, FIVE_ELEMENT_ORDER, STEM_ELEMENTS

HIDDEN_STEM_WEIGHTS: list[float] = [1.0, 0.5, 0.3]


def calculate_five_elements(chart: dict) -> dict:
    """
    根据四柱天干、地支、藏干计算五行权重。
    """
    scores = {element: 0.0 for element in FIVE_ELEMENT_ORDER}
    pillars = chart.get("pillars", {})

    for key, pillar in pillars.items():
        gan = pillar.get("gan", "")
        zhi = pillar.get("zhi", "")

        if gan in STEM_ELEMENTS:
            scores[STEM_ELEMENTS[gan]] += 1.0

        hidden_stems = BRANCH_HIDDEN_STEMS.get(zhi, [])
        for index, hidden_gan in enumerate(hidden_stems):
            weight = HIDDEN_STEM_WEIGHTS[index] if index < len(HIDDEN_STEM_WEIGHTS) else 0.3
            scores[STEM_ELEMENTS[hidden_gan]] += weight

        if key == "month" and hidden_stems:
            scores[STEM_ELEMENTS[hidden_stems[0]]] += 2.0

    return {element: round(score, 2) for element, score in scores.items()}


def judge_element_strength(score: float, total: float) -> str:
    """
    根据占比判断五行强弱。
    """
    if total <= 0:
        return "偏弱"
    ratio = score / total
    if ratio >= 0.30:
        return "偏旺"
    if ratio >= 0.15:
        return "中等"
    return "偏弱"


def element_summary(five_elements: dict) -> dict:
    """
    返回每个五行的分数、占比、强弱判断。
    """
    total = sum(float(score) for score in five_elements.values())
    summary = {}
    for element in FIVE_ELEMENT_ORDER:
        score = float(five_elements.get(element, 0.0))
        ratio = score / total if total else 0.0
        summary[element] = {
            "score": round(score, 2),
            "ratio": round(ratio * 100, 1),
            "strength": judge_element_strength(score, total),
        }
    return summary
