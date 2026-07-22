"""v1.0.4 不同命盘流月事件差异化测试。"""

from __future__ import annotations

import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


PROFILES = [
    {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False},
    {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州", "use_solar_time": False},
    {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都", "use_solar_time": False},
    {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
]


def _overlap(left: list[str], right: list[str]) -> float:
    a, b = set(left), set(right)
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


class MonthlyEventCrossChartDiversityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_activation_bridge import infer_monthly_likely_events_full
        from core.yearly_engine import analyze_yearly_fortune

        cls.rows = []
        for profile in PROFILES:
            chart = build_bazi_chart(profile)
            yearly = analyze_yearly_fortune(chart, 2026)
            months = analyze_monthly_fortune(chart, 2026)
            cls.rows.append([
                [e.get("event_type", "") for e in infer_monthly_likely_events_full(chart, m, yearly).get("top_events", [])[:3]]
                for m in months
            ])

    def test_same_month_top3_overlap_is_lower_than_before(self):
        overlaps = []
        for month_idx in range(12):
            for i in range(len(self.rows)):
                for j in range(i + 1, len(self.rows)):
                    overlaps.append(_overlap(self.rows[i][month_idx], self.rows[j][month_idx]))
        self.assertLessEqual(sum(overlaps) / len(overlaps), 0.35)

    def test_single_chart_monthly_repeat_rate_is_controlled(self):
        for rows in self.rows:
            flat = [event for month in rows for event in month]
            repeat_rate = 1 - len(set(flat)) / max(1, len(flat))
            self.assertLessEqual(repeat_rate, 0.50)

    def test_full_year_bridge_applies_non_adjacent_month_deduplication(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_activation_bridge import build_year_monthly_event_results
        from core.yearly_engine import analyze_yearly_fortune

        profile = {"name": "重复回归", "gender": "男", "birth_date": "1994-02-16", "birth_hour": 4, "birth_minute": 0}
        chart = build_bazi_chart(profile)
        yearly = analyze_yearly_fortune(chart, 2026)
        results = build_year_monthly_event_results(chart, analyze_monthly_fortune(chart, 2026), yearly)
        top_three = [tuple(event["event_type"] for event in month["top_events"][:3]) for month in results]

        self.assertEqual(len(top_three), len(set(top_three)), top_three)

    def test_public_full_year_entrypoint_calls_the_year_postprocessor(self):
        import core.monthly_event_activation_bridge as bridge
        from unittest.mock import patch

        raw = [{"month": 1, "top_events": []}]
        processed = [{"month": 1, "top_events": [{"event_type": "processed"}]}]
        with patch.object(bridge, "infer_monthly_likely_events_full", return_value=raw[0]), patch(
            "core.monthly_event_inference_engine.postprocess_monthly_events", return_value=processed
        ) as postprocess:
            result = bridge.build_year_monthly_event_results({}, [{}])

        postprocess.assert_called_once_with(raw)
        self.assertEqual(result, processed)

    def test_known_case_has_no_repeated_top_three_set_across_twelve_months(self):
        from core.bazi_engine import build_bazi_chart
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_activation_bridge import build_year_monthly_event_results
        from core.yearly_engine import analyze_yearly_fortune

        profile = {"name": "跨月去重回归", "gender": "男", "birth_date": "1987-04-15", "birth_hour": 6, "birth_minute": 0}
        chart = build_bazi_chart(profile)
        results = build_year_monthly_event_results(
            chart, analyze_monthly_fortune(chart, 2026), analyze_yearly_fortune(chart, 2026)
        )
        top_sets = [frozenset(event["event_type"] for event in month["top_events"][:3]) for month in results]

        self.assertEqual(len(top_sets), len(set(top_sets)), top_sets)


if __name__ == "__main__":
    unittest.main()
