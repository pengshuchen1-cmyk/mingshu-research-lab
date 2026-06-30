"""紫微斗数白话说明书测试。"""

from __future__ import annotations

import json
import unittest


FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


def sample_profile() -> dict:
    return {
        "name": "紫微测试",
        "gender": "男",
        "birth_date": "1996-08-18",
        "birth_hour": 14,
        "birth_minute": 20,
        "birth_place": "上海",
    }


class ZiweiPlainGuideTests(unittest.TestCase):
    """普通用户可读说明书。"""

    def test_plain_guide_has_five_user_facing_cards(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_readable_engine import build_ziwei_plain_guide

        guide = build_ziwei_plain_guide(build_ziwei_chart(sample_profile()))
        titles = [item["title"] for item in guide["focus_cards"]]

        for title in ["命宫说明", "身宫说明", "事业宫说明", "财帛宫说明", "夫妻宫说明"]:
            self.assertIn(title, titles)

    def test_each_card_explains_meaning_reality_attention_and_stars(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_readable_engine import build_ziwei_plain_guide

        guide = build_ziwei_plain_guide(build_ziwei_chart(sample_profile()))
        for card in guide["focus_cards"]:
            self.assertIn("what_it_means", card)
            self.assertIn("real_world_view", card)
            self.assertIn("what_to_notice", card)
            self.assertIn("one_sentence", card)
            self.assertIn("life_examples", card)
            self.assertIn("action_advice", card)
            self.assertIn("boundary_note", card)
            self.assertIn("star_combination_text", card)
            self.assertGreater(len(card["what_it_means"]), 10)
            self.assertGreater(len(card["real_world_view"]), 10)
            self.assertGreater(len(card["what_to_notice"]), 10)
            self.assertGreater(len(card["one_sentence"]), 10)
            self.assertGreaterEqual(len(card["life_examples"]), 2)
            self.assertGreater(len(card["action_advice"]), 10)
            self.assertIn("参考", card["boundary_note"])

    def test_capability_review_separates_ready_cautious_and_pending_items(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_readable_engine import build_ziwei_capability_review

        review = build_ziwei_capability_review(build_ziwei_chart(sample_profile()))
        names = [item["name"] for item in review["items"]]
        statuses = {item["name"]: item["status"] for item in review["items"]}

        self.assertIn("命宫与身宫", names)
        self.assertIn("十四主星落宫", names)
        self.assertIn("飞化", names)
        self.assertIn("紫微流年流月", names)
        self.assertEqual(statuses["飞化"], "未接入")
        self.assertEqual(statuses["紫微流年流月"], "未接入")
        self.assertIn("不会把未接入内容包装成结论", review["boundary"])

    def test_plain_guide_has_star_combination_section_and_no_forbidden_words(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_readable_engine import build_ziwei_plain_guide

        guide = build_ziwei_plain_guide(build_ziwei_chart(sample_profile()))
        text = json.dumps(guide, ensure_ascii=False)

        self.assertIn("星曜组合", text)
        self.assertIn("当前组合怎么看", text)
        for word in FORBIDDEN:
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
