"""喜忌用神分析入口。"""

from __future__ import annotations

from report.useful_god_report import generate_useful_god_explanation


def analyze_useful_god(chart: dict) -> dict:
    """
    返回喜用五行细化解释。
    """
    return generate_useful_god_explanation(chart)
