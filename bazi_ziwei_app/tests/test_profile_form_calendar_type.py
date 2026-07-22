"""新建命盘表单历法选择测试。"""

from __future__ import annotations

import unittest
from datetime import date


class ProfileFormCalendarTypeTests(unittest.TestCase):
    def test_lunar_selection_preserves_lunar_date_for_conversion(self):
        from ui.profile_form import _build_profile_payload

        profile = _build_profile_payload(
            name="张旭森",
            gender="男",
            calendar_label="农历",
            birth_date=date(2000, 12, 28),
            birth_hour=7,
            birth_minute=30,
            birth_place="",
            use_solar_time=False,
            birth_longitude=None,
        )

        self.assertEqual(profile["calendar_type"], "lunar")
        self.assertEqual(profile["birth_date"], "2000-12-28")
        self.assertEqual(profile["lunar_birth_date"], "2000-12-28")
        self.assertFalse(profile["use_true_solar_time"])

    def test_solar_selection_marks_solar_calendar_and_ignores_legacy_solar_time(self):
        from ui.profile_form import _build_profile_payload

        profile = _build_profile_payload(
            name="测试",
            gender="女",
            calendar_label="公历",
            birth_date=date(2001, 1, 22),
            birth_hour=7,
            birth_minute=30,
            birth_place="北京",
            use_solar_time=True,
            birth_longitude="116.4",
        )

        self.assertEqual(profile["calendar_type"], "solar")
        self.assertEqual(profile["birth_date"], "2001-01-22")
        self.assertNotIn("lunar_birth_date", profile)
        self.assertFalse(profile["use_true_solar_time"])
        self.assertIsNone(profile["birth_longitude"])
        self.assertEqual(profile["time_mode"], "china_standard")


if __name__ == "__main__":
    unittest.main()
