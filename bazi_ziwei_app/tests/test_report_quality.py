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


class ReportQualityTests(unittest.TestCase):
    def test_text_repetition_fails_when_same_sentence_exceeds_three_times(self):
        from utils.report_quality import check_text_repetition

        text = "事业适合稳步推进。事业适合稳步推进。事业适合稳步推进。事业适合稳步推进。"
        result = check_text_repetition(text)

        self.assertFalse(result["passed"])
        self.assertTrue(any("重复" in issue for issue in result["issues"]))

    def test_monthly_diversity_fails_when_all_themes_are_same(self):
        from utils.report_quality import check_monthly_diversity

        monthly_data = [
            {
                "theme": "平稳观察",
                "event_tags": ["平稳观察"],
                "advice_text": "建议稳步观察。",
            }
            for _ in range(12)
        ]
        result = check_monthly_diversity(monthly_data)

        self.assertFalse(result["passed"])
        self.assertTrue(any("主题" in issue for issue in result["issues"]))

    def test_yearly_detail_fails_when_required_fields_are_missing(self):
        from utils.report_quality import check_yearly_detail

        result = check_yearly_detail({"year": 2026, "overall_text": "年度总览"})

        self.assertFalse(result["passed"])
        self.assertTrue(any("缺少" in issue for issue in result["issues"]))

    def test_generated_yearly_report_contains_deep_fields(self):
        from core.yearly_engine import analyze_yearly_fortune
        from utils.report_quality import check_yearly_detail

        result = analyze_yearly_fortune(sample_chart(), 2026)

        for key in [
            "annual_keywords",
            "suitable_actions",
            "actions_to_avoid",
            "high_attention_months",
            "opportunity_months",
        ]:
            self.assertIn(key, result)
        self.assertTrue(check_yearly_detail(result)["passed"])

    def test_generated_monthly_report_is_event_based_and_diverse(self):
        from core.monthly_engine import analyze_monthly_fortune
        from utils.report_quality import check_monthly_diversity

        result = analyze_monthly_fortune(sample_chart(), 2026)

        self.assertEqual(len(result), 12)
        for item in result:
            for key in [
                "relation_to_favorable",
                "likely_events",
                "risk_text",
                "suitable_actions",
                "actions_to_avoid",
            ]:
                self.assertIn(key, item)
            self.assertGreaterEqual(len(item["likely_events"]), 3)
            self.assertGreaterEqual(len(item["event_tags"]), 3)
        self.assertTrue(check_monthly_diversity(result)["passed"])

    def test_future_ten_years_brief_text_is_not_overly_repetitive(self):
        from core.yearly_engine import analyze_yearly_fortune
        from utils.report_quality import check_text_repetition

        text = "。".join(
            analyze_yearly_fortune(sample_chart(), year)["brief_text"]
            for year in range(2026, 2036)
        )

        self.assertTrue(check_text_repetition(text)["passed"])

    def test_full_markdown_report_is_not_overly_repetitive(self):
        from core.luck_engine import get_luck_cycles
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune
        from report.bazi_report import generate_basic_bazi_report
        from report.export_report import build_markdown_report
        from utils.report_quality import check_text_repetition

        profile = {
            "name": "复核样例",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
            "use_solar_time": False,
        }
        chart = sample_chart()
        chart["profile"] = profile
        report = generate_basic_bazi_report(chart)
        luck_data = get_luck_cycles(profile, chart)
        yearly_data = analyze_yearly_fortune(chart, 2026, luck_data)
        monthly_data = analyze_monthly_fortune(chart, 2026)
        markdown = build_markdown_report(profile, chart, report, luck_data, yearly_data, monthly_data)

        self.assertTrue(check_text_repetition(markdown)["passed"])


if __name__ == "__main__":
    unittest.main()
