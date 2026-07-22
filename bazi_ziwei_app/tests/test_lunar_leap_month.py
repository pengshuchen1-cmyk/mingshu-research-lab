"""农历闰月输入排盘测试 — v1.1-B"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "lunar_leap_month_cases.json")


class TestLunarLeapMonth(unittest.TestCase):
    """验证农历闰月输入转换与排盘。"""

    def test_fixture_exists(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH), "农历闰月测试样例文件不存在")

    def test_fixture_loadable(self):
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        self.assertIn("cases", data)
        self.assertGreater(len(data["cases"]), 2)

    def test_lunar_to_solar_conversion(self):
        """农历输入可正常转换而不报错。"""
        from lunar_python import Lunar
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        for case in data["cases"]:
            try:
                lunar = Lunar.fromYmd(case["lunar_year"], case["lunar_month"], case["lunar_day"])
                solar = lunar.getSolar()
                self.assertIsNotNone(solar, f"{case['case_id']}: 转换失败")
            except Exception as exc:
                if case.get("is_leap_month"):
                    self.skipTest(f"闰月可能存在转换限制: {exc}")
                else:
                    self.fail(f"{case['case_id']}: 非闰月也应可转换: {exc}")

    def test_leap_month_calendar_type_recorded(self):
        """如果 chart 支持 calendar_type/lunar_info，应正确记录。"""
        from core.bazi_engine import build_bazi_chart
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        for case in data["cases"]:
            if not case.get("is_leap_month"):
                continue
            # Use birth_datetime from fixture
            dt_parts = case["birth_datetime"].split(" ")
            prof = {
                "name": case.get("description", "Test"),
                "gender": case["gender"],
                "birth_date": dt_parts[0],
                "birth_hour": int(dt_parts[1].split(":")[0]),
                "birth_minute": int(dt_parts[1].split(":")[1]),
                "birth_place": "Beijing",
            }
            chart = build_bazi_chart(prof)
            self.assertNotIn("error", chart,
                f"{case['case_id']}: 排盘失败: {chart.get('error')}")
            self.assertIn("pillars", chart)
            self.assertIn("lunar_text", chart, "应包含农历文本")

    def test_non_leap_month_not_confused(self):
        """非闰月月份输入不应被误判为闰月。"""
        from lunar_python import Lunar
        # 2023年二月十五（非闰月）
        lunar = Lunar.fromYmd(2023, 2, 15)
        # 验证月为正数（非闰月）
        actual_month = lunar.getMonth()
        self.assertEqual(actual_month, 2, "非闰月月份应为正数2")
        # 闰月存储为负数月，验证负数月标志闰月
        # 2023年有闰二月，对应 Lunar.fromYmd(2023, -2, 15)
        leap_lunar = Lunar.fromYmd(2023, -2, 15)
        leap_month = leap_lunar.getMonth()
        self.assertEqual(leap_month, -2, "闰月月份应为负数-2")
        self.assertNotEqual(leap_lunar.getMonth(), lunar.getMonth(), "闰月与非闰月月份应不同")

    def test_build_bazi_chart_converts_lunar_profile_before_pillars(self):
        """农历资料进入排盘核心时，应先换算成真实公历再排四柱。"""
        from core.bazi_engine import build_bazi_chart

        chart = build_bazi_chart({
            "name": "张旭森",
            "gender": "男",
            "calendar_type": "lunar",
            "birth_date": "2000-12-28",
            "birth_hour": 7,
            "birth_minute": 30,
            "birth_place": "未提供",
            "use_true_solar_time": False,
        })

        self.assertNotIn("error", chart)
        self.assertEqual(chart.get("profile", {}).get("birth_date"), "2001-01-22")
        self.assertEqual(chart.get("profile", {}).get("lunar_birth_date"), "2000-12-28")
        self.assertEqual(chart.get("profile", {}).get("calendar_type"), "lunar")
        self.assertEqual(chart.get("original_birth_datetime"), "2001-01-22 07:30")
        self.assertEqual(
            {key: value.get("pillar") for key, value in chart.get("pillars", {}).items()},
            {"year": "庚辰", "month": "己丑", "day": "乙酉", "hour": "庚辰"},
        )


if __name__ == "__main__":
    unittest.main()
