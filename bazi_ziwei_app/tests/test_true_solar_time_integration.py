"""真太阳时集成测试 — v1.1-B"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestTrueSolarTimeIntegration(unittest.TestCase):
    """验证真太阳时校正集成正确性。"""

    def _make_profile(self, **overrides):
        prof = {
            "name": "Test",
            "gender": "男",
            "birth_date": "1990-06-15",
            "birth_hour": 8,
            "birth_minute": 0,
            "birth_place": "Beijing",
        }
        prof.update(overrides)
        return prof

    def test_default_standard_time(self):
        """默认 use_true_solar_time=False 时，使用标准时间排盘。"""
        from core.bazi_engine import build_bazi_chart
        profile = self._make_profile()
        chart = build_bazi_chart(profile)
        self.assertEqual(chart.get("time_mode"), "standard_time",
            "默认应为 standard_time")
        self.assertFalse(chart.get("true_solar_time_applied", True),
            "默认不应启用真太阳时")

    def test_true_solar_without_longitude_no_crash(self):
        """启用真太阳时但未提供 longitude，不报错，返回 warning。"""
        from core.bazi_engine import build_bazi_chart
        profile = self._make_profile(use_true_solar_time=True)
        chart = build_bazi_chart(profile)
        self.assertNotIn("error", chart,
            "不应返回 error")
        self.assertEqual(chart.get("time_mode"), "standard_time",
            "缺少经度时应回退标准时间")
        self.assertTrue(chart.get("true_solar_time_warning", ""),
            "应包含 warning")

    def test_longitude_string_float_safe_convert(self):
        """longitude 为字符串时能安全转 float。"""
        from core.calendar_engine import _ensure_float
        self.assertEqual(_ensure_float("116.4"), 116.4)
        self.assertEqual(_ensure_float("120.0"), 120.0)
        self.assertEqual(_ensure_float("女", default=120.0), 120.0,
            "非法字符串应回退默认值")
        self.assertEqual(_ensure_float(None, default=120.0), 120.0)
        self.assertEqual(_ensure_float(116.4), 116.4)

    def test_longitude_invalid_string_no_crash(self):
        """非法 longitude 字符串不应导致 crash。"""
        from core.bazi_engine import build_bazi_chart
        profile = self._make_profile(use_true_solar_time=True, birth_longitude="invalid")
        chart = build_bazi_chart(profile)
        # "invalid" in profile -> raw_longitude="invalid" -> float("invalid") raises -> except catches
        self.assertIn("error", chart,
            "非法 longitude 应返回 error 而不是 crash")

    def test_longitude_valid_standard_time_10_cases_unchanged(self):
        """use_true_solar_time=False 时，原 10 个已知样例四柱不变。"""
        from core.bazi_engine import build_bazi_chart
        fixture = os.path.join(ROOT, "tests", "fixtures", "known_bazi_cases.json")
        with open(fixture, "r") as f:
            cases = json.load(f)["cases"]
        for case in cases:
            prof = {
                "name": case.get("name", "Test"),
                "gender": case["gender"],
                "birth_date": case["birth_datetime"].split(" ")[0],
                "birth_hour": int(case["birth_datetime"].split(" ")[1].split(":")[0]),
                "birth_minute": int(case["birth_datetime"].split(" ")[1].split(":")[1]),
                "birth_place": "Beijing",
                "use_true_solar_time": False,
            }
            chart = build_bazi_chart(prof)
            p = chart.get("pillars", {})
            exp = case["expected_pillars"]
            for key in ["year", "month", "day", "hour"]:
                actual = p.get(key, {}).get("pillar", "")
                expected = exp.get(key, "")
                self.assertEqual(actual, expected,
                    f"{case['case_id']} use_true_solar_time=False: {key}: 期望{expected} 实际{actual}")

    def test_chart_has_time_mode_fields(self):
        """chart 中必须包含 time_mode / adjusted_birth_datetime 等字段。"""
        from core.bazi_engine import build_bazi_chart
        profile = self._make_profile()
        chart = build_bazi_chart(profile)
        self.assertIn("time_mode", chart)
        self.assertIn("use_true_solar_time", chart)
        self.assertIn("true_solar_time_applied", chart)
        self.assertIn("original_birth_datetime", chart)
        self.assertIn("adjusted_birth_datetime", chart)
        self.assertIn("birth_longitude", chart)

    def test_unified_form_only_renders_longitude_when_true_solar_time_is_enabled(self):
        """高级设置关闭真太阳时后，不应继续显示或提交经度字段。"""
        path = os.path.join(ROOT, "ui", "profile_form.py")
        with open(path, "r") as f:
            source = f.read()
        unified_form = source[source.index("def _render_unified_profile_form") :]
        condition_index = unified_form.index("if use_solar_time:")
        longitude_input_index = unified_form.index('"出生地经度（东经）"')
        submit_index = unified_form.index('st.form_submit_button("生成命盘"')
        self.assertLess(condition_index, longitude_input_index)
        self.assertLess(longitude_input_index, submit_index)

        from datetime import date
        from ui.profile_form import _build_profile_payload

        profile = _build_profile_payload(
            name="Test",
            gender="男",
            calendar_label="公历",
            birth_date=date(1990, 6, 15),
            birth_hour=8,
            birth_minute=0,
            birth_place="Beijing",
            use_solar_time=False,
            birth_longitude="invalid",
        )
        self.assertIsNone(profile["birth_longitude"])
        self.assertFalse(profile["use_true_solar_time"])


if __name__ == "__main__":
    unittest.main()
