import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class VersionVisibleTests(unittest.TestCase):
    def test_home_wires_the_editorial_version_contract(self):
        with open(os.path.join(APP_DIR, "ui", "home.py"), "r", encoding="utf-8") as file:
            text = file.read()
        self.assertIn("HOME_VERSION", text)
        self.assertIn("HOME_CACHE_VERSION_LABEL", text)
        self.assertIn("render_homepage_landing", text)
        with open(os.path.join(APP_DIR, "ui", "homepage_components.py"), "r", encoding="utf-8") as file:
            component_text = file.read()
        self.assertNotIn("v106", text)
        self.assertIn('HOME_VERSION = "v5.0.0"', component_text)
        self.assertIn('HOME_CACHE_VERSION_LABEL = "v5-static-sky"', component_text)
        self.assertNotIn("helix", component_text.lower())
        self.assertIn('<h1>命数</h1>', component_text)
        self.assertIn("TYPEWRITER_QUESTIONS", component_text)
        self.assertNotIn("问问命数研究室", component_text)
        for stale_marker in ["当前版本：", "首页视觉重构", "运行端口：8501", "AI科技感"]:
            self.assertNotIn(stale_marker, component_text)


if __name__ == "__main__":
    unittest.main()
