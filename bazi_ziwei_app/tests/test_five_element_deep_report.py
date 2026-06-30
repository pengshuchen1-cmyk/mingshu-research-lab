"""测试五行深度报告 — v1.2-F"""

from __future__ import annotations

import unittest

from report.five_element_deep_report import (
    generate_five_element_deep_report,
    ELEMENT_DEEP_DETAILS,
    FIVE_ELEMENT_ORDER,
)


class TestFiveElementDeepReport(unittest.TestCase):

    def setUp(self):
        self.chart = {
            "five_elements": {"木": 8.0, "火": 5.0, "土": 3.0, "金": 4.0, "水": 6.0},
            "day_master_strength": {
                "strength": "中等",
                "net_score": 0,
                "favorable_elements": ["水", "木"],
                "unfavorable_elements": ["火", "金"],
            },
        }

    def test_report_contains_element_details(self):
        """五行深度报告必须包含五个 element_details。"""
        report = generate_five_element_deep_report(self.chart)
        details = report.get("element_details", {})
        self.assertEqual(len(details), 5, "必须有5个五行详情")

    def test_element_detail_has_all_fields(self):
        """每个五行必须包含所有必需字段。"""
        required_fields = [
            "element", "score", "level", "is_favorable", "is_unfavorable",
            "basic_meaning", "in_this_chart",
            "career_meaning", "wealth_meaning", "relationship_meaning",
            "health_tendency", "when_too_strong", "when_too_weak",
            "if_favorable", "if_unfavorable", "real_life_advice",
        ]
        report = generate_five_element_deep_report(self.chart)
        details = report.get("element_details", {})
        for element in FIVE_ELEMENT_ORDER:
            detail = details.get(element, {})
            for field in required_fields:
                self.assertIn(field, detail, f"{element} 缺少字段：{field}")

    def test_element_meaning_not_empty(self):
        """五行解释不能过短。"""
        report = generate_five_element_deep_report(self.chart)
        details = report.get("element_details", {})
        for element in FIVE_ELEMENT_ORDER:
            detail = details.get(element, {})
            for field in ["career_meaning", "wealth_meaning", "relationship_meaning",
                          "health_tendency", "when_too_strong", "when_too_weak"]:
                text = detail.get(field, "")
                self.assertGreater(len(text), 5, f"{element} 的 {field} 过短：{text}")

    def test_real_life_advice_is_list(self):
        """real_life_advice 必须是列表且有内容。"""
        report = generate_five_element_deep_report(self.chart)
        details = report.get("element_details", {})
        for element in FIVE_ELEMENT_ORDER:
            advice = details.get(element, {}).get("real_life_advice", [])
            self.assertIsInstance(advice, list, f"{element} advice 不是列表")
            self.assertGreater(len(advice), 0, f"{element} advice 为空")

    def test_has_overview(self):
        """报告必须包含 element_overview。"""
        report = generate_five_element_deep_report(self.chart)
        self.assertIn("element_overview", report)
        self.assertGreater(len(report["element_overview"]), 5)

    def test_has_balance_summary(self):
        """报告必须包含 element_balance_summary。"""
        report = generate_five_element_deep_report(self.chart)
        self.assertIn("element_balance_summary", report)
        self.assertGreater(len(report["element_balance_summary"]), 5)

    def test_has_strong_weak_elements(self):
        """报告必须包含 strong_elements 和 weak_elements。"""
        report = generate_five_element_deep_report(self.chart)
        self.assertIn("strong_elements", report)
        self.assertIn("weak_elements", report)

    def test_has_implications(self):
        """报告必须包含 career/wealth/relationship/health implications。"""
        report = generate_five_element_deep_report(self.chart)
        for field in ["career_implications", "wealth_implications",
                      "relationship_implications", "health_implications"]:
            self.assertIn(field, report, f"缺少字段：{field}")

    def test_has_adjustment_advice(self):
        """报告必须包含 adjustment_advice。"""
        report = generate_five_element_deep_report(self.chart)
        advice = report.get("adjustment_advice", [])
        self.assertGreater(len(advice), 0, "调整建议不能为空")

    def test_has_source_ids(self):
        """报告必须包含 source_ids 和 source_titles。"""
        report = generate_five_element_deep_report(self.chart)
        self.assertIn("source_ids", report)
        self.assertIn("source_titles", report)

    def test_no_absolute_words(self):
        """不得出现禁用词。"""
        forbidden = ["一定买房", "一定发财", "必定破财", "必有车祸",
                     "必有灾", "必定离婚", "必有大病", "短命", "注定"]
        report = generate_five_element_deep_report(self.chart)
        text = str(report)
        for word in forbidden:
            self.assertNotIn(word, text, f"包含禁用词：{word}")

    def test_empty_chart_handling(self):
        """空命盘也能正确处理。"""
        report = generate_five_element_deep_report({})
        self.assertEqual(len(report.get("element_details", {})), 0)

    def test_all_elements_in_every_detail(self):
        """所有五行在 ELEMENT_DEEP_DETAILS 中都有定义。"""
        for element in FIVE_ELEMENT_ORDER:
            self.assertIn(element, ELEMENT_DEEP_DETAILS,
                          f"ELEMENT_DEEP_DETAILS 缺少 {element}")


if __name__ == "__main__":
    unittest.main()
