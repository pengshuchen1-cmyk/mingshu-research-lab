import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageV3Tests(unittest.TestCase):
    def test_homepage_modules_and_version_marker_exist(self):
        home_text = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
        components = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        self.assertIn('HOME_VERSION = "v3.0.0"', components)
        self.assertIn("render_homepage_landing", home_text)
        self.assertTrue((ROOT / "assets" / "hero-sky-v1.png").exists())

    def test_homepage_contains_required_immersive_sections(self):
        text = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        for phrase in [
            "<em>看见</em>你的命数。",
            "今天我的运势如何？",
            "如何推算我的命盘？",
            "今年是我的本命年，我的事业和爱情怎么样？",
        ]:
            self.assertIn(phrase, text)
        for removed_phrase in [
            "命数研究室 · AI 命理助手",
            "问问命数研究室",
            "或者从一个常见问题开始",
        ]:
            self.assertNotIn(removed_phrase, text)

    def test_homepage_reuses_application_navigation(self):
        component = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("def _render_product_nav", component)
        self.assertIn('st.container(key="editorial-product-nav")', app)

    def test_homepage_mounts_question_placeholder_typing_effect(self):
        component = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

        self.assertIn("render_question_typing_effect", component)
        self.assertIn("render_question_typing_effect(", component)
        self.assertNotIn("focus_input=", component)

    def test_homepage_styles_are_immersive_and_mobile_safe(self):
        text = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
        for token in [
            ".st-key-ms2-home",
            ".st-key-ms2-hero",
            ".st-key-ms2-question-composer",
            "linear-gradient",
            "object-fit: cover",
            "@media (max-width: 768px)",
            "prefers-reduced-motion: reduce",
        ]:
            self.assertIn(token, text)

    def test_homepage_does_not_use_forbidden_claims(self):
        combined = (
            (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
            + (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
        )
        for word in ["逆天改命", "必定发财", "正缘必到", "化灾", "转运", "消灾"]:
            self.assertNotIn(word, combined)


if __name__ == "__main__":
    unittest.main()
