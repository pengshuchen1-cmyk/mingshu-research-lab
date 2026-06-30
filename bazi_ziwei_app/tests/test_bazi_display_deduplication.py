import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class BaziDisplayDeduplicationTests(unittest.TestCase):
    def _read_ui(self, filename: str) -> str:
        with open(os.path.join(APP_DIR, "ui", filename), "r", encoding="utf-8") as file:
            return file.read()

    def test_shared_bazi_components_exist(self):
        with open(os.path.join(APP_DIR, "ui", "bazi_components.py"), "r", encoding="utf-8") as file:
            text = file.read()
        self.assertIn("def render_compact_bazi_summary", text)
        self.assertIn("def render_full_bazi_chart", text)
        self.assertIn("def render_loaded_profile_hint", text)

    def test_home_uses_compact_summary_only(self):
        text = self._read_ui("home.py")
        self.assertIn("render_compact_bazi_summary", text)
        self.assertNotIn("render_full_bazi_chart", text)

    def test_bazi_page_keeps_full_chart(self):
        text = self._read_ui("bazi_page.py")
        self.assertIn("render_full_bazi_chart", text)
        self.assertIn("唯一完整展示四柱", text)

    def test_overview_yearly_special_pages_use_loaded_profile_hint(self):
        for filename in ["life_overview_page.py", "yearly_page.py", "special_reports_page.py"]:
            with self.subTest(filename=filename):
                text = self._read_ui(filename)
                self.assertIn("render_loaded_profile_hint", text)
                self.assertNotIn("render_full_bazi_chart", text)

    def test_report_page_may_keep_full_chart_for_export(self):
        text = self._read_ui("report_page.py")
        self.assertIn("报告内容包含八字排盘", text)


if __name__ == "__main__":
    unittest.main()
