import os
import unittest
from datetime import date


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

    def test_rebuild_payload_preserves_lunar_calendar_semantics(self):
        from ui.archive_page import _build_rebuild_profile

        profile = _build_rebuild_profile(
            name="农历样例",
            gender="女",
            calendar_label="农历",
            birth_date=date(1986, 7, 10),
            birth_hour=10,
            birth_minute=0,
            birth_place="",
            is_leap_month=False,
            time_known=True,
            note="",
        )

        self.assertEqual(profile["calendar_type"], "lunar")
        self.assertEqual(profile["lunar_birth_date"], "1986-07-10")
        self.assertFalse(profile["is_leap_month"])
        self.assertEqual(profile["time_mode"], "china_standard")
        self.assertFalse(profile["use_solar_time"])

    def test_rebuild_payload_keeps_unknown_time_explicit(self):
        from ui.archive_page import _build_rebuild_profile

        profile = _build_rebuild_profile(
            name="未知时辰",
            gender="男",
            calendar_label="公历",
            birth_date=date(1994, 9, 23),
            birth_hour=10,
            birth_minute=0,
            birth_place="",
            is_leap_month=True,
            time_known=False,
            note="",
        )

        self.assertEqual(profile["calendar_type"], "solar")
        self.assertIsNone(profile["birth_hour"])
        self.assertIsNone(profile["birth_minute"])
        self.assertFalse(profile["is_leap_month"])
        self.assertNotIn("lunar_birth_date", profile)


if __name__ == "__main__":
    unittest.main()
