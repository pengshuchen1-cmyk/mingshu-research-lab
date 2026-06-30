import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ArchiveLoadVisibilityTests(unittest.TestCase):
    def test_archive_load_refreshes_visible_current_chart(self):
        with open(os.path.join(APP_DIR, "ui", "archive_page.py"), "r", encoding="utf-8") as file:
            text = file.read()

        self.assertIn('st.session_state["current_profile"]', text)
        self.assertIn('st.session_state["current_chart"]', text)
        self.assertIn('st.session_state["current_report"]', text)
        for key in [
            "current_luck_data",
            "current_yearly_data",
            "current_monthly_data",
            "current_monthly_event_results",
        ]:
            self.assertIn(f'st.session_state.pop("{key}", None)', text)
        self.assertIn('st.session_state["navigate_to"] = "八字排盘"', text)
        self.assertIn("st.rerun()", text)


if __name__ == "__main__":
    unittest.main()
