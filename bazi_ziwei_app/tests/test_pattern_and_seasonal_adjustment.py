import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class PatternAndSeasonalAdjustmentTests(unittest.TestCase):
    def _chart(self, day_master="甲", month_gan="丙", month_zhi="寅"):
        return {
            "day_master": day_master,
            "pillars": {
                "year": {"gan": "癸", "zhi": "亥", "pillar": "癸亥"},
                "month": {"gan": month_gan, "zhi": month_zhi, "pillar": f"{month_gan}{month_zhi}"},
                "day": {"gan": day_master, "zhi": "子", "pillar": f"{day_master}子"},
                "hour": {"gan": "戊", "zhi": "辰", "pillar": "戊辰"},
            },
            "ten_god_counts": {"食神": 1, "偏印": 1, "偏财": 1},
            "day_master_strength": {
                "strength": "身强",
                "favorable_elements": ["火", "土", "金"],
                "unfavorable_elements": ["水", "木"],
            },
        }

    def test_seasonal_adjustment_uses_ten_stems_twelve_months_table(self):
        from core.seasonal_adjustment import analyze_seasonal_adjustment

        result = analyze_seasonal_adjustment(self._chart("甲", "丙", "寅"))

        self.assertEqual(result["day_master"], "甲")
        self.assertEqual(result["month_branch"], "寅")
        self.assertEqual(result["month_name"], "寅月")
        self.assertIn("丙", result["primary_useful_stems"])
        self.assertIn("癸", result["supporting_stems"])
        self.assertIn("初春", result["plain_text"])
        self.assertIn("调候", result["basis"])

    def test_pattern_analysis_detects_month_command_pattern_and_quality(self):
        from core.pattern_engine import analyze_pattern

        result = analyze_pattern(self._chart("甲", "丙", "寅"))

        self.assertEqual(result["pattern"], "食神格")
        self.assertEqual(result["month_command_ten_god"], "比肩")
        self.assertIn("丙", result["exposed_stems"])
        self.assertIn(result["quality"], ["成中有待", "较成", "需经营", "格局未明"])
        self.assertTrue(result["plain_text"])
        self.assertTrue(result["evidence"])

    def test_bazi_chart_contains_pattern_and_seasonal_adjustment(self):
        from core.bazi_engine import build_bazi_chart

        chart = build_bazi_chart({
            "name": "测试",
            "gender": "男",
            "birth_date": "1999-07-01",
            "birth_hour": 10,
            "birth_minute": 0,
        })

        self.assertNotIn("error", chart)
        self.assertIn("pattern_analysis", chart)
        self.assertIn("seasonal_adjustment", chart)
        self.assertIn("pattern", chart["pattern_analysis"])
        self.assertIn("plain_text", chart["seasonal_adjustment"])


if __name__ == "__main__":
    unittest.main()
