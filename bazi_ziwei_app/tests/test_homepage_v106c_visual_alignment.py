import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageImmersiveVisualAlignmentTests(unittest.TestCase):
    def test_homepage_has_origin_inspired_visual_contract(self):
        component = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        self.assertIn('st.container(key="ms2-hero")', component)
        self.assertIn('st.container(key="ms2-hero-content")', component)
        self.assertIn('st.image(str(HERO_BACKGROUND)', component)
        self.assertIn("font-size: clamp(60px, 7vw, 96px)", css)
        self.assertIn("font-weight: 300", css)
        self.assertIn("border-radius: 999px", css)
        self.assertIn("box-shadow: 0 18px 28px rgba(0, 0, 0, .20)", css)

    def test_landing_page_does_not_render_or_style_product_navigation(self):
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn(".st-key-editorial-product-nav", css)
        self.assertIn("if active_page != LANDING_PAGE_NAME:", app)

    def test_homepage_entry_actions_route_to_today_and_chart(self):
        component = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        self.assertIn('_open_product_page("今日/年度建议")', component)
        self.assertIn('_open_product_page("个人命盘")', component)

    def test_mobile_landing_overlays_submit_button_without_fixed_widths(self):
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        phone = css.split("@media (max-width: 768px)", 1)[1]
        self.assertIn("display: block !important", phone)
        self.assertIn("width: 48px !important", phone)
        self.assertIn("width: 100%", phone)
        self.assertNotIn("width: 640px", phone)


if __name__ == "__main__":
    unittest.main()
