"""紫微星曜组合规则测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


class ZiweiStarCombinationTests(unittest.TestCase):
    """星曜组合从单星解释升级为组合规则。"""

    def test_rules_include_required_example_combinations(self) -> None:
        path = PROJECT_ROOT / "rules" / "ziwei_star_combinations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = {tuple(rule["stars"]) for rule in data["rules"]}

        self.assertIn(("紫微", "天府"), pairs)
        self.assertIn(("武曲", "七杀"), pairs)
        self.assertIn(("太阳", "太阴"), pairs)
        self.assertIn(("天同", "太阴"), pairs)
        self.assertIn(("天机", "天梁"), pairs)
        self.assertIn(("破军", "七杀"), pairs)
        self.assertIn(("天相", "天府"), pairs)

    def test_each_rule_has_reality_strength_risk_and_advice(self) -> None:
        path = PROJECT_ROOT / "rules" / "ziwei_star_combinations.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for rule in data["rules"]:
            for key in ["id", "title", "stars", "plain_meaning", "real_world_view", "strengths", "risks", "advice", "source_ids"]:
                self.assertIn(key, rule)
            for key in ["suitable_palaces", "reality_examples", "trigger_signals", "boundary"]:
                self.assertIn(key, rule)
            self.assertGreaterEqual(len(rule["strengths"]), 2)
            self.assertGreaterEqual(len(rule["risks"]), 2)
            self.assertGreaterEqual(len(rule["reality_examples"]), 2)
            self.assertGreaterEqual(len(rule["trigger_signals"]), 2)
            self.assertGreater(len(rule["advice"]), 10)

    def test_match_same_palace_combination(self) -> None:
        from core.ziwei_star_combination_engine import match_star_combinations

        matches = match_star_combinations(["武曲", "七杀"], palace_name="官禄宫")
        self.assertTrue(matches)
        self.assertEqual(matches[0]["id"], "wuqu_qisha")
        self.assertIn("执行", matches[0]["real_world_view"])
        self.assertIn("官禄宫", matches[0]["palace_interpretation"])

    def test_plain_guide_uses_combination_rule_when_available(self) -> None:
        from core.ziwei_readable_engine import build_ziwei_plain_guide

        chart = {
            "available": True,
            "life_palace": "子",
            "body_palace": "午",
            "lunar_month": 6,
            "lunar_day": 12,
            "hour_branch": "未",
            "main_stars_ready": True,
            "main_stars_by_palace": {"官禄宫": ["武曲", "七杀"]},
            "palaces": [
                {"name": "命宫", "branch": "子", "is_body_palace": False, "main_stars": []},
                {"name": "官禄宫", "branch": "申", "is_body_palace": False, "main_stars": ["武曲", "七杀"]},
                {"name": "财帛宫", "branch": "辰", "is_body_palace": False, "main_stars": []},
                {"name": "夫妻宫", "branch": "戌", "is_body_palace": False, "main_stars": []},
                {"name": "迁移宫", "branch": "寅", "is_body_palace": False, "main_stars": []},
                {"name": "福德宫", "branch": "巳", "is_body_palace": False, "main_stars": []},
                {"name": "疾厄宫", "branch": "酉", "is_body_palace": False, "main_stars": []},
                {"name": "田宅宫", "branch": "丑", "is_body_palace": False, "main_stars": []},
                {"name": "兄弟宫", "branch": "卯", "is_body_palace": False, "main_stars": []},
                {"name": "子女宫", "branch": "未", "is_body_palace": False, "main_stars": []},
                {"name": "交友宫", "branch": "亥", "is_body_palace": False, "main_stars": []},
                {"name": "父母宫", "branch": "午", "is_body_palace": True, "main_stars": []},
            ],
        }

        guide = build_ziwei_plain_guide(chart)
        career_card = next(card for card in guide["focus_cards"] if card["title"] == "事业宫说明")

        self.assertIn("武曲七杀", career_card["star_combination_text"])
        self.assertIn("现实表现", career_card["star_combination_text"])
        for word in FORBIDDEN:
            self.assertNotIn(word, career_card["star_combination_text"])


if __name__ == "__main__":
    unittest.main()
