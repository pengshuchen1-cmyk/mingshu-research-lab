import os
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class VisibleAcceptancePolishTests(unittest.TestCase):
    def _read_ui(self, filename: str) -> str:
        with open(os.path.join(APP_DIR, "ui", filename), "r", encoding="utf-8") as file:
            return file.read()

    def test_bazi_page_uses_short_lunar_summary_and_expander_details(self):
        text = self._read_ui("bazi_page.py")
        self.assertIn("def _short_lunar_text", text)
        self.assertIn('rows.append(("农历", _short_lunar_text(lunar)))', text)
        self.assertIn('st.expander("专业历法细节"', text)

    def test_yearly_month_cards_show_top_event_labels(self):
        text = self._read_ui("yearly_page.py")
        self.assertIn("def _month_top_event_summary", text)
        self.assertIn("event_summary_html", text)
        self.assertIn("本月重点事件", text)
        self.assertIn("top_events", text)


if __name__ == "__main__":
    unittest.main()
