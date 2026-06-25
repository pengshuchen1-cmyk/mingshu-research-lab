import os
import sys
import unittest
from difflib import SequenceMatcher


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


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


class SameYearDifferentChartTests(unittest.TestCase):
    def test_same_2026_year_generates_different_yearly_and_monthly_text(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune

        profiles = [
            {"name": "中和火日主", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
            {"name": "身弱土日主", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
        ]
        charts = [build_bazi_chart(profile) for profile in profiles]

        self.assertNotEqual(charts[0]["day_master"], charts[1]["day_master"])
        self.assertNotEqual(
            charts[0]["day_master_strength"]["strength"],
            charts[1]["day_master_strength"]["strength"],
        )

        yearly_reports = [analyze_yearly_fortune(chart, 2026) for chart in charts]
        monthly_reports = [analyze_monthly_fortune(chart, 2026) for chart in charts]

        self.assertLess(text_similarity(yearly_text(yearly_reports[0]), yearly_text(yearly_reports[1])), 0.72)
        self.assertLess(text_similarity(monthly_text(monthly_reports[0]), monthly_text(monthly_reports[1])), 0.72)


if __name__ == "__main__":
    unittest.main()
