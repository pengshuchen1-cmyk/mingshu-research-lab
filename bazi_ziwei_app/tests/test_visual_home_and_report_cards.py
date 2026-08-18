import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VisualHomeAndReportCardsTests(unittest.TestCase):
    def test_home_has_editorial_landing_visual_and_internal_links(self):
        home_text = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
        text = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        self.assertIn("render_homepage_landing", home_text)
        self.assertNotIn("清理页面缓存并刷新", home_text)
        self.assertIn("ms2-hero", text)
        app_text = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("editorial-product-nav", app_text)
        self.assertIn("ms2-question-composer", text)
        self.assertIn("今天我的运势如何？", text)
        self.assertIn("如何推算我的命盘？", text)
        self.assertIn("今年是我的本命年，我的事业和爱情怎么样？", text)
        self.assertIn('<p class="ms2-hero-kicker">看见你的</p>', text)
        self.assertIn("<h1>命数</h1>", text)
        self.assertNotIn("AI科技感", text)
        self.assertIn('_open_product_page("今日/年度建议")', text)
        self.assertIn('_open_product_page("个人命盘")', text)

    def test_global_css_contains_editorial_visual_system(self):
        global_text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        text = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        self.assertIn(".ms2-hero", text)
        self.assertIn(".st-key-editorial-product-nav", global_text)
        self.assertIn(".st-key-ms2-question-composer", text)
        self.assertIn("backdrop-filter: blur(22px)", text)
        self.assertNotIn(".ms2-helix-canvas", text)
        self.assertNotIn(".st-key-ms2-dashboard-grid", text)
        self.assertIn("prefers-reduced-motion: reduce", text)
        self.assertNotIn(".ms2-value-strip", text)
        self.assertNotIn(".ms2-product-preview", text)
        self.assertNotIn(".ms2-footer-action", text)
        self.assertIn(".mingshu-report-card", global_text)
        self.assertIn("#FFFFFF", text)
        self.assertNotIn(".st-key-editorial-product-nav", text)

    def test_yearly_cards_follow_editorial_tokens_and_mobile_stack(self):
        text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertIn(".ms3-year-cover", text)
        self.assertIn(".ms3-year-metrics", text)
        self.assertIn(".ms3-insight-grid", text)
        self.assertIn("@media (max-width: 768px)", text)
        self.assertIn("grid-template-columns: 1fr", text)

    def test_special_reports_use_card_reader_and_left_right_buttons(self):
        text = (ROOT / "ui" / "special_reports_page.py").read_text(encoding="utf-8")
        self.assertIn("_render_special_report_card_carousel", text)
        self.assertIn("专项报告名片", text)
        self.assertIn("← 上一张", text)
        self.assertIn("下一张 →", text)
        self.assertNotIn("expanded=True", text)

    def test_report_export_keeps_card_reader_and_simple_summary(self):
        text = (ROOT / "ui" / "report_page.py").read_text(encoding="utf-8")
        self.assertIn("报告名片预览", text)
        self.assertIn("报告摘要", text)
        self.assertIn("下一步建议", text)
        self.assertIn("mingshu-report-card", text)
        self.assertIn("← 上一张", text)
        self.assertIn("下一张 →", text)
        self.assertIn("报告很长，先用名片看重点", text)


if __name__ == "__main__":
    unittest.main()
