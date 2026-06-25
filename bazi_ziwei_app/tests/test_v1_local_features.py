import os
import sys
import tempfile
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def sample_profile() -> dict:
    return {
        "name": "测试用户",
        "gender": "男",
        "birth_date": "1990-01-01",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "上海",
        "use_solar_time": False,
        "note": "v1测试",
    }


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
        "ten_god_counts": {"比肩": 2, "食神": 1, "七杀": 1, "偏印": 1, "正财": 1},
        "day_master_strength": {
            "strength": "中和",
            "net_score": 1.0,
            "favorable_elements": ["木", "火"],
            "unfavorable_elements": ["金", "水"],
        },
    }


class V1LocalFeatureTests(unittest.TestCase):
    def test_app_navigation_contains_v1_pages(self):
        from app import get_pages

        pages = list(get_pages().keys())

        self.assertEqual(
            pages,
            [
                "首页",
                "新建命盘",
                "八字排盘",
                "五行十神",
                "日主喜忌",
                "大运流年",
                "年度运程",
                "专项报告",
                "紫微斗数",
                "报告导出",
                "命盘档案",
                "数据备份",
                "设置",
            ],
        )

    def test_special_reports_have_required_sections_and_disclaimer(self):
        from report.career_report import generate_career_report
        from report.love_report import generate_love_report
        from report.wealth_report import generate_wealth_report
        from report.export_report import DISCLAIMER

        reports = [
            generate_career_report(sample_chart()),
            generate_wealth_report(sample_chart()),
            generate_love_report(sample_chart(), sample_profile()),
        ]

        for report in reports:
            self.assertIn("title", report)
            self.assertIn("sections", report)
            self.assertIn("advice", report)
            self.assertEqual(report["disclaimer"], DISCLAIMER)
            self.assertGreaterEqual(len(report["sections"]), 8)

    def test_rule_engine_loads_and_matches_rules(self):
        from core.rule_engine import build_context_from_chart, load_rules, match_rules

        rules = load_rules("career_rules.json")
        context = build_context_from_chart(sample_chart())
        matched = match_rules(context, rules)

        self.assertIsInstance(rules, dict)
        self.assertGreater(len(rules.get("rules", [])), 0)
        self.assertGreater(len(matched), 0)
        for rule in rules["rules"]:
            for key in ["id", "title", "condition", "text", "advice"]:
                self.assertIn(key, rule)

    def test_report_quality_checks_forbidden_words_and_required_sections(self):
        from utils.report_quality import (
            check_forbidden_words,
            check_special_report_completeness,
            check_yearly_series_diversity,
        )

        forbidden = check_forbidden_words("这个判断绝对不适合作为报告。")
        self.assertFalse(forbidden["passed"])

        ok = check_special_report_completeness(
            {
                "title": "事业专项报告",
                "sections": [
                    {"title": "事业核心驱动力", "text": "适合稳步积累。"},
                    {"title": "适合工作模式", "text": "专业技术型。"},
                    {"title": "适合行业方向", "text": "教育、咨询。"},
                    {"title": "事业优势", "text": "学习力。"},
                    {"title": "事业风险", "text": "节奏压力。"},
                    {"title": "未来三年事业趋势", "text": "逐年观察。"},
                    {"title": "适合发力的年份", "text": "结合流年。"},
                    {"title": "行动建议", "text": "先做计划。"},
                ],
                "advice": "持续复盘。",
            },
            ["事业核心驱动力", "适合工作模式", "适合行业方向", "事业优势", "事业风险", "未来三年事业趋势", "行动建议"],
        )
        self.assertTrue(ok["passed"])

        bad_series = [{"brief_text": "同一句提示"} for _ in range(10)]
        self.assertFalse(check_yearly_series_diversity(bad_series)["passed"])

    def test_ziwei_basic_chart_and_report_do_not_forge_main_stars(self):
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        chart = build_ziwei_chart(sample_profile())
        report = generate_ziwei_report(chart)

        self.assertTrue(chart["available"])
        self.assertEqual(len(chart["palaces"]), 12)
        self.assertIn("命宫", [item["name"] for item in chart["palaces"]])
        self.assertIn("十四主星排布将在后续版本完善", chart["star_note"])
        self.assertIn("命宫分析", [item["title"] for item in report["sections"]])
        self.assertIn("综合建议", [item["title"] for item in report["sections"]])

    def test_backup_export_import_round_trip(self):
        from utils import database
        from utils.backup import export_profiles_to_json, import_profiles_from_json

        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "profiles.db")
            database.init_db()
            profile_id = database.save_profile(sample_profile(), sample_chart(), {"summary": "测试报告"})

            payload = export_profiles_to_json()
            self.assertIn("测试用户", payload)

            database.delete_profile(profile_id)
            self.assertEqual(database.list_profiles(), [])

            result = import_profiles_from_json(payload)
            self.assertEqual(result["imported"], 1)
            self.assertEqual(database.list_profiles()[0]["name"], "测试用户")

    def test_page_modules_import_without_streamlit_side_effects(self):
        modules = [
            "ui.home",
            "ui.profile_form",
            "ui.bazi_page",
            "ui.five_element_page",
            "ui.useful_god_page",
            "ui.luck_page",
            "ui.yearly_page",
            "ui.special_reports_page",
            "ui.ziwei_page",
            "ui.report_page",
            "ui.archive_page",
            "ui.backup_page",
            "ui.settings_page",
        ]

        for module_name in modules:
            __import__(module_name)


if __name__ == "__main__":
    unittest.main()
