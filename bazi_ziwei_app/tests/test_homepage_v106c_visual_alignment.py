import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageEditorialVisualAlignmentTests(unittest.TestCase):
    def test_homepage_has_editorial_visual_contract(self):
        home = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

        self.assertIn("editorial", home)
        self.assertIn(".ms2-home", css)
        self.assertIn('section[data-testid="stSidebar"]', css)
        self.assertIn('header[data-testid="stHeader"]', css)

    def test_homepage_hero_matches_editorial_structure(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

        for token in [
            "ms2-hero-copy",
            "ms2-daily-advice",
            "今日宜穿",
            "今日注意",
            "大众参考",
        ]:
            self.assertIn(token, comp)
        self.assertIn('st.container(key="ms2-hero")', comp)
        self.assertIn("st.columns([1.08, 0.92]", comp)
        self.assertIn(
            '.st-key-ms2-hero div[data-testid="stHorizontalBlock"] '
            '> div[data-testid="stColumn"]:first-child .stButton > button[kind="primary"]',
            css,
        )

    def test_homepage_removes_old_orbit_and_gold_layers(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        for token in ["orbit", "bagua", "taiji", "mountain", "#D8B96A"]:
            self.assertNotIn(token, comp + css)

    def test_product_navigation_and_single_cta_use_internal_navigation(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

        for name in ["今日/年度建议", "个人命盘", "简明报告", "设置/档案", "开始探索命数"]:
            self.assertIn(name, comp)
        self.assertIn('_go("新建命盘"', comp)
        self.assertEqual(comp.count("primary=True"), 1)
        self.assertNotIn("_render_entry_choices", comp)
        self.assertNotIn('return f"?page={target}"', comp)

    def test_homepage_uses_truthful_public_preview_instead_of_fixed_chart_results(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

        self.assertIn("build_daily_advice", comp)
        self.assertIn("daily['day_pillar']", comp)
        self.assertIn('daily["wearing_colors"][:3]', comp)
        self.assertNotIn("build_yearly_popular_advice", comp)
        self.assertNotIn("命盘评分", comp)

    def test_homepage_uses_internal_navigation_instead_of_query_links(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        self.assertIn('st.session_state["navigate_to"] = target', comp)
        self.assertIn("st.rerun()", comp)
        self.assertNotIn("?page=", comp)
        self.assertNotIn("?page=", comp)
        self.assertIn('st.markdown("[跳到主要内容](#ms2-main)")', comp)

    def test_homepage_has_one_internal_editorial_cta_and_no_footer_cta(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

        self.assertIn("开始探索命数", comp)
        self.assertEqual(comp.count("primary=True"), 1)
        self.assertNotIn("_render_footer_action", comp)
        self.assertNotIn(".ms2-footer-action", css)

    def test_homepage_has_phone_width_public_layout(self):
        comp = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 768px)", css)
        self.assertIn(".ms2-daily-advice", css)
        phone_css = css.split("@media (max-width: 768px)", 1)[1]
        self.assertIn(".st-key-ms2-hero", phone_css)
        self.assertIn("flex-direction: column", phone_css)
        self.assertIn("width: 100%", phone_css)
        self.assertIn("min-height: 44px", css)
        self.assertIn("prefers-reduced-motion: reduce", css)


if __name__ == "__main__":
    unittest.main()
