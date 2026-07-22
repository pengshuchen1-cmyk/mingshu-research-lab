"""节气边界月柱切换测试 — v1.1-B"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "jieqi_boundary_cases.json")


class TestJieqiBoundaryMonthPillar(unittest.TestCase):
    """验证节气切换前后月柱正确性。"""

    def test_fixture_exists(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH), "节气边界测试样例文件不存在")

    def test_fixture_loadable(self):
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        self.assertIn("cases", data)
        self.assertGreater(len(data["cases"]), 5)

    def test_each_case_generates_pillars_no_crash(self):
        """每个节气案例至少能正常排盘不报错。"""
        from core.bazi_engine import build_bazi_chart
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        for case in data["cases"]:
            prof = {
                "name": case.get("description", "Test"),
                "gender": case["gender"],
                "birth_date": case["birth_datetime"].split(" ")[0],
                "birth_hour": int(case["birth_datetime"].split(" ")[1].split(":")[0]),
                "birth_minute": int(case["birth_datetime"].split(" ")[1].split(":")[1]),
                "birth_place": "Beijing",
            }
            chart = build_bazi_chart(prof)
            self.assertNotIn("error", chart,
                f"{case['case_id']}: 排盘失败: {chart.get('error')}")

    def test_lichun_boundary_year_change(self):
        """验证立春前后年柱不同。"""
        from core.bazi_engine import build_bazi_chart
        # 2024年立春约2月4日16:27
        before = build_bazi_chart({"name": "T", "gender": "男", "birth_date": "2024-02-03", "birth_hour": 10, "birth_minute": 0, "birth_place": "Beijing"})
        after = build_bazi_chart({"name": "T", "gender": "男", "birth_date": "2024-02-04", "birth_hour": 20, "birth_minute": 0, "birth_place": "Beijing"})
        yr_before = before.get("pillars", {}).get("year", {}).get("pillar", "")
        yr_after = after.get("pillars", {}).get("year", {}).get("pillar", "")
        self.assertNotEqual(yr_before, yr_after, "立春前后年柱应不同")
        self.assertTrue(yr_before.startswith("癸"), f"2024立春前应为癸卯: 实际{yr_before}")
        self.assertTrue(yr_after.startswith("甲"), f"2024立春后应为甲辰: 实际{yr_after}")

    def test_verified_cases_match(self):
        """review_status=verified 的案例期望四柱应匹配。"""
        from core.bazi_engine import build_bazi_chart
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        for case in data["cases"]:
            if case.get("review_status") != "verified":
                continue
            prof = {
                "name": case.get("description", "Test"),
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


if __name__ == "__main__":
    unittest.main()
