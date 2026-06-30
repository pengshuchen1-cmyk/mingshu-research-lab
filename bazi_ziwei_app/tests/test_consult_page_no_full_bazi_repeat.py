import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ConsultPageNoFullBaziRepeatTests(unittest.TestCase):
    def test_inquiry_page_does_not_render_full_four_pillars(self):
        with open(os.path.join(APP_DIR, "ui", "inquiry_page.py"), "r", encoding="utf-8") as file:
            text = file.read()
        self.assertIn("render_loaded_profile_hint", text)
        self.assertNotIn("def _render_pillar_section", text)
        self.assertNotIn("### 四柱八字", text)
        self.assertNotIn("PILLAR_NAMES", text)


if __name__ == "__main__":
    unittest.main()
