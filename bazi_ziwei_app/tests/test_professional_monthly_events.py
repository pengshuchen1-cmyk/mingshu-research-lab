import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class ProfessionalMonthlyEventTests(unittest.TestCase):
    def setUp(self):
        self.chart = {
            "day_master": "甲",
            "pillars": {
                "year": {"gan": "壬", "zhi": "子", "pillar": "壬子"},
                "month": {"gan": "丙", "zhi": "寅", "pillar": "丙寅"},
                "day": {"gan": "甲", "zhi": "午", "pillar": "甲午"},
                "hour": {"gan": "庚", "zhi": "申", "pillar": "庚申"},
            },
            "day_master_strength": {
                "strength": "偏弱",
                "favorable_elements": ["水", "木"],
                "unfavorable_elements": ["火", "金"],
            },
            "ten_god_counts": {
                "正财": 1,
                "偏财": 2,
                "正官": 1,
                "七杀": 1,
                "正印": 1,
                "偏印": 0,
                "比肩": 1,
                "劫财": 2,
                "食神": 1,
                "伤官": 1,
            },
            "five_elements": {"木": 8, "火": 5, "土": 3, "金": 4, "水": 6},
        }

    def test_monthly_events_include_real_life_objects_and_evidence(self):
        from core.monthly_event_inference_engine import infer_monthly_likely_events

        month = {
            "month": 7,
            "gan": "丙",
            "zhi": "午",
            "pillar": "丙午",
            "ten_god": "七杀",
            "branch_relations": [{"relation_type": "六冲", "target": "日支"}],
            "has_clash": True,
        }

        result = infer_monthly_likely_events(self.chart, month)
        events = result.get("top_events", [])
        combined = " ".join(
            " ".join(
                [
                    event.get("label", ""),
                    event.get("plain_summary", ""),
                    " ".join(event.get("real_world_signals", [])),
                    " ".join(event.get("trigger_factors", [])),
                ]
            )
            for event in events
        )

        object_words = ["车辆", "驾驶", "酒局", "饭局", "房子", "店铺", "回款", "项目进账", "身体"]
        self.assertTrue(any(word in combined for word in object_words), combined)
        for event in events[:3]:
            self.assertGreaterEqual(
                len(event.get("trigger_factors", [])),
                2,
                f"{event.get('event_type')} 缺少足够触发依据",
            )
            self.assertIn("plain_summary", event)
            self.assertIn("real_world_signals", event)

    def test_yearly_page_event_format_uses_plain_language(self):
        from ui.yearly_page import format_monthly_event_for_display

        text = format_monthly_event_for_display(
            {
                "event_type": "vehicle_safety",
                "label": "车辆驾驶提醒",
                "probability_level": "中等",
                "plain_summary": "本月更像是车辆、通勤或临时奔波被点亮。",
                "reason": "流月冲时支，又遇到七杀压力，现实中容易表现为赶路、开车、临时跑动增多。",
                "advice": "提前检查车况，少赶时间，重要行程留出缓冲。",
                "trigger_factors": ["流月冲时支", "七杀带来压力", "火为忌神"],
                "real_world_signals": ["车辆保养", "开车谨慎", "行程变动"],
                "source_titles": ["《三命通会》", "《命理探源》"],
            }
        )

        self.assertIn("一句话：本月更像是车辆、通勤或临时奔波被点亮。", text)
        self.assertIn("可能表现：车辆保养、开车谨慎、行程变动", text)
        self.assertNotIn("event_type", text)
        self.assertNotIn("{", text)

    def test_generic_yearly_page_phrases_removed(self):
        yearly_page = os.path.join(APP_DIR, "ui", "yearly_page.py")
        with open(yearly_page, "r", encoding="utf-8") as f:
            text = f.read()

        forbidden = [
            "出行、差旅或奔波较多，宜提前规划路线，避免赶时间。",
            "合同、审批、流程类事务较多，重要事项建议落到文字。",
            "关系信号积极，适合推进沟通或确认关系。",
            "健康状态容易受作息或情绪影响，建议关注身体信号。",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, text)


class HomePillarDisplayTests(unittest.TestCase):
    def test_home_has_compact_pillar_summary_helper(self):
        from ui.home import _compact_pillar_text

        chart = {
            "pillars": {
                "year": {"pillar": "甲子"},
                "month": {"pillar": "乙丑"},
                "day": {"pillar": "丙寅"},
                "hour": {"pillar": "丁卯"},
            }
        }

        self.assertEqual(_compact_pillar_text(chart), "甲子 · 乙丑 · 丙寅 · 丁卯")


if __name__ == "__main__":
    unittest.main()
