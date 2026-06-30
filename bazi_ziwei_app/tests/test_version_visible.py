import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class VersionVisibleTests(unittest.TestCase):
    def test_home_contains_visible_v102_version_marker(self):
        with open(os.path.join(APP_DIR, "ui", "home.py"), "r", encoding="utf-8") as file:
            text = file.read()
        self.assertIn("当前版本：v1.0.2 专业流月断事增强", text)
        self.assertIn("运行端口：8501", text)
        self.assertIn("更新时间：2026-06-27", text)
        self.assertIn("v1.0.2-professional-monthly-events", text)


if __name__ == "__main__":
    unittest.main()
