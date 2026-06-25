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


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def report_text(report: dict) -> str:
    parts = [
        report.get("title", ""),
        " ".join(report.get("evidence", [])),
        " ".join(str(value) for key, value in report.items() if key not in {"title", "sections", "disclaimer"}),
    ]
    for section in report.get("sections", []):
        parts.append(section.get("title", ""))
        parts.append(section.get("text", ""))
    return "\n".join(parts)


def yearly_text(data: dict) -> str:
    return "\n".join(
        str(data.get(key, ""))
        for key in [
            "overall_text",
            "career_text",
            "wealth_text",
            "relationship_text",
            "health_text",
            "risk_text",
            "advice_text",
        ]
    )


def monthly_text(items: list[dict]) -> str:
    return "\n".join(
        "\n".join(
            [
                item.get("theme", ""),
                item.get("event_tendency", ""),
                " ".join(item.get("likely_events", [])),
                item.get("career_text", ""),
                item.get("wealth_text", ""),
                item.get("relationship_text", ""),
                item.get("risk_text", ""),
                item.get("advice_text", ""),
            ]
        )
        for item in items
    )


class CrossSampleDiversityTests(unittest.TestCase):
    def test_chart_fingerprint_differs_for_distinct_samples(self):
        from core.bazi_engine import build_bazi_chart
        from core.chart_fingerprint import build_chart_fingerprint

        fingerprints = [build_chart_fingerprint(build_bazi_chart(profile)) for profile in SAMPLE_PROFILES]
        keys = [
            (
                item["day_master"],
                item["strength"],
                tuple(item["top_ten_gods"]),
                tuple(item["career_pattern_tags"]),
                tuple(item["wealth_pattern_tags"]),
                tuple(item["love_pattern_tags"]),
            )
            for item in fingerprints
        ]

        self.assertEqual(len(keys), len(set(keys)))

    def test_special_reports_are_not_overly_similar_across_distinct_charts(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune
        from report.career_report import generate_career_report
        from report.love_report import generate_love_report
        from report.wealth_report import generate_wealth_report

        charts = [(profile, build_bazi_chart(profile)) for profile in SAMPLE_PROFILES]
        report_sets = {
            "career": [report_text(generate_career_report(chart)) for _, chart in charts],
            "wealth": [report_text(generate_wealth_report(chart)) for _, chart in charts],
            "love": [report_text(generate_love_report(chart, profile)) for profile, chart in charts],
            "yearly": [yearly_text(analyze_yearly_fortune(chart, 2026)) for _, chart in charts],
            "monthly": [monthly_text(analyze_monthly_fortune(chart, 2026)) for _, chart in charts],
        }

        for report_type, texts in report_sets.items():
            for left, right in combinations(range(len(texts)), 2):
                similarity = text_similarity(texts[left], texts[right])
                self.assertLess(
                    similarity,
                    0.72,
                    f"{report_type} report too similar: {SAMPLE_PROFILES[left]['name']} vs {SAMPLE_PROFILES[right]['name']} = {similarity:.3f}",
                )


if __name__ == "__main__":
    unittest.main()
