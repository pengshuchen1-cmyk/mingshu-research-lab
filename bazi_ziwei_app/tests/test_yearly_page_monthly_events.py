import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class YearlyPageMonthlyEventTests(unittest.TestCase):
    def test_format_monthly_event_hides_developer_fields(self):
        from ui.yearly_page import format_monthly_event_for_display

        event = {
            "event_type": "health_fluctuation",
            "label": "健康状态波动",
            "probability_level": "中等",
            "score": 55.0,
            "reason": "流月为忌神，状态容易波动。",
            "advice": "建议注意作息，重要事项留出缓冲。",
            "trigger_factors": ["流月为忌神", "冲+忌神健康"],
            "source_ids": ["yuanhai_ziping"],
        }

        text = format_monthly_event_for_display(event)

        self.assertIn("健康状态波动｜中等", text)
        self.assertIn("现实表现：流月为忌神，状态容易波动。", text)
        self.assertIn("触发因素：流月为忌神、冲+忌神健康", text)
        self.assertIn("行动建议：建议注意作息，重要事项留出缓冲。", text)
        self.assertNotIn("{'event_type'", text)
        self.assertNotIn("source_ids", text)
        self.assertNotIn("score", text)

    def test_build_monthly_event_results_returns_diverse_top_events(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune
        from ui.yearly_page import build_monthly_event_results

        profile = {
            "name": "年度页面事件样例",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
            "use_solar_time": False,
        }
        chart = build_bazi_chart(profile)
        yearly_data = analyze_yearly_fortune(chart, 2026)
        monthly_data = analyze_monthly_fortune(chart, 2026)

        event_results = build_monthly_event_results(chart, monthly_data, yearly_data, None)
        top3_sets = [
            tuple(event.get("event_type") for event in result.get("top_events", [])[:3])
            for result in event_results
        ]

        self.assertEqual(len(event_results), 12)
        self.assertGreaterEqual(len(set(top3_sets)), 6)
        for left, right in zip(top3_sets, top3_sets[1:]):
            self.assertNotEqual(left, right)


if __name__ == "__main__":
    unittest.main()
