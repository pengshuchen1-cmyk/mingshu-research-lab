"""合婚匹配测试 — v1.3-A"""

from __future__ import annotations

import unittest

from core.compatibility import (
    analyze_compatibility,
    _analyze_heavenly_stems,
    _analyze_nayin,
    _analyze_favorable_complement,
    _analyze_daxian_sync,
)


class TestCompatibilityEnhancements(unittest.TestCase):

    def setUp(self):
        self.chart1 = {
            "day_master": "甲",
            "pillars": {
                "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
                "month": {"gan": "丙", "zhi": "寅"},
                "day": {"gan": "甲", "zhi": "午"},
                "hour": {"gan": "庚", "zhi": "申"},
            },
            "day_master_strength": {"favorable_elements": ["水", "木"], "unfavorable_elements": ["火", "金"]},
            "five_elements": {"木": 8, "火": 5, "土": 3, "金": 4, "水": 6},
            "ten_god_counts": {"正财": 1, "偏财": 2, "正官": 1, "比肩": 1, "劫财": 1, "食神": 1},
        }
        self.chart2 = {
            "day_master": "庚",
            "pillars": {
                "year": {"gan": "己", "zhi": "卯", "pillar": "己卯"},
                "month": {"gan": "癸", "zhi": "未"},
                "day": {"gan": "庚", "zhi": "寅"},
                "hour": {"gan": "丙", "zhi": "子"},
            },
            "day_master_strength": {"favorable_elements": ["土", "金"], "unfavorable_elements": ["木", "火"]},
            "five_elements": {"木": 4, "火": 3, "土": 8, "金": 7, "水": 2},
            "ten_god_counts": {"正财": 1, "偏财": 1, "正官": 1, "七杀": 1, "正印": 2, "偏印": 1, "比肩": 1, "劫财": 1, "食神": 1},
        }

    def test_analyze_returns_result(self):
        """analyze_compatibility 返回完整结构。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        self.assertIn("overall_score", r)
        self.assertIn("dimensions", r)
        self.assertIn("summary", r)
        self.assertIn("level", r)
        self.assertIn("key_cautions", r)
        self.assertIn("source_ids", r)
        self.assertIn("basis", r)

    def test_heavenly_stems_analysis(self):
        """天干五合返回合理分数。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        dims = {d["label"]: d for d in r["dimensions"]}
        if "天干五合" in dims:
            self.assertGreaterEqual(dims["天干五合"]["score"], 0)
            self.assertLessEqual(dims["天干五合"]["score"], 10)

    def test_nayin_analysis(self):
        """纳音配对返回合理分数。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        dims = {d["label"]: d for d in r["dimensions"]}
        if "纳音配对" in dims:
            self.assertGreaterEqual(dims["纳音配对"]["score"], 0)
            self.assertLessEqual(dims["纳音配对"]["score"], 8)

    def test_favorable_complement(self):
        """喜用神互补返回合理分数。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        dims = {d["label"]: d for d in r["dimensions"]}
        if "喜用神互补" in dims:
            self.assertGreaterEqual(dims["喜用神互补"]["score"], 0)
            self.assertLessEqual(dims["喜用神互补"]["score"], 10)

    def test_daxian_sync(self):
        """大运同步性不崩溃。"""
        r = analyze_compatibility(self.chart1, self.chart2, {}, {})
        dims = {d["label"]: d for d in r["dimensions"]}
        if "大运同步性" in dims:
            self.assertGreaterEqual(dims["大运同步性"]["score"], 0)
            self.assertLessEqual(dims["大运同步性"]["score"], 6)

    def test_hour_branch(self):
        """时支关系维度存在。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        labels = [d["label"] for d in r["dimensions"]]
        self.assertIn("时支关系", labels)

    def test_total_score_range(self):
        """总分在 0-100 之间。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        self.assertGreaterEqual(r["overall_score"], 0)
        self.assertLessEqual(r["overall_score"], 100)

    def test_11_dimensions(self):
        """增强版有 11 个维度。"""
        r = analyze_compatibility(self.chart1, self.chart2)
        self.assertEqual(len(r["dimensions"]), 11)

    def test_no_absolute_words(self):
        """结果中不含禁用词。"""
        forbidden = ["必定", "绝对", "注定", "一定离婚", "必有灾", "必有大病", "短命"]
        r = analyze_compatibility(self.chart1, self.chart2)
        text = str(r)
        for w in forbidden:
            self.assertNotIn(w, text, f"包含禁用词：{w}")

    def test_different_charts_different_results(self):
        """不同命盘组合的评分不完全相同。"""
        chart3 = dict(self.chart2)
        chart3["day_master"] = "丙"
        r1 = analyze_compatibility(self.chart1, self.chart2)
        r2 = analyze_compatibility(self.chart1, chart3)
        self.assertNotEqual(r1["overall_score"], r2["overall_score"],
                            "不同命盘组合评分不应相同")


if __name__ == "__main__":
    unittest.main()
