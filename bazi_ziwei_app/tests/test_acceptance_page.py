import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class AcceptancePageTests(unittest.TestCase):
    def test_acceptance_page_imports_and_defines_samples(self):
        from ui.acceptance_page import ACCEPTANCE_SAMPLE_PROFILES, render_acceptance_page

        self.assertEqual(len(ACCEPTANCE_SAMPLE_PROFILES), 5)
        self.assertTrue(callable(render_acceptance_page))

    def test_app_navigation_contains_acceptance_center(self):
        from app import get_pages

        pages = get_pages()
        self.assertIn("验收中心", pages)

    def test_acceptance_center_shows_ziwei_plain_guide(self):
        source_path = os.path.join(APP_DIR, "ui", "acceptance_page.py")
        with open(source_path, "r", encoding="utf-8") as handle:
            source = handle.read()

        self.assertIn("build_ziwei_plain_guide", source)
        self.assertIn("build_ziwei_capability_review", source)
        self.assertIn("主星落宫怎么看", source)
        self.assertIn("星曜组合", source)
        self.assertIn("life_palace", source)
        self.assertNotIn("ming_gong", source)


if __name__ == "__main__":
    unittest.main()
