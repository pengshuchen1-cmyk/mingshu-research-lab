"""紫微主星落宫解释测试。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


class ZiweiStarPalaceExplanationTests(unittest.TestCase):
    """解释已落宫主星，不新增不确定算法。"""

    def test_rule_file_has_key_star_palace_cases(self) -> None:
        path = PROJECT_ROOT / "rules" / "ziwei_star_palace_rules.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = {(rule["condition"]["star"], rule["condition"]["palace"]) for rule in data["rules"]}

        self.assertIn(("紫微", "命宫"), pairs)
        self.assertIn(("武曲", "财帛宫"), pairs)
        self.assertIn(("七杀", "官禄宫"), pairs)
        self.assertIn(("太阳", "官禄宫"), pairs)
        self.assertIn(("太阴", "夫妻宫"), pairs)

    def test_each_rule_has_plain_fields_and_no_forbidden_words(self) -> None:
        path = PROJECT_ROOT / "rules" / "ziwei_star_palace_rules.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(data, ensure_ascii=False)

        for rule in data["rules"]:
            for key in [
                "id", "title", "condition", "text", "real_world_view",
                "strengths", "risks", "advice", "boundary", "source_ids",
            ]:
                self.assertIn(key, rule)
            self.assertIn("star", rule["condition"])
            self.assertIn("palace", rule["condition"])
            self.assertGreaterEqual(len(rule["strengths"]), 2)
            self.assertGreaterEqual(len(rule["risks"]), 2)
            self.assertGreater(len(rule["real_world_view"]), 10)
            self.assertGreater(len(rule["boundary"]), 10)

        for word in FORBIDDEN:
            self.assertNotIn(word, text)

    def test_explain_star_in_palace_uses_specific_rule(self) -> None:
        from core.ziwei_star_palace_engine import explain_star_in_palace

        result = explain_star_in_palace("武曲", "财帛宫", sihua=["化禄"])

        self.assertEqual(result["star"], "武曲")
        self.assertEqual(result["palace"], "财帛宫")
        self.assertTrue(result["matched_rule"])
        self.assertIn("钱", result["plain_text"])
        self.assertIn("化禄", result["sihua_text"])
        self.assertIn("参考", result["boundary"])

    def test_build_chart_star_palace_explanations_returns_focus_palaces(self) -> None:
        from core.ziwei_star_palace_engine import build_star_palace_explanations

        chart = {
            "available": True,
            "main_stars_by_palace": {
                "命宫": ["紫微"],
                "财帛宫": ["武曲"],
                "官禄宫": ["七杀"],
                "夫妻宫": ["太阴"],
            },
        }
        result = build_star_palace_explanations(chart, sihua_by_palace={"财帛宫": ["化禄"]})

        self.assertIn("命宫", result)
        self.assertIn("财帛宫", result)
        self.assertGreaterEqual(len(result["财帛宫"]), 1)
        self.assertIn("plain_text", result["财帛宫"][0])

    def test_plain_guide_contains_star_palace_explanations(self) -> None:
        from core.ziwei_readable_engine import build_ziwei_plain_guide

        chart = {
            "available": True,
            "life_palace": "子",
            "body_palace": "午",
            "lunar_month": 6,
            "lunar_day": 12,
            "hour_branch": "未",
            "main_stars_ready": True,
            "main_stars_by_palace": {"财帛宫": ["武曲"]},
            "palaces": [
                {"name": "命宫", "branch": "子", "is_body_palace": False, "main_stars": []},
                {"name": "官禄宫", "branch": "申", "is_body_palace": False, "main_stars": []},
                {"name": "财帛宫", "branch": "辰", "is_body_palace": False, "main_stars": ["武曲"]},
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
        wealth_card = next(card for card in guide["focus_cards"] if card["title"] == "财帛宫说明")

        self.assertIn("star_palace_explanations", wealth_card)
        self.assertIn("武曲", wealth_card["star_palace_explanations"][0]["star"])
        self.assertIn("财帛宫", wealth_card["star_palace_explanations"][0]["palace"])


if __name__ == "__main__":
    unittest.main()
