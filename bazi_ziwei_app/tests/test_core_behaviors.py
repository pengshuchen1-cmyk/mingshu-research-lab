import json
import os
import sqlite3
import sys
import tempfile
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class CoreBehaviorTests(unittest.TestCase):
    def test_ten_god_relationships_follow_day_master_rules(self):
        from core.ten_gods import get_ten_god

        self.assertEqual(get_ten_god("甲", "甲"), "比肩")
        self.assertEqual(get_ten_god("甲", "乙"), "劫财")
        self.assertEqual(get_ten_god("甲", "丙"), "食神")
        self.assertEqual(get_ten_god("甲", "丁"), "伤官")
        self.assertEqual(get_ten_god("甲", "戊"), "偏财")
        self.assertEqual(get_ten_god("甲", "己"), "正财")
        self.assertEqual(get_ten_god("甲", "庚"), "七杀")
        self.assertEqual(get_ten_god("甲", "辛"), "正官")
        self.assertEqual(get_ten_god("甲", "壬"), "偏印")
        self.assertEqual(get_ten_god("甲", "癸"), "正印")

    def test_five_element_weights_include_month_command_bonus(self):
        from core.five_elements import calculate_five_elements

        chart = {
            "pillars": {
                "year": {"gan": "甲", "zhi": "子"},
                "month": {"gan": "丙", "zhi": "寅"},
                "day": {"gan": "戊", "zhi": "午"},
                "hour": {"gan": "庚", "zhi": "申"},
            }
        }

        scores = calculate_five_elements(chart)

        self.assertAlmostEqual(scores["木"], 4.0)
        self.assertAlmostEqual(scores["火"], 2.5)
        self.assertAlmostEqual(scores["土"], 2.1)
        self.assertAlmostEqual(scores["金"], 2.0)
        self.assertAlmostEqual(scores["水"], 1.5)

    def test_strength_analysis_returns_required_fields(self):
        from core.five_elements import calculate_five_elements
        from core.strength_engine import analyze_day_master_strength

        chart = {
            "pillars": {
                "year": {"gan": "甲", "zhi": "子"},
                "month": {"gan": "丙", "zhi": "寅"},
                "day": {"gan": "戊", "zhi": "午"},
                "hour": {"gan": "庚", "zhi": "申"},
            },
            "day_master": "戊",
        }
        scores = calculate_five_elements(chart)

        self.assertEqual(set(scores.keys()), {"木", "火", "土", "金", "水"})

        result = analyze_day_master_strength(chart)

        for key in ["strength", "net_score", "support_score", "pressure_score", "favorable_elements"]:
            self.assertIn(key, result)
        self.assertIn(result["strength"], ["身强", "中和", "身弱"])

    def test_luck_stage_scores_favorable_elements_positive(self):
        from core.stage_engine import analyze_luck_stage

        chart = {
            "day_master_strength": {
                "strength": "身弱",
                "favorable_elements": ["木", "火"],
                "unfavorable_elements": ["金", "水"],
            }
        }
        luck_item = {"gan_element": "木", "zhi_element": "土"}

        result = analyze_luck_stage(chart, luck_item)

        self.assertGreater(result["stage_score"], 0)
        self.assertIn(result["stage_level"], ["小有助力", "偏助力"])

    def test_profile_validation_rejects_invalid_time(self):
        from utils.validators import validate_profile

        ok, message = validate_profile(
            {"name": "测试", "birth_date": "1990-01-01", "birth_hour": 24, "birth_minute": 0}
        )

        self.assertFalse(ok)
        self.assertIn("出生小时", message)

    def test_database_round_trip_uses_local_sqlite(self):
        from utils import database

        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "profiles.db")
            database.init_db()
            profile = {
                "name": "测试用户",
                "gender": "男",
                "birth_date": "1990-01-01",
                "birth_hour": 10,
                "birth_minute": 0,
                "birth_place": "",
                "use_solar_time": False,
            }
            chart = {"day_master": "丙", "pillars": {}}
            report = {"summary": "基础报告"}

            profile_id = database.save_profile(profile, chart, report)
            items = database.list_profiles()
            loaded = database.get_profile(profile_id)

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["name"], "测试用户")
            self.assertEqual(loaded["chart"]["day_master"], "丙")
            self.assertEqual(loaded["report"]["summary"], "基础报告")

            with sqlite3.connect(database.DB_PATH) as conn:
                raw = conn.execute("SELECT chart_json FROM bazi_charts").fetchone()[0]
            self.assertEqual(json.loads(raw)["day_master"], "丙")

            database.delete_profile(profile_id)
            self.assertEqual(database.list_profiles(), [])


if __name__ == "__main__":
    unittest.main()
