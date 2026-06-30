import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class SinglePort8501Tests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        with open(os.path.join(APP_DIR, relative_path), "r", encoding="utf-8") as file:
            return file.read()

    def test_readme_recommends_venv_python_and_8501(self):
        text = self._read("README.md")
        self.assertIn(".venv/bin/python -m streamlit run app.py --server.port 8501", text)
        self.assertIn("python3", text)
        self.assertIn("http://127.0.0.1:8501", text)
        self.assertNotIn("http://127.0.0.1:8888", text)
        self.assertNotIn("--server.port 8888", text)

    def test_run_mac_uses_8501(self):
        text = self._read("run_mac.sh")
        self.assertIn("--server.port 8501", text)
        self.assertIn("http://127.0.0.1:8501", text)
        self.assertNotIn("--server.port 8888", text)


if __name__ == "__main__":
    unittest.main()
