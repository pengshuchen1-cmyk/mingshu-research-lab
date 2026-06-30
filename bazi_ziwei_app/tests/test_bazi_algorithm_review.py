import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class BaziAlgorithmReviewTests(unittest.TestCase):
    def test_luck_cycles_do_not_return_negative_age(self):
        from core.bazi_engine import build_bazi_chart
        from core.luck_engine import get_luck_cycles

        profile = {
            "name": "大运年龄验收",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
            "use_solar_time": False,
        }
        chart = build_bazi_chart(profile)
        luck = get_luck_cycles(profile, chart)

        for item in luck.get("dayun_list", []):
            self.assertGreaterEqual(int(item.get("start_age", 0)), 0)
            self.assertGreaterEqual(int(item.get("end_age", 0)), 0)

    def test_day_master_strength_has_core_fields(self):
        from core.bazi_engine import build_bazi_chart

        profile = {
            "name": "强弱字段验收",
            "gender": "女",
            "birth_date": "1992-12-26",
            "birth_hour": 0,
            "birth_minute": 0,
            "birth_place": "北京",
            "use_solar_time": False,
        }
        chart = build_bazi_chart(profile)
        strength = chart.get("day_master_strength", {})

        for key in ["strength", "net_score", "support_score", "pressure_score", "favorable_elements"]:
            self.assertIn(key, strength)


if __name__ == "__main__":
    unittest.main()
