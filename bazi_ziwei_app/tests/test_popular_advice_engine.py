import datetime as dt
import os
import sys
import unittest
from unittest.mock import patch


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


FORBIDDEN_WORDS = [
    "必定",
    "绝对",
    "一定发财",
    "一定离婚",
    "必有灾",
    "必分手",
]


def flatten_text(value):
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


class PopularAdviceEngineTests(unittest.TestCase):
    def test_daily_advice_exposes_public_contract_and_boundary(self):
        from core.popular_advice_engine import build_daily_advice

        result = build_daily_advice(dt.date(2026, 7, 11))

        self.assertEqual(result["date"], "2026-07-11")
        self.assertEqual(result["day_pillar"], result["pillar"])
        self.assertIn(result["element_theme"], ["木", "火", "土", "金", "水"])
        self.assertEqual(result["timezone"], "Asia/Shanghai")
        self.assertIn("未读取", result["boundary_note"])
        self.assertIn("非个人", result["boundary_note"])
        for major_decision_area in ["医疗", "投资", "法律", "婚姻"]:
            self.assertIn(major_decision_area, result["boundary_note"])

    def test_daily_advice_is_stable_for_the_same_date(self):
        from core.popular_advice_engine import build_daily_advice

        target = dt.date(2026, 7, 11)
        self.assertEqual(build_daily_advice(target), build_daily_advice(target))

    def test_daily_advice_does_not_guess_when_calendar_calculation_fails(self):
        from core.popular_advice_engine import (
            PopularAdviceUnavailableError,
            build_daily_advice,
        )

        with patch(
            "core.popular_advice_engine._get_day_pillar",
            side_effect=PopularAdviceUnavailableError("calendar unavailable"),
        ):
            with self.assertRaises(PopularAdviceUnavailableError):
                build_daily_advice(dt.date(2026, 7, 11))

    def test_get_day_pillar_raises_when_solar_construction_fails(self):
        from core.popular_advice_engine import (
            PopularAdviceUnavailableError,
            _get_day_pillar,
        )

        with patch(
            "core.bazi_calendar_adapter.day_pillar_seed",
            side_effect=RuntimeError("calendar unavailable"),
        ):
            with self.assertRaises(PopularAdviceUnavailableError) as raised:
                _get_day_pillar(dt.date(2026, 7, 11))

        self.assertIsInstance(raised.exception.__cause__, RuntimeError)

    def test_yearly_popular_advice_for_2026_uses_bingwu_year(self):
        from core.popular_advice_engine import build_yearly_popular_advice

        result = build_yearly_popular_advice(2026)

        self.assertEqual(result["year"], 2026)
        self.assertEqual(result["pillar"], "丙午")
        self.assertIn("今年建议", result["title"])
        self.assertGreaterEqual(len(result["keywords"]), 3)
        self.assertGreaterEqual(len(result["action_advice"]), 3)
        self.assertGreaterEqual(len(result["wellbeing_advice"]), 2)
        self.assertIn("立春", result["boundary_note"])

    def test_daily_advice_contains_color_wearing_relaxation_and_actions(self):
        from core.popular_advice_engine import build_daily_advice

        result = build_daily_advice(dt.date(2026, 7, 11))

        for key in [
            "date",
            "pillar",
            "title",
            "lucky_colors",
            "wearing_advice",
            "relaxation_advice",
            "suitable_actions",
            "actions_to_avoid",
            "basis",
        ]:
            self.assertIn(key, result)
        self.assertEqual(result["date"], "2026-07-11")
        self.assertGreaterEqual(len(result["lucky_colors"]), 2)
        self.assertGreaterEqual(len(result["suitable_actions"]), 3)
        self.assertGreaterEqual(len(result["actions_to_avoid"]), 2)

    def test_popular_advice_copy_avoids_absolute_claims(self):
        from core.popular_advice_engine import build_daily_advice, build_yearly_popular_advice

        text = flatten_text(
            {
                "daily": build_daily_advice(dt.date(2026, 7, 11)),
                "yearly": build_yearly_popular_advice(2026),
            }
        )

        for forbidden in FORBIDDEN_WORDS:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
