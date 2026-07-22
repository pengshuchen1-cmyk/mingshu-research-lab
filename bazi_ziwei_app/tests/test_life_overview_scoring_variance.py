"""v1.0.4 命盘评分差异化测试。"""

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


class LifeOverviewScoringVarianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.bazi_engine import build_bazi_chart
        from core.life_overview_engine import analyze_life_overview

        cls.results = [analyze_life_overview(build_bazi_chart(profile)) for profile in PROFILES]

    def test_score_details_exist(self):
        for item in self.results:
            details = item.get("score_details", {})
            for key in ["wealth", "romance", "health_stability", "career", "learning_growth", "social_resources", "risk_control", "overall_pace"]:
                self.assertIn(key, details)
                self.assertIn("sub_scores", details[key])
                self.assertIn("evidence", details[key])
                self.assertIn("advice", details[key])

    def test_core_scores_have_visible_spread(self):
        for key in ["wealth", "romance", "health_stability", "career", "overall_balance"]:
            values = [item["scores"][key] for item in self.results]
            self.assertGreaterEqual(max(values) - min(values), 18, f"{key} 评分差异不足：{values}")

    def test_romance_score_and_copy_share_the_same_relationship_facts(self):
        for item in self.results:
            romance = item["romance_overview"]
            signature = romance["relationship_signature"]
            detail = item["score_details"]["romance"]
            self.assertEqual(
                detail["sub_scores"]["spouse_star_visibility"],
                min(24, signature["spouse_star"]["total"] * 8),
            )
            self.assertEqual(
                detail["sub_scores"]["peach_blossom_signal"],
                min(18, signature["peach_blossom"]["count"] * 8),
            )
            self.assertIn(romance["core_portrait"], romance["romance_summary"])
            self.assertIn(romance["primary_relationship_focus"], romance["romance_summary"])


if __name__ == "__main__":
    unittest.main()
