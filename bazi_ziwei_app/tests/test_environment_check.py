import os
import sys
import types
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class EnvironmentCheckTests(unittest.TestCase):
    def test_check_dependencies_reports_all_available(self):
        from check_env import check_dependencies

        def fake_import(name):
            if name == "lunar_python":
                return types.SimpleNamespace(Solar=object)
            return object()

        ok, messages = check_dependencies(fake_import)

        self.assertTrue(ok)
        self.assertEqual(messages, ["环境检查通过"])

    def test_check_dependencies_reports_install_hint_when_missing(self):
        from check_env import check_dependencies

        def fake_import(name):
            if name == "lunar_python":
                raise ImportError("missing lunar_python")
            return object()

        ok, messages = check_dependencies(fake_import)

        self.assertFalse(ok)
        self.assertIn("lunar_python 未安装或不可导入", messages[0])
        self.assertIn("python -m pip install -r requirements.txt", messages[-1])


if __name__ == "__main__":
    unittest.main()
