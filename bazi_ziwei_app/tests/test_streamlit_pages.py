import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class StreamlitPageImportTests(unittest.TestCase):
    def test_v1_page_modules_import(self):
        for module_name in [
            "ui.home",
            "ui.profile_form",
            "ui.bazi_page",
            "ui.five_element_page",
            "ui.useful_god_page",
            "ui.acceptance_page",
            "ui.luck_page",
            "ui.yearly_page",
            "ui.special_reports_page",
            "ui.ziwei_page",
            "ui.report_page",
            "ui.archive_page",
            "ui.backup_page",
            "ui.settings_page",
        ]:
            __import__(module_name)


if __name__ == "__main__":
    unittest.main()
