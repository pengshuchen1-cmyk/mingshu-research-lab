"""v1.0.4 流月事件分类丰富度测试。"""

from __future__ import annotations

import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class MonthlyEventCategoryRichnessTests(unittest.TestCase):
    def test_top3_are_not_single_category_when_possible(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_activation_bridge import infer_monthly_likely_events_full
        from core.yearly_engine import analyze_yearly_fortune

        chart = build_bazi_chart({"name": "分类丰富度", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False})
        yearly = analyze_yearly_fortune(chart, 2026)
        months = analyze_monthly_fortune(chart, 2026)
        for month in months:
            result = infer_monthly_likely_events_full(chart, month, yearly)
            top3 = result.get("top_events", [])[:3]
            categories = {e.get("category", "") for e in top3}
            self.assertGreaterEqual(len(categories), 2)
            for event in top3:
                self.assertGreaterEqual(event.get("trigger_count", 0), 2)
                self.assertGreaterEqual(len(event.get("evidence", [])), 2)
                self.assertGreaterEqual(len(event.get("source_ids", [])), 1)

    def test_page_safe_payload_has_no_raw_dict_tokens(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_activation_bridge import infer_monthly_likely_events_full

        chart = build_bazi_chart({"name": "页面安全", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False})
        result = infer_monthly_likely_events_full(chart, analyze_monthly_fortune(chart, 2026)[0])
        text = "\n".join(str(e.get(key, "")) for e in result.get("top_events", []) for key in ["label", "one_line", "advice", "basis"])
        self.assertNotIn("{'event_type'", text)
        self.assertNotIn("source_ids':", text)
        self.assertNotIn("trigger_factors':", text)


if __name__ == "__main__":
    unittest.main()
