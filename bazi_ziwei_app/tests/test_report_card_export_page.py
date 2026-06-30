import unittest


class ReportCardExportPageTests(unittest.TestCase):
    def test_markdown_sections_become_preview_cards(self):
        from ui.report_page import _build_report_preview_cards

        markdown = "\n".join(
            [
                "# 命数研究室 - 命盘综合报告",
                "",
                "## 一、基础信息",
                "- 姓名：测试",
                "",
                "## 二、年度运程",
                "- 事业：适合稳步推进",
                "- 财运：注意现金流",
            ]
        )
        cards = _build_report_preview_cards(markdown)

        self.assertGreaterEqual(len(cards), 2)
        self.assertEqual(cards[0]["title"], "一、基础信息")
        self.assertIn("姓名：测试", cards[0]["content"])
        self.assertEqual(cards[1]["title"], "二、年度运程")
        self.assertIn("现金流", cards[1]["content"])

    def test_report_page_contains_card_navigation_controls(self):
        with open("ui/report_page.py", "r", encoding="utf-8") as file:
            text = file.read()

        self.assertIn("报告名片预览", text)
        self.assertIn("上一张", text)
        self.assertIn("下一张", text)
        self.assertIn("report_card_index", text)


if __name__ == "__main__":
    unittest.main()
