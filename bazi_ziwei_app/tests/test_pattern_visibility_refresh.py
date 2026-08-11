import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class PatternVisibilityRefreshTests(unittest.TestCase):
    def _old_chart_without_new_fields(self):
        return {
            "day_master": "甲",
            "pillars": {
                "year": {"gan": "癸", "zhi": "亥", "pillar": "癸亥"},
                "month": {"gan": "丙", "zhi": "寅", "pillar": "丙寅"},
                "day": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
                "hour": {"gan": "戊", "zhi": "辰", "pillar": "戊辰"},
            },
            "day_master_strength": {
                "strength": "身强",
                "favorable_elements": ["火", "土", "金"],
                "unfavorable_elements": ["水", "木"],
            },
        }

    def test_old_session_chart_is_enriched_with_pattern_and_seasonal_fields(self):
        from core.bazi_engine import ensure_bazi_analysis_fields

        chart = self._old_chart_without_new_fields()
        enriched = ensure_bazi_analysis_fields(chart)

        self.assertIs(enriched, chart)
        self.assertIn("pattern_analysis", enriched)
        self.assertIn("seasonal_adjustment", enriched)
        self.assertEqual(enriched["pattern_analysis"]["pattern"], "食神格")
        self.assertIn("丙", enriched["seasonal_adjustment"]["primary_useful_stems"])

    def test_bazi_and_overview_pages_call_enrichment_helper(self):
        for rel in ["ui/bazi_page.py", "ui/life_overview_page.py", "ui/home.py"]:
            with open(os.path.join(APP_DIR, rel), "r", encoding="utf-8") as file:
                text = file.read()
            self.assertIn("ensure_bazi_analysis_fields", text, rel)

    def test_home_displays_editorial_homepage_contract(self):
        with open(os.path.join(APP_DIR, "ui", "home.py"), "r", encoding="utf-8") as file:
            text = file.read()
        self.assertIn("HOME_VERSION", text)
        self.assertIn("HOME_CACHE_VERSION_LABEL", text)
        self.assertIn("render_homepage_landing", text)
        self.assertNotIn("v106", text)
        with open(os.path.join(APP_DIR, "ui", "homepage_components.py"), "r", encoding="utf-8") as file:
            component_text = file.read()
        self.assertIn('HOME_VERSION = "v4.1.0"', component_text)
        self.assertIn('<h1>命数</h1>', component_text)
        self.assertIn("本地排盘", component_text)
        self.assertIn("隐私优先", component_text)
        self.assertNotIn("当前版本：", component_text)
        self.assertNotIn("AI科技感", component_text)


if __name__ == "__main__":
    unittest.main()
