import os
import sys
import tempfile
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class DatabaseRebuildTests(unittest.TestCase):
    def test_rebuild_helpers_update_profile_chart_and_report(self):
        from utils import database

        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "profiles.db")
            database.init_db()
            profile = {
                "name": "旧名字",
                "gender": "男",
                "birth_date": "1990-01-01",
                "birth_hour": 10,
                "birth_minute": 0,
                "birth_place": "上海",
                "use_solar_time": False,
            }
            profile_id = database.save_profile(
                profile,
                {"day_master": "甲", "pillars": {}},
                {"summary": "旧报告"},
            )

            database.update_profile_birth_info(
                profile_id,
                {
                    "name": "新名字",
                    "gender": "女",
                    "birth_date": "1991-02-03",
                    "birth_hour": 8,
                    "birth_minute": 30,
                    "birth_place": "北京",
                    "use_solar_time": True,
                    "note": "重新排盘测试",
                },
            )
            database.update_chart_and_report(
                profile_id,
                {"day_master": "乙", "pillars": {"day": {"pillar": "乙卯"}}},
                {"summary": "新报告"},
            )
            loaded = database.get_profile(profile_id)

            self.assertEqual(loaded["name"], "新名字")
            self.assertEqual(loaded["gender"], "女")
            self.assertEqual(loaded["birth_hour"], 8)
            self.assertEqual(loaded["chart"]["day_master"], "乙")
            self.assertEqual(loaded["report"]["summary"], "新报告")


if __name__ == "__main__":
    unittest.main()
