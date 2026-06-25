import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class ExportReportTests(unittest.TestCase):
    def test_markdown_report_contains_required_sections(self):
        from report.export_report import build_markdown_report, build_pdf_report

        profile = {
            "name": "测试用户",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
        }
        chart = {
            "day_master": "丙",
            "pillars": {
                "year": {"pillar": "己巳"},
                "month": {"pillar": "丙子"},
                "day": {"pillar": "丙寅"},
                "hour": {"pillar": "癸巳"},
            },
            "five_elements": {"木": 2.5, "火": 3.0, "土": 1.0, "金": 0.5, "水": 2.0},
            "ten_god_counts": {"比肩": 2, "正财": 1},
            "day_master_strength": {
                "strength": "中和",
                "net_score": 1.0,
                "favorable_elements": [],
                "unfavorable_elements": [],
            },
        }
        report = {
            "summary": "基础总结",
            "personality_text": "性格倾向",
            "career_text": "事业倾向",
            "wealth_text": "财富倾向",
            "love_text": "关系倾向",
            "risk_text": "风险提醒",
            "advice": "行动建议",
        }

        markdown = build_markdown_report(profile, chart, report)
        pdf_bytes = build_pdf_report(profile, chart, report)

        self.assertIsInstance(markdown, str)
        self.assertIn("命数研究室", markdown)
        self.assertIn("八字排盘", markdown)
        self.assertIn("免责声明", markdown)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)

    def test_pdf_report_embeds_renderable_chinese_font_when_available(self):
        from report.export_report import build_pdf_report

        profile = {
            "name": "中文测试",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
        }
        chart = {
            "day_master": "甲",
            "pillars": {
                "year": {"pillar": "甲子"},
                "month": {"pillar": "丙寅"},
                "day": {"pillar": "甲午"},
                "hour": {"pillar": "庚申"},
            },
            "five_elements": {"木": 3.0, "火": 2.0, "土": 1.0, "金": 2.0, "水": 1.0},
            "ten_god_counts": {"比肩": 2, "食神": 1},
            "day_master_strength": {"strength": "中和", "net_score": 1.0},
        }
        report = {"summary": "中文报告", "career_text": "事业建议", "wealth_text": "财务建议", "love_text": "关系建议", "risk_text": "风险提醒", "advice": "行动建议"}

        pdf_bytes = build_pdf_report(profile, chart, report)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertTrue(b"/FontFile" in pdf_bytes or b"ArialUnicode" in pdf_bytes)


if __name__ == "__main__":
    unittest.main()
