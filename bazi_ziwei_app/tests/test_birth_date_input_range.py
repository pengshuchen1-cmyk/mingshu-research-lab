"""出生日期输入范围测试 — v1.1-B-Fix-InputDate"""

from __future__ import annotations

import os, unittest
from datetime import date

from utils.validators import validate_profile


class TestBirthDateInputRange(unittest.TestCase):
    """验证出生日期选择范围正确性。"""

    def test_profile_form_max_value_is_today(self):
        """profile_form.py 中 date_input 的 max_value 应为 date.today()。"""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "profile_form.py")
        with open(path, "r") as f:
            text = f.read()
        self.assertIn("max_value=date.today()", text,
                      "profile_form.py 应包含 max_value=date.today()")

    def test_unified_profile_form_keeps_full_supported_date_range(self):
        """一页式表单仍允许选择 1900 年起至今日的出生日期。"""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "profile_form.py")
        with open(path, "r") as f:
            text = f.read()
        self.assertIn("def _render_unified_profile_form", text)
        self.assertIn("min_value=date(1900, 1, 1)", text)
        self.assertIn("max_value=date.today()", text)

    def test_archive_page_max_value_is_today(self):
        """archive_page.py 中 date_input 的 max_value 应为 date.today()。"""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "archive_page.py")
        with open(path, "r") as f:
            text = f.read()
        self.assertIn("max_value=date.today()", text,
                      "archive_page.py 应包含 max_value=date.today()")

    def test_validate_profile_forbid_future_date(self):
        """validate_profile 应拒绝未来日期。"""
        future_profile = {
            "name": "Future",
            "gender": "男",
            "birth_date": "2099-12-31",
            "birth_hour": 10,
            "birth_minute": 0,
        }
        ok, msg = validate_profile(future_profile)
        self.assertFalse(ok, "未来日期应被拒绝")

    def test_validate_profile_accept_past_date(self):
        """validate_profile 应接受过去日期。"""
        ok, msg = validate_profile({
            "name": "Past",
            "gender": "男",
            "birth_date": "2005-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
        })
        self.assertTrue(ok, f"过去日期应被接受: {msg}")

    def test_build_bazi_chart_2005_01_01(self):
        """2005-01-01 可正常生成四柱。"""
        from core.bazi_engine import build_bazi_chart
        prof = {"name": "T", "gender": "男", "birth_date": "2005-01-01",
                "birth_hour": 10, "birth_minute": 30, "birth_place": "Beijing"}
        chart = build_bazi_chart(prof)
        self.assertNotIn("error", chart,
                         f"2005-01-01 应可生成四柱: {chart.get('error')}")
        self.assertIn("pillars", chart)

    def test_build_bazi_chart_2005_06_15(self):
        """2005-06-15 可正常生成四柱。"""
        from core.bazi_engine import build_bazi_chart
        prof = {"name": "T", "gender": "女", "birth_date": "2005-06-15",
                "birth_hour": 14, "birth_minute": 30, "birth_place": "Shanghai"}
        chart = build_bazi_chart(prof)
        self.assertNotIn("error", chart,
                         f"2005-06-15 应可生成四柱: {chart.get('error')}")

    def test_build_bazi_chart_2005_12_31(self):
        """2005-12-31 可正常生成四柱。"""
        from core.bazi_engine import build_bazi_chart
        prof = {"name": "T", "gender": "男", "birth_date": "2005-12-31",
                "birth_hour": 23, "birth_minute": 0, "birth_place": "Beijing"}
        chart = build_bazi_chart(prof)
        self.assertNotIn("error", chart,
                         f"2005-12-31 应可生成四柱: {chart.get('error')}")

    def test_lunar_year_2005_conversion(self):
        """农历 2005 年输入可正常转换。"""
        from lunar_python import Lunar
        try:
            lunar = Lunar.fromYmd(2005, 2, 15)
            solar = lunar.getSolar()
            self.assertIsNotNone(solar)
            self.assertEqual(solar.getYear(), 2005)
        except Exception as exc:
            self.fail(f"农历 2005 年转换失败: {exc}")


if __name__ == "__main__":
    unittest.main()
