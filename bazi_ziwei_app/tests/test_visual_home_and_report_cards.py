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
        self.assertIn("ms2-product-nav", text)
        self.assertIn("ms2-daily-advice", text)
        self.assertIn("今日宜穿", text)
        self.assertIn("大众参考", text)
        self.assertIn("认识命数<br>活出选择", text)
        self.assertNotIn("认识命数，", text)
        self.assertIn("开始探索命数", text)
        self.assertNotIn("AI科技感", text)
        self.assertIn('"今日/年度建议": "今日/年度建议"', text)
        self.assertIn('"个人命盘": "个人命盘"', text)
        self.assertIn('"简明报告": "简明报告"', text)
        self.assertIn('"设置/档案": "设置/档案"', text)
        self.assertIn('st.session_state["navigate_to"] = target', text)

    def test_global_css_contains_editorial_visual_system(self):
        global_text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        text = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        self.assertIn(".ms2-hero", text)
        self.assertIn(".ms2-product-nav", text)
        self.assertIn(".ms2-daily-advice", text)
        self.assertIn(".ms2-color-dot", text)
        self.assertIn("prefers-reduced-motion: reduce", text)
        self.assertNotIn(".ms2-value-strip", text)
        self.assertNotIn(".ms2-product-preview", text)
        self.assertNotIn(".ms2-footer-action", text)
        self.assertIn(".mingshu-report-card", global_text)
        self.assertIn("#FAFAFA", text)
        self.assertIn("#EC4899", text)

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
