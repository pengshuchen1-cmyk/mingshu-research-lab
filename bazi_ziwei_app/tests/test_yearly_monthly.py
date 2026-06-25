import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def sample_chart() -> dict:
    return {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
            "month": {"gan": "丙", "zhi": "寅", "pillar": "丙寅"},
            "day": {"gan": "甲", "zhi": "午", "pillar": "甲午"},
            "hour": {"gan": "庚", "zhi": "申", "pillar": "庚申"},
        },
        "five_elements": {"木": 3.0, "火": 2.0, "土": 1.0, "金": 2.0, "水": 1.0},
        "ten_god_counts": {"比肩": 2, "食神": 1, "七杀": 1, "偏印": 1},
        "day_master_strength": {
            "strength": "中和",
            "net_score": 1.0,
            "favorable_elements": ["木", "火"],
            "unfavorable_elements": ["金", "水"],
        },
    }


class YearlyMonthlyTests(unittest.TestCase):
    def test_yearly_fortune_returns_required_fields(self):
        from core.yearly_engine import analyze_yearly_fortune

        result = analyze_yearly_fortune(sample_chart(), 2026)

        for key in [
            "year",
            "overall_text",
            "career_text",
            "wealth_text",
            "relationship_text",
            "health_text",
            "suitable_actions",
            "actions_to_avoid",
            "high_attention_months",
            "opportunity_months",
        ]:
            self.assertIn(key, result)
        self.assertEqual(result["year"], 2026)
        self.assertIsInstance(result["keywords"], list)
        self.assertIsInstance(result["opportunity_months"], list)
        self.assertGreater(len(result["suitable_actions"]), 0)
        self.assertGreater(len(result["actions_to_avoid"]), 0)

    def test_monthly_fortune_returns_twelve_items(self):
        from core.monthly_engine import analyze_monthly_fortune

        items = analyze_monthly_fortune(sample_chart(), 2026)

        self.assertEqual(len(items), 12)
        self.assertEqual(items[0]["month"], 1)
        for item in items:
            self.assertIn("career_text", item)
            self.assertIn("advice_text", item)

    def test_v04_copy_avoids_forbidden_absolute_words(self):
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune
        from report.useful_god_report import generate_useful_god_explanation

        yearly_text = str(analyze_yearly_fortune(sample_chart(), 2026))
        monthly_text = str(analyze_monthly_fortune(sample_chart(), 2026))
        useful_text = str(generate_useful_god_explanation(sample_chart()))
        text = yearly_text + monthly_text + useful_text

        for forbidden in ["必定", "一定发财", "一定离婚", "绝对"]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
