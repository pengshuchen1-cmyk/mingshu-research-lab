import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class DefaultPortTests(unittest.TestCase):
    def test_default_docs_and_launchers_use_8501_not_8888(self):
        checked_files = ["README.md", "CHANGELOG.md", "run_mac.sh", "start.command"]
        for filename in checked_files:
            path = os.path.join(APP_DIR, filename)
            with self.subTest(filename=filename):
                with open(path, "r", encoding="utf-8") as file:
                    text = file.read()
                self.assertIn("8501", text)
                forbidden_defaults = [
                    "--server.port 8888",
                    "http://127.0.0.1:8888",
                    "localhost:8888",
                ]
                for forbidden in forbidden_defaults:
                    self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
