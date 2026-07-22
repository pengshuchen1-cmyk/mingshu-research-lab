import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InquiryLuckV106CVisualAlignmentTests(unittest.TestCase):
    def test_inquiry_and_luck_pages_use_homepage_visual_language(self):
        expected = {
            "inquiry_page.py": ["v106c-page-hero", "ms-report-panel", "ms-mini-metric", "ms-tag"],
            "luck_page.py": ["v106c-page-hero", "ms-report-panel", "ms-mini-metric", "ms-luck-stage-card", "ms-tag"],
        }
        for filename, tokens in expected.items():
            text = (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text, f"{filename} 缺少 {token}")

    def test_inquiry_and_luck_pages_do_not_emit_old_light_inline_cards(self):
        combined = "\n".join(
            (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for filename in ["inquiry_page.py", "luck_page.py"]
        )
        forbidden = [
            "background:#FAF7F4",
            "background:#f8f9fa",
            "background:#e8f5e9",
            "color:#3D2B1A",
            "color:#5C4A32",
            "color:#8C7A64",
            "color:#666",
            "border:1px solid #EDE6DC",
            "border:1px solid #e0e0e0",
        ]
        for snippet in forbidden:
            self.assertNotIn(snippet, combined)

    def test_global_css_has_luck_stage_card_component(self):
        text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        for token in [".ms-luck-stage-card", ".ms-luck-stage-card.current", ".ms-action-grid"]:
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
