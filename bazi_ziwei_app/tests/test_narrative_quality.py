import os
import re
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


FORBIDDEN_WORDS = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


def sample_chart() -> dict:
    return {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
            "month": {"gan": "丙", "zhi": "寅", "pillar": "丙寅"},
            "day": {"gan": "甲", "zhi": "午", "pillar": "甲午"},
            "hour": {"gan": "庚", "zhi": "申", "pillar": "庚申"},
        },
        "five_elements": {"木": 3.0, "火": 2.0, "土": 1.0, "金": 2.0, "水": 1.0},
        "ten_god_counts": {"比肩": 2, "食神": 1, "七杀": 1, "偏财": 1, "正印": 1},
        "day_master_strength": {
            "strength": "中和",
            "net_score": 1.0,
            "favorable_elements": ["木", "火"],
            "unfavorable_elements": ["金", "水"],
        },
    }


def sample_profile() -> dict:
    return {
        "name": "测试用户",
        "gender": "男",
        "birth_date": "1990-01-01",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "上海",
        "use_solar_time": False,
    }


def sample_report() -> dict:
    return {
        "summary": "基础总结",
        "five_element_text": "五行结构可作为观察参考。",
        "ten_god_text": "十神结构可作为行为模式参考。",
        "strength_text": "日主承接力较平衡。",
        "favorable_text": "喜用五行可作为选择方向参考。",
        "personality_text": "性格倾向重视成长和自主。",
        "career_text": "事业适合长期积累能力。",
        "wealth_text": "财务适合稳健规划。",
        "love_text": "关系适合保持沟通。",
        "risk_text": "风险上注意节奏。",
        "advice": "建议结合现实反馈复盘。",
    }


class NarrativeQualityTests(unittest.TestCase):
    def test_luck_age_range_never_uses_negative_age(self):
        from core.luck_engine import _normalize_age_range

        start_age, end_age, _warning = _normalize_age_range(-2, 11, 2, 0)

        self.assertEqual(start_age, 2)
        self.assertEqual(end_age, 11)

    def test_luck_stage_narratives_change_by_ten_god_and_elements(self):
        from report.narrative_engine import build_luck_stage_narrative

        chart = sample_chart()
        items = [
            {"pillar": "甲子", "gan": "甲", "zhi": "子", "gan_element": "木", "zhi_element": "水", "ten_god": "比肩"},
            {"pillar": "丙寅", "gan": "丙", "zhi": "寅", "gan_element": "火", "zhi_element": "木", "ten_god": "食神"},
            {"pillar": "戊辰", "gan": "戊", "zhi": "辰", "gan_element": "土", "zhi_element": "土", "ten_god": "偏财"},
        ]

        texts = [build_luck_stage_narrative(chart, item) for item in items]

        self.assertEqual(len(set(texts)), len(texts))
        self.assertTrue(all("事业" in text and "财" in text and "关系" in text for text in texts))

    def test_yearly_and_monthly_narratives_are_not_all_same(self):
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune

        chart = sample_chart()
        yearly_texts = [analyze_yearly_fortune(chart, year)["overall_text"] for year in range(2026, 2036)]
        monthly_items = analyze_monthly_fortune(chart, 2026)

        self.assertGreater(len(set(yearly_texts)), 6)
        self.assertGreater(len(set(item["theme"] for item in monthly_items)), 6)
        self.assertTrue(all("event_tendency" in item for item in monthly_items))

    def test_export_report_uses_comprehensive_structure_and_limits_repetition(self):
        from core.monthly_engine import analyze_monthly_fortune
        from core.yearly_engine import analyze_yearly_fortune
        from report.export_report import build_markdown_report

        chart = sample_chart()
        yearly_data = analyze_yearly_fortune(chart, 2026)
        monthly_data = analyze_monthly_fortune(chart, 2026)
        luck_data = {
            "available": True,
            "start_text": "起运时间为传统命理推算结果，具体起运点可在后续版本结合节气进一步校正。",
            "dayun_list": [
                {
                    "start_age": 2,
                    "end_age": 11,
                    "start_year": 1992,
                    "end_year": 2001,
                    "pillar": "甲子",
                    "gan": "甲",
                    "zhi": "子",
                    "gan_element": "木",
                    "zhi_element": "水",
                    "ten_god": "比肩",
                },
                {
                    "start_age": 12,
                    "end_age": 21,
                    "start_year": 2002,
                    "end_year": 2011,
                    "pillar": "丙寅",
                    "gan": "丙",
                    "zhi": "寅",
                    "gan_element": "火",
                    "zhi_element": "木",
                    "ten_god": "食神",
                },
            ],
            "yearly_list": [analyze_yearly_fortune(chart, year) for year in range(2026, 2036)],
        }

        markdown = build_markdown_report(sample_profile(), chart, sample_report(), luck_data, yearly_data, monthly_data)

        for heading in [
            "命盘综合报告",
            "五行结构分析",
            "十神结构分析",
            "日主强弱与喜忌",
            "基础性格与行为模式",
            "事业方向分析",
            "财运模式分析",
            "感情关系分析",
            "大运阶段分析",
            "未来十年流年趋势",
            "年度运程详情",
            "十二个月流月趋势",
            "综合行动建议",
        ]:
            self.assertIn(heading, markdown)

        sentences = [item.strip() for item in re.split(r"[。\n]", markdown) if item.strip()]
        for sentence in set(sentences):
            self.assertLessEqual(sentences.count(sentence), 3, sentence)
        for forbidden in FORBIDDEN_WORDS:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
