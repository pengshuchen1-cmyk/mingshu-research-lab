"""bazi-skill 对照落地测试。"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class BaziSkillIntegrationStepsTests(unittest.TestCase):
    """覆盖算法复核、早晚子时提示和调候解释。"""

    def test_late_zi_time_warning_is_user_visible(self):
        from core.calendar_engine import get_zi_time_boundary_note

        note = get_zi_time_boundary_note(23, 20)
        self.assertIn("子时", note)
        self.assertIn("换日", note)
        self.assertIn("统一", note)

    def test_normal_time_has_no_zi_warning(self):
        from core.calendar_engine import get_zi_time_boundary_note

        self.assertEqual(get_zi_time_boundary_note(10, 30), "")

    def test_chart_carries_zi_time_warning(self):
        from core.bazi_engine import build_bazi_chart

        chart = build_bazi_chart(
            {
                "name": "子时边界样例",
                "gender": "男",
                "birth_date": "1990-06-15",
                "birth_hour": 23,
                "birth_minute": 30,
                "birth_place": "北京",
            }
        )
        self.assertIn("zi_time_boundary_note", chart)
        self.assertIn("23:00", chart["zi_time_boundary_note"])
        self.assertIn("次日", chart["zi_time_boundary_note"])

    def test_strength_result_has_season_adjustment_explanation(self):
        from core.bazi_engine import build_bazi_chart

        chart = build_bazi_chart(
            {
                "name": "调候样例",
                "gender": "男",
                "birth_date": "1990-12-15",
                "birth_hour": 8,
                "birth_minute": 0,
                "birth_place": "北京",
            }
        )
        strength = chart.get("day_master_strength", {})
        self.assertIn("season_adjustment", strength)
        self.assertIn("plain_text", strength["season_adjustment"])
        self.assertTrue(strength["season_adjustment"]["plain_text"])

    def test_review_report_can_be_generated(self):
        from tools.bazi_skill_algorithm_review import build_bazi_skill_review_report

        review = build_bazi_skill_review_report(write_file=False)
        self.assertIn("立春", review)
        self.assertIn("早晚子时", review)
        self.assertIn("真太阳时", review)


if __name__ == "__main__":
    unittest.main()
