import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageV106Tests(unittest.TestCase):
    def test_homepage_v106_modules_and_version_marker_exist(self):
        home_text = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
        components_text = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        self.assertIn('HOME_VERSION = "v2.0.0"', components_text)
        self.assertIn("from ui.homepage_components import", home_text)
        self.assertIn("render_homepage_landing", home_text)
        self.assertTrue((ROOT / "ui" / "homepage_components.py").exists())
        self.assertTrue((ROOT / "ui" / "homepage_styles.py").exists())

    def test_homepage_contains_required_landing_sections(self):
        text = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        required_phrases = [
            "命数研究室",
            "认识命数<br>活出选择",
            "五行主题",
            "今日宜穿",
            "今日注意",
            "大众参考",
            "今日/年度建议",
            "开始探索命数",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, text)
        self.assertIn('st.session_state["navigate_to"] = target', text)
        self.assertNotIn("AI科技感", text)

    def test_homepage_contains_internal_product_navigation(self):
        text = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        expected_targets = {
            "今日/年度建议": "今日/年度建议",
            "个人命盘": "个人命盘",
            "简明报告": "简明报告",
            "设置/档案": "设置/档案",
        }
        for label, target in expected_targets.items():
            self.assertIn(f'"{label}"', text)
            self.assertIn(f'"{target}"', text)

    def test_homepage_styles_match_editorial_visual_system(self):
        text = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        for token in [
            ".ms2-home",
            ".ms2-product-nav",
            ".ms2-hero",
            ".ms2-daily-advice",
            ".ms2-color-dot",
            "@media (max-width: 768px)",
            "prefers-reduced-motion: reduce",
        ]:
            self.assertIn(token, text)
        for removed in [
            ".ms2-phone-preview",
            ".ms2-value-strip",
            ".ms2-entry-choices",
            ".ms2-method-boundary",
            ".ms2-footer-action",
        ]:
            self.assertNotIn(removed, text)

    def test_homepage_does_not_use_forbidden_words(self):
        combined = (
            (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
            + (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
            + (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        )
        forbidden = [
            "逆天改命",
            "必定发财",
            "正缘必到",
            "有灾",
            "化灾",
            "破解",
            "转运",
            "消灾",
            "短命",
            "大病",
            "车祸",
        ]
        for word in forbidden:
            self.assertNotIn(word, combined)

    def test_reference_design_asset_or_spec_exists(self):
        self.assertTrue(
            (ROOT / "docs" / "design" / "homepage_reference.png").exists()
            or (ROOT / "docs" / "design" / "homepage_design_spec.md").exists()
        )


if __name__ == "__main__":
    unittest.main()
