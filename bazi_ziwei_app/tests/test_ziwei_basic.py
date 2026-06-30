import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class ZiweiBasicTests(unittest.TestCase):
    def test_basic_ziwei_chart_has_twelve_palaces(self):
        from core.ziwei_engine import build_ziwei_chart

        chart = build_ziwei_chart(
            {
                "name": "测试用户",
                "gender": "女",
                "birth_date": "1992-05-06",
                "birth_hour": 9,
                "birth_minute": 30,
            }
        )

        self.assertTrue(chart["available"])
        self.assertEqual(len(chart["palaces"]), 12)
        self.assertTrue(
            "十四主星排布将在后续版本完善" in chart["star_note"]
            or "十四主星排布已实现" in chart["star_note"]
        )


if __name__ == "__main__":
    unittest.main()
