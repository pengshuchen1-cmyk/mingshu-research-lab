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

    def test_overview_yearly_use_compact_identity_and_special_uses_loaded_hint(self):
        life_text = self._read_ui("life_overview_page.py")
        self.assertIn("命盘：", life_text)
        self.assertIn('profile.get("name"', life_text)
        self.assertIn('dp["overall_pattern"]', life_text)
        self.assertNotIn("render_loaded_profile_hint", life_text)
        self.assertNotIn("render_full_bazi_chart", life_text)

        yearly_text = self._read_ui("yearly_page.py")
        self.assertIn("ms3-year-identity", yearly_text)
        self.assertIn("当前命盘", yearly_text)
        self.assertIn("日主{day_master}", yearly_text)
        self.assertNotIn("render_loaded_profile_hint", yearly_text)
        self.assertNotIn("render_full_bazi_chart", yearly_text)

        special_text = self._read_ui("special_reports_page.py")
        self.assertIn("render_loaded_profile_hint", special_text)
        self.assertNotIn("render_full_bazi_chart", special_text)

    def test_report_page_may_keep_full_chart_for_export(self):
        text = self._read_ui("report_page.py")
        self.assertIn("报告内容包含八字排盘", text)


if __name__ == "__main__":
    unittest.main()
