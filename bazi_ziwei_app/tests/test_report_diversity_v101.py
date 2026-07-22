"""v1.0.1+ 命盘报告差异化阈值测试。"""

from __future__ import annotations

import os
import sys
import unittest
from difflib import SequenceMatcher
from itertools import combinations


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


SAMPLE_PROFILES = [
    {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False},
    {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州", "use_solar_time": False},
    {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都", "use_solar_time": False},
    {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
]


MAX_ALLOWED_READABLE_SIMILARITY = 0.60
MAX_ALLOWED_SIGNAL_SIMILARITY = 0.50


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def signal_similarity(left: str, right: str) -> float:
    left_tokens = {item for item in left.replace(",", "|").split("|") if item}
    right_tokens = {item for item in right.replace(",", "|").split("|") if item}
    if not left_tokens and not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def assert_texts_are_distinct(
    testcase: unittest.TestCase,
    label: str,
    texts: list[str],
    threshold: float,
    metric=similarity,
) -> None:
    for left, right in combinations(range(len(texts)), 2):
        score = metric(texts[left], texts[right])
        testcase.assertLessEqual(
            score,
            threshold,
            f"{label} 相似度过高：{SAMPLE_PROFILES[left]['name']} vs "
            f"{SAMPLE_PROFILES[right]['name']} = {score:.3f}",
        )


def build_charts() -> list[dict]:
    from core.bazi_engine import build_bazi_chart

    return [build_bazi_chart(profile) for profile in SAMPLE_PROFILES]


def life_report_text(chart: dict) -> str:
    from report.bazi_report import generate_basic_bazi_report

    report = generate_basic_bazi_report(chart)
    return "\n".join([
        report.get("summary", ""),
        report.get("life_overview", ""),
        report.get("career_text", ""),
        report.get("wealth_text", ""),
        report.get("love_text", ""),
    ])


def chart_type_text(chart: dict) -> str:
    from core.chart_type import classify_chart

    item = classify_chart(chart)
    return "\n".join(str(item.get(key, "")) for key in [
        "basic_pattern",
        "element_pattern",
        "ten_god_pattern",
        "special_combinations",
        "summary",
    ])


def life_overview_text(chart: dict) -> str:
    from core.life_overview_engine import analyze_life_overview

    item = analyze_life_overview(chart)
    return "\n".join([
        item.get("overall_pattern", ""),
        item.get("overall_summary", ""),
        item.get("wealth_overview", {}).get("wealth_summary", ""),
        item.get("romance_overview", {}).get("romance_summary", ""),
        item.get("health_overview", {}).get("health_summary", ""),
        item.get("career_overview", {}).get("career_summary", ""),
        "；".join(item.get("evidence", [])),
    ])


def inquiry_summary_text(chart: dict) -> str:
    from core.report_diversity import build_brief_signature, build_chart_signature_text

    return "\n".join([build_brief_signature(chart), build_chart_signature_text(chart, "综合问盘差异依据")])


def structural_signal_text(chart: dict) -> str:
    from core.chart_fingerprint import build_chart_fingerprint

    fp = build_chart_fingerprint(chart)
    pillars = chart.get("pillars", {})
    strength = chart.get("day_master_strength", {})
    profile = chart.get("profile", {})
    return "|".join([
        profile.get("name", ""),
        profile.get("gender", ""),
        str(profile.get("birth_date", "")),
        str(profile.get("birth_hour", "")),
        str(profile.get("birth_place", "")),
        pillars.get("year", {}).get("pillar", ""),
        pillars.get("month", {}).get("pillar", ""),
        pillars.get("day", {}).get("pillar", ""),
        pillars.get("hour", {}).get("pillar", ""),
        fp.get("day_master", ""),
        fp.get("strength", ""),
        ",".join(fp.get("favorable_elements", [])),
        ",".join(fp.get("unfavorable_elements", [])),
        ",".join(fp.get("top_elements", [])),
        ",".join(fp.get("weak_elements", [])),
        ",".join(fp.get("top_ten_gods", [])),
        ",".join(fp.get("career_pattern_tags", [])),
        ",".join(fp.get("wealth_pattern_tags", [])),
        ",".join(fp.get("love_pattern_tags", [])),
        str(strength.get("net_score", "")),
    ])


class ReportDiversityV101Tests(unittest.TestCase):
    def test_report_quality_thresholds_are_stricter_than_old_acceptance(self):
        from utils.report_quality import READABLE_SIMILARITY_THRESHOLD, STRUCTURAL_SIGNAL_THRESHOLD

        self.assertLessEqual(READABLE_SIMILARITY_THRESHOLD, 0.55)
        self.assertLessEqual(STRUCTURAL_SIGNAL_THRESHOLD, 0.50)

    def test_five_sample_charts_have_distinct_core_report_texts(self):
        charts = build_charts()

        assert_texts_are_distinct(self, "命局总论", [life_report_text(chart) for chart in charts], MAX_ALLOWED_READABLE_SIMILARITY)
        assert_texts_are_distinct(self, "命盘类型", [chart_type_text(chart) for chart in charts], MAX_ALLOWED_READABLE_SIMILARITY)
        assert_texts_are_distinct(self, "命盘总览", [life_overview_text(chart) for chart in charts], MAX_ALLOWED_READABLE_SIMILARITY)
        assert_texts_are_distinct(self, "综合问盘摘要", [inquiry_summary_text(chart) for chart in charts], MAX_ALLOWED_READABLE_SIMILARITY)
        assert_texts_are_distinct(
            self,
            "命盘结构信号",
            [structural_signal_text(chart) for chart in charts],
            MAX_ALLOWED_SIGNAL_SIMILARITY,
            signal_similarity,
        )


if __name__ == "__main__":
    unittest.main()
