import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BaziPageV106CVisualAlignmentTests(unittest.TestCase):
    def test_bazi_page_uses_unified_dark_gold_components(self):
        text = (ROOT / "ui" / "bazi_page.py").read_text(encoding="utf-8")
        for token in [
            "v106c-page-hero",
            "ms-bazi-card",
            "ms-bazi-pill",
            "ms-bazi-note",
            "ms-bazi-bar",
        ]:
            self.assertIn(token, text)

    def test_bazi_components_do_not_use_old_light_inline_palette(self):
        combined = "\n".join(
            [
                (ROOT / "ui" / "bazi_page.py").read_text(encoding="utf-8"),
                (ROOT / "ui" / "bazi_components.py").read_text(encoding="utf-8"),
                (ROOT / "core" / "ten_god_explanations.py").read_text(encoding="utf-8"),
            ]
        )
        forbidden = [
            "background:#FAF7F4",
            "background:#EDE6DC",
            "color:#3D2B1A",
            "color:#5C4A32",
            "color:#8C7A64",
            "border:1px solid #EDE6DC",
            "border-left:3px solid #B8860B",
        ]
        for snippet in forbidden:
            self.assertNotIn(snippet, combined)

    def test_global_css_defines_bazi_page_readability_tokens(self):
        text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        for token in [
            ".v106c-page-hero",
            ".ms-bazi-card",
            ".ms-bazi-pillar-card",
            ".ms-bazi-note",
            ".ms-bazi-bar",
            ".ms-bazi-text",
        ]:
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
