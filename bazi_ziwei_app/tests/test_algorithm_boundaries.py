import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class AlgorithmBoundaryTests(unittest.TestCase):
    """核心算法边界条件测试。"""

    def test_solar_time_correction_beijing(self):
        """北京（东经 116.4°）校正应在 ±1 分钟以内。"""
        from core.calendar_engine import _solar_time_correction
        h, m = _solar_time_correction(12, 0, 116.4)
        # 116.4 - 120 = -3.6 → offset = round(-3.6*4) = -14 分钟
        self.assertEqual((h, m), (11, 60 - 14))  # 11:46

    def test_solar_time_correction_xinjiang(self):
        """新疆（东经 75°E）校正应在 -3 小时左右。"""
        from core.calendar_engine import _solar_time_correction
        h, m = _solar_time_correction(8, 0, 75.0)
        # 75 - 120 = -45 → offset = round(-45*4) = -180 分钟 = -3 小时
        self.assertEqual((h, m), (5, 0))

    def test_solar_time_correction_tokyo(self):
        """东京（东经 139.7°E）校正应在 +79 分钟。"""
        from core.calendar_engine import _solar_time_correction
        h, m = _solar_time_correction(23, 30, 139.7)
        # 139.7 - 120 = 19.7 → offset = round(19.7*4) = 79 分钟 = 1h19m
        self.assertEqual((h, m), (0, 49))

    def test_solar_time_no_correction_default(self):
        """默认经度 120°E 时校正应为 0。"""
        from core.calendar_engine import _solar_time_correction
        h, m = _solar_time_correction(8, 30)
        self.assertEqual((h, m), (8, 30))

    def test_normalize_age_range_normal(self):
        """正常年齡區間不產生警告。"""
        from core.luck_engine import _normalize_age_range
        _, _, warning = _normalize_age_range(8, 17)
        self.assertEqual(warning, "")

    def test_normalize_age_range_negative_warning(self):
        """負數起運年齡應返回警告。"""
        from core.luck_engine import _normalize_age_range
        start, end, warning = _normalize_age_range(-1, 8)
        self.assertIn("大运起运年龄为负", warning)
        self.assertGreaterEqual(start, 0)

    def test_detect_special_pattern_cong_wang(self):
        """全部同一五行時檢測到從旺格。"""
        from core.strength_engine import _detect_special_pattern
        from core.bazi_constants import STEM_ELEMENTS
        pillars = {
            "year": {"gan": "甲", "zhi": "寅"},
            "month": {"gan": "甲", "zhi": "寅"},
            "day": {"gan": "甲", "zhi": "寅"},
            "hour": {"gan": "甲", "zhi": "寅"},
        }
        result = _detect_special_pattern(pillars, "木")
        self.assertEqual(result, "从旺")

    def test_detect_special_pattern_cong_ruo(self):
        """日主全被克泄耗時檢測到從弱格。"""
        from core.strength_engine import _detect_special_pattern
        pillars = {
            "year": {"gan": "庚", "zhi": "申"},
            "month": {"gan": "庚", "zhi": "申"},
            "day": {"gan": "甲", "zhi": "申"},
            "hour": {"gan": "庚", "zhi": "申"},
        }
        result = _detect_special_pattern(pillars, "木")
        self.assertEqual(result, "从弱")

    def test_detect_special_pattern_none(self):
        """平衡命局檢測為無特殊格局。"""
        from core.strength_engine import _detect_special_pattern
        pillars = {
            "year": {"gan": "甲", "zhi": "子"},
            "month": {"gan": "丙", "zhi": "午"},
            "day": {"gan": "甲", "zhi": "辰"},
            "hour": {"gan": "庚", "zhi": "申"},
        }
        result = _detect_special_pattern(pillars, "木")
        self.assertEqual(result, "无")

    def test_detect_special_pattern_rejects_cong_ruo_when_day_master_has_root(self):
        """占比很低但地支仍有同类根气时，不得仅凭比例判成从弱。"""
        from core.strength_engine import _detect_special_pattern

        pillars = {
            "year": {"gan": "庚", "zhi": "申"},
            "month": {"gan": "庚", "zhi": "申"},
            "day": {"gan": "甲", "zhi": "辰"},
            "hour": {"gan": "庚", "zhi": "申"},
        }

        self.assertEqual(_detect_special_pattern(pillars, "木"), "无")

    def test_strength_classification_uses_season_root_and_pressure_dimensions(self):
        from core.strength_engine import _judge_strength

        self.assertEqual(
            _judge_strength(
                0.5,
                season_score=2.0,
                root_score=2.0,
                support_score=5.0,
                pressure_score=4.5,
            ),
            "身强",
        )
        self.assertEqual(
            _judge_strength(
                -0.5,
                season_score=-3.0,
                root_score=0.0,
                support_score=3.0,
                pressure_score=3.5,
            ),
            "身弱",
        )


if __name__ == "__main__":
    unittest.main()
