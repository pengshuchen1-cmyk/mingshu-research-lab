"""八字算法准确性测试 — v1.1-A"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "known_bazi_cases.json")


class TestBaziAlgorithmAccuracy(unittest.TestCase):
    """验证八字排盘算法准确性。"""

    def test_fixture_exists(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH))

    def test_fixture_loadable(self):
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        self.assertIn("cases", data)
        self.assertGreater(len(data["cases"]), 5)

    def test_each_case_generates_pillars(self):
        from core.bazi_engine import build_bazi_chart
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            prof = {
                "name": case.get("name", "Test"),
                "gender": case["gender"],
                "birth_date": case["birth_datetime"].split(" ")[0],
                "birth_hour": int(case["birth_datetime"].split(" ")[1].split(":")[0]),
                "birth_minute": int(case["birth_datetime"].split(" ")[1].split(":")[1]),
                "birth_place": "Beijing",
            }
            chart = build_bazi_chart(prof)
            p = chart.get("pillars", {})
            exp = case["expected_pillars"]
            for key in ["year", "month", "day", "hour"]:
                actual = p.get(key, {}).get("pillar", "")
                expected = exp.get(key, "")
                self.assertEqual(actual, expected,
                    f"{case['case_id']} {key}: 期望{expected} 实际{actual}")

    def test_each_case_day_master(self):
        from core.bazi_engine import build_bazi_chart
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            prof = {
                "name": case.get("name", "Test"),
                "gender": case["gender"],
                "birth_date": case["birth_datetime"].split(" ")[0],
                "birth_hour": int(case["birth_datetime"].split(" ")[1].split(":")[0]),
                "birth_minute": int(case["birth_datetime"].split(" ")[1].split(":")[1]),
                "birth_place": "Beijing",
            }
            chart = build_bazi_chart(prof)
            dm = chart.get("day_master", "")
            self.assertEqual(dm, case["expected_day_master"],
                f"{case['case_id']}: 日主期望{case['expected_day_master']} 实际{dm}")

    def test_calendar_engine_direct_api(self):
        from core.calendar_engine import get_lunar_eight_char
        result = get_lunar_eight_char(1990, 6, 15, 14, 30, "女")
        self.assertNotIn("error", result,
            "calendar_engine.get_lunar_eight_char 不应返回 error")

    def test_strength_engine_returns_fields(self):
        from core.bazi_engine import build_bazi_chart
        prof = {"name":"T","gender":"男","birth_date":"1990-06-15","birth_hour":14,"birth_minute":30,"birth_place":"Beijing"}
        chart = build_bazi_chart(prof)
        strength = chart.get("day_master_strength", {})
        for field in ["strength", "net_score", "favorable_elements", "unfavorable_elements"]:
            self.assertIn(field, strength,
                f"day_master_strength 缺少 {field}")

    def test_ten_gods_returns_counts(self):
        from core.bazi_engine import build_bazi_chart
        prof = {"name":"T","gender":"男","birth_date":"1990-06-15","birth_hour":14,"birth_minute":30,"birth_place":"Beijing"}
        chart = build_bazi_chart(prof)
        tg = chart.get("ten_god_counts", {})
        self.assertGreater(len(tg), 0, "ten_god_counts 不应为空")
        self.assertIn("正财", tg, "应包含正财")

    def test_lichun_year_change(self):
        from core.bazi_engine import build_bazi_chart
        # 1990年立春 2月4日 15:24
        before = build_bazi_chart({"name":"T","gender":"男","birth_date":"1990-02-04","birth_hour":10,"birth_minute":0,"birth_place":"Beijing"})
        after = build_bazi_chart({"name":"T","gender":"男","birth_date":"1990-02-04","birth_hour":16,"birth_minute":0,"birth_place":"Beijing"})
        yr_before = before.get("pillars", {}).get("year", {}).get("pillar", "")
        yr_after = after.get("pillars", {}).get("year", {}).get("pillar", "")
        self.assertEqual(yr_before, "己巳", "立春前年柱应为己巳")
        self.assertEqual(yr_after, "庚午", "立春后年柱应为庚午")
        self.assertNotEqual(yr_before, yr_after, "立春前后年柱应不同")

    def test_zi_hour_correct_stem(self):
        from core.bazi_engine import build_bazi_chart
        chart = build_bazi_chart({"name":"T","gender":"男","birth_date":"2000-01-01","birth_hour":0,"birth_minute":0,"birth_place":"Beijing"})
        hour = chart.get("pillars", {}).get("hour", {}).get("pillar", "")
        self.assertTrue(len(hour) == 2, f"时柱应有2个字: {hour}")


if __name__ == "__main__":
    unittest.main()
