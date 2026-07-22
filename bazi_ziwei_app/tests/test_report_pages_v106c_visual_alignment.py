import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportPagesV106CVisualAlignmentTests(unittest.TestCase):
    def test_yearly_special_and_export_pages_use_homepage_visual_language(self):
        expected = {
            "yearly_page.py": ["ms3-year-cover", "ms3-year-metrics", "ms3-month-card", "ms3-month-tag"],
            "special_reports_page.py": ["v106c-page-hero", "mingshu-report-card", "mingshu-report-body"],
            "report_page.py": [
                "v106c-page-hero",
                "mingshu-report-card",
                "mingshu-report-body",
                "报告摘要",
                "下一步建议",
                "var(--ms-surface)",
            ],
        }
        for filename, tokens in expected.items():
            text = (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text, f"{filename} 缺少 {token}")

    def test_three_report_pages_do_not_emit_old_light_inline_cards(self):
        combined = "\n".join(
            (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for filename in ["yearly_page.py", "special_reports_page.py", "report_page.py"]
        )
        forbidden = [
            "background:#FAF7F4",
            "background:#EDE6DC",
            "color:#3D2B1A",
            "color:#5C4A32",
            "color:#8C7A64",
            "border:1px solid #EDE6DC",
            "border-top:1px solid #EDE6DC",
        ]
        for snippet in forbidden:
            self.assertNotIn(snippet, combined)

    def test_global_css_keeps_expanders_and_report_cards_readable(self):
        text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        for token in [
            ".ms-mini-metric",
            ".ms-month-card",
            ".ms-report-panel",
            ".ms-tag",
            "div[data-testid=\"stExpander\"] p",
            ".mingshu-report-body",
        ]:
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
