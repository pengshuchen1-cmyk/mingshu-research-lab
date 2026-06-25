import os
import sys
import tempfile
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class DatabaseTests(unittest.TestCase):
    def test_save_search_update_and_delete_profile(self):
        from utils import database

        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "profiles.db")
            profile = {
                "name": "数据库测试",
                "gender": "男",
                "birth_date": "1988-08-08",
                "birth_hour": 8,
                "birth_minute": 8,
                "birth_place": "北京",
                "use_solar_time": False,
                "note": "初始备注",
            }
            profile_id = database.save_profile(profile, {"day_master": "甲"}, {"summary": "报告"})

            self.assertEqual(database.search_profiles("数据库测试")[0]["id"], profile_id)
            database.update_profile_basic(profile_id, note="新备注")
            self.assertEqual(database.get_profile(profile_id)["note"], "新备注")
            database.delete_profile(profile_id)
            self.assertEqual(database.list_profiles(), [])


if __name__ == "__main__":
    unittest.main()
