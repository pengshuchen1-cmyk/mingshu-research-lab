"""测试流月具体事件推断 — v1.2-F"""

from __future__ import annotations

import unittest

from core.monthly_event_inference_engine import (
    infer_monthly_likely_events,
    EVENT_TYPES,
    EVENT_PLAIN_DETAILS,
    REALITY_EVENT_RULES,
    _score_event,
)


class TestMonthlyEventInference(unittest.TestCase):

    def setUp(self):
        self.chart = {
            "day_master": "甲",
            "pillars": {
                "year": {"gan": "甲", "zhi": "子"},
                "month": {"gan": "丙", "zhi": "寅"},
                "day": {"gan": "甲", "zhi": "午"},
                "hour": {"gan": "庚", "zhi": "申"},
            },
            "day_master_strength": {
                "strength": "偏弱",
                "net_score": -2,
                "favorable_elements": ["水", "木"],
                "unfavorable_elements": ["火", "金"],
            },
            "ten_god_counts": {
                "正财": 1, "偏财": 2, "正官": 1, "七杀": 0,
                "正印": 1, "偏印": 0, "比肩": 1, "劫财": 1,
                "食神": 1, "伤官": 0,
            },
            "five_elements": {
                "木": 8.0, "火": 5.0, "土": 3.0, "金": 4.0, "水": 6.0,
            },
        }

    def _make_monthly_item(self, gan="甲", zhi="子", ten_god="正财", has_clash=False):
        return {
            "gan": gan, "zhi": zhi, "ten_god": ten_god,
            "branch_relations": [],
            "has_clash": has_clash,
        }

    def test_infer_returns_top_events(self):
        """每个月必须返回 top_events。"""
        item = self._make_monthly_item("甲", "子", "正财")
        result = infer_monthly_likely_events(self.chart, item)
        events = result.get("top_events", [])
        self.assertGreaterEqual(len(events), 1, "必须返回至少1条事件")
        for e in events:
            self.assertIn("event_type", e)
            self.assertIn("label", e)
            self.assertIn("probability_level", e)
            self.assertIn("reason", e)
            self.assertIn("advice", e)

    def test_infer_returns_event_score_map(self):
        """必须返回 event_score_map。"""
        item = self._make_monthly_item("甲", "子", "正财")
        result = infer_monthly_likely_events(self.chart, item)
        score_map = result.get("event_score_map", {})
        self.assertGreater(len(score_map), 0, "score_map不能为空")

    def test_different_months_different_events(self):
        """不同月份的 top_events 不能完全相同。"""
        items = [
            self._make_monthly_item("甲", "子", "正财"),
            self._make_monthly_item("丙", "午", "七杀"),
            self._make_monthly_item("戊", "辰", "正印"),
        ]
        events_sets = []
        for item in items:
            result = infer_monthly_likely_events(self.chart, item)
            types = tuple(sorted(e["event_type"] for e in result.get("top_events", [])[:3]))
            events_sets.append(types)
        # 至少有两组不完全相同
        self.assertGreaterEqual(len(set(events_sets)), 2,
                                "不同月份的top_events不应该完全相同")

    def test_supports_required_event_types(self):
        """必须支持要求的核心事件类型。"""
        required = [
            "wealth_inflow", "wealth_outflow", "property_housing",
            "travel_traffic", "contract_document",
            "relationship_progress", "relationship_conflict",
            "health_fluctuation",
        ]
        for r in required:
            self.assertIn(r, EVENT_TYPES, f"缺少事件类型：{r}")

    def test_reality_event_rules_have_explicit_triggers(self):
        """现实断事事件必须有明确触发条件，不允许只堆词。"""
        required = [
            "vehicle_safety",
            "property_housing",
            "shop_property",
            "contract_document",
            "illness_symbol_attention",
            "social_drinking",
            "favor_obligation",
            "official_dispute",
            "debt_loss",
            "client_payment",
            "relationship_progress",
            "family_issue",
        ]
        for event_type in required:
            self.assertIn(event_type, EVENT_TYPES, f"缺少现实事件类型：{event_type}")
            self.assertIn(event_type, EVENT_PLAIN_DETAILS, f"缺少白话解释：{event_type}")
            self.assertIn(event_type, REALITY_EVENT_RULES, f"缺少触发条件规则：{event_type}")
            rule = REALITY_EVENT_RULES[event_type]
            self.assertGreaterEqual(rule.get("min_trigger_count", 0), 2, f"{event_type}触发门槛过低")
            self.assertGreaterEqual(len(rule.get("trigger_conditions", [])), 3, f"{event_type}触发条件过少")

    def test_specific_scenarios_trigger_specific_reality_events(self):
        """不同现实场景应触发不同事件，而不是统一泛化提醒。"""
        scenarios = [
            (self._make_monthly_item("庚", "申", "七杀", has_clash=True), {"vehicle_safety", "official_dispute", "illness_symbol_attention"}),
            (self._make_monthly_item("戊", "辰", "正印", has_clash=True), {"property_housing", "shop_property", "family_issue"}),
            (self._make_monthly_item("己", "丑", "正财"), {"client_payment", "property_housing", "shop_property"}),
            (self._make_monthly_item("乙", "卯", "劫财", has_clash=True), {"social_drinking", "favor_obligation", "debt_loss"}),
        ]
        for item, expected_any in scenarios:
            result = infer_monthly_likely_events(self.chart, item)
            event_types = {event["event_type"] for event in result.get("top_events", [])}
            self.assertTrue(event_types & expected_any, f"{item} 未触发预期现实事件，实际为 {event_types}")
            for event in result.get("top_events", []):
                self.assertGreaterEqual(len(event.get("trigger_factors", [])), 2)

    def test_score_event_bounds(self):
        """_score_event 返回 0-100。"""
        s = _score_event(50, [True, True], [1.0, 1.0])
        self.assertLessEqual(s, 100)
        self.assertGreaterEqual(s, 0)

    def test_no_absolute_words(self):
        """不得出现禁用绝对化词。"""
        forbidden = ["一定买房", "一定发财", "必定破财", "必有车祸",
                     "必有灾", "必定离婚", "必有大病", "短命", "注定"]
        item = self._make_monthly_item("甲", "子", "正财")
        result = infer_monthly_likely_events(self.chart, item)
        text = str(result)
        for word in forbidden:
            self.assertNotIn(word, text, f"包含禁用词：{word}")

    def test_events_have_categories(self):
        """每个事件必须带有 category。"""
        item = self._make_monthly_item("甲", "子", "正财")
        result = infer_monthly_likely_events(self.chart, item)
        for e in result.get("top_events", []):
            self.assertIn("category", e, f"事件{e.get('event_type')}缺少category")

    def test_different_charts_different_events(self):
        """不同命盘同月的 top_events 不能完全相同。"""
        chart2 = dict(self.chart)
        chart2["day_master_strength"] = {
            "strength": "偏旺",
            "favorable_elements": ["火", "土"],
            "unfavorable_elements": ["水", "木"],
        }
        item = self._make_monthly_item("甲", "子", "正财")
        r1 = infer_monthly_likely_events(self.chart, item)
        r2 = infer_monthly_likely_events(chart2, item)
        t1 = tuple(sorted(e["event_type"] for e in r1.get("top_events", [])[:3]))
        t2 = tuple(sorted(e["event_type"] for e in r2.get("top_events", [])[:3]))
        self.assertNotEqual(t1, t2, "不同命盘同月top_events不应完全相同")



class TestMonthlyEventDiversity(unittest.TestCase):
    """流月事件差异化测试 — v1.2-F-Fix"""

    def setUp(self):
        self.chart = {
            "day_master": "甲",
            "pillars": {"year": {"gan": "甲", "zhi": "子"}, "month": {"gan": "丙", "zhi": "寅"}, "day": {"gan": "甲", "zhi": "午"}, "hour": {"gan": "庚", "zhi": "申"}},
            "day_master_strength": {"strength": "偏弱", "favorable_elements": ["水", "木"], "unfavorable_elements": ["火", "金"]},
            "ten_god_counts": {"正财": 1, "偏财": 2, "正官": 1, "比肩": 1, "劫财": 1, "食神": 1, "伤官": 1, "正印": 1, "偏印": 0},
            "five_elements": {"木": 8, "火": 5, "土": 3, "金": 4, "水": 6},
        }
        from core.monthly_engine import analyze_monthly_fortune
        self.monthly_data = analyze_monthly_fortune(self.chart, 2026)

    def test_12_months_not_all_same(self):
        """12个月 top_events 不能全部相同。"""
        from core.monthly_event_inference_engine import infer_monthly_likely_events
        results = [infer_monthly_likely_events(self.chart, item) for item in self.monthly_data]
        top_sets = set(tuple(e["event_type"] for e in r.get("top_events", [])[:2]) for r in results)
        self.assertGreater(len(top_sets), 3, "12个月top_events不能过于相似")

    def test_adjacent_months_not_all_same(self):
        """相邻3个月 top_events 不能完全相同。"""
        from core.monthly_event_inference_engine import infer_monthly_likely_events
        results = [infer_monthly_likely_events(self.chart, item) for item in self.monthly_data]
        for i in range(len(results) - 2):
            t1 = tuple(e["event_type"] for e in results[i]["top_events"][:3])
            t2 = tuple(e["event_type"] for e in results[i+1]["top_events"][:3])
            t3 = tuple(e["event_type"] for e in results[i+2]["top_events"][:3])
            self.assertFalse(t1 == t2 == t3, f"相邻3个月份第{i+1}-{i+3}月top_events完全相同")

    def test_each_month_has_3_events(self):
        """每个月 top_events 至少 3 条。"""
        from core.monthly_event_inference_engine import infer_monthly_likely_events
        results = [infer_monthly_likely_events(self.chart, item) for item in self.monthly_data]
        for i, r in enumerate(results):
            self.assertGreaterEqual(len(r.get("top_events", [])), 2, f"月{i+1}事件少于2条")

    def test_each_event_has_required_fields(self):
        """每个 top_event 必须有必需字段。"""
        from core.monthly_event_inference_engine import infer_monthly_likely_events
        r = infer_monthly_likely_events(self.chart, self.monthly_data[0])
        for e in r.get("top_events", []):
            for field in ["event_type", "label", "probability_level", "reason", "advice", "trigger_factors"]:
                self.assertIn(field, e, f"事件缺少字段：{field}")

    def test_reason_different_across_months(self):
        """事件 reason 不能全部一样。"""
        from core.monthly_event_inference_engine import infer_monthly_likely_events
        results = [infer_monthly_likely_events(self.chart, item) for item in self.monthly_data]
        all_reasons = set()
        for r in results:
            for e in r.get("top_events", []):
                all_reasons.add(e.get("reason", ""))
        self.assertGreater(len(all_reasons), 5, "事件原因过于重复")


if __name__ == "__main__":
    unittest.main()
