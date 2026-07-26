"""Tests for customer bazi reference cases."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "tests" / "fixtures" / "bazi_reference_cases.json"


class BaziReferenceCaseTests(unittest.TestCase):
    def setUp(self):
        with CASE_PATH.open(encoding="utf-8") as f:
            self.data = json.load(f)

    def _case(self, case_id: str) -> dict:
        return next((item for item in self.data.get("cases", []) if item.get("case_id") == case_id), {})

    def test_tang_rui_reference_case_is_registered(self):
        case = self._case("bazi_ref_tang_rui_1997_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "唐瑞")
        self.assertEqual(case.get("profile", {}).get("gender"), "女")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "1997-07-17")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "庚申")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "庚")

    def test_xie_xin_reference_case_is_registered(self):
        case = self._case("bazi_ref_xie_xin_2000_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "谢昕")
        self.assertEqual(case.get("profile", {}).get("gender"), "女")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "lunar")
        self.assertEqual(case.get("profile", {}).get("lunar_birth_date"), "2000-07-11")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "2000-08-10")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "庚子")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "庚")
        self.assertEqual(case.get("standard_time_chart", {}).get("pattern"), "建禄格")

    def test_wang_weiheng_reference_case_is_registered(self):
        case = self._case("bazi_ref_wang_weiheng_1996_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "王伟蘅")
        self.assertEqual(case.get("profile", {}).get("gender"), "男")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "solar")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "1996-08-28")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "丙子")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "丙申")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "丁酉")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "戊申")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "丁")
        self.assertEqual(case.get("standard_time_chart", {}).get("pattern"), "正财格")
        self.assertIn("财星桃花重", case.get("research_tags", []))

    def test_zhang_qizheng_reference_case_is_registered(self):
        case = self._case("bazi_ref_zhang_qizheng_2003_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "张齐正")
        self.assertEqual(case.get("profile", {}).get("gender"), "男")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "solar")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "2003-11-26")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "癸未")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "癸亥")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "癸卯")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "庚申")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "癸")
        self.assertEqual(case.get("standard_time_chart", {}).get("pattern"), "月刃格")
        self.assertIn("水旺身强", case.get("research_tags", []))

    def test_shuai_weixuan_ordinary_reference_case_is_registered(self):
        case = self._case("bazi_ref_shuai_weixuan_1985_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "帅伟轩")
        self.assertEqual(case.get("profile", {}).get("gender"), "男")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "1985-01-28")
        self.assertEqual(case.get("profile", {}).get("birth_time_label"), "辰时")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "甲子")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "丁丑")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "丁卯")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "甲辰")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "丁")
        self.assertIn("普通盘", case.get("research_tags", []))
        self.assertEqual(case.get("grade_reference", {}).get("classical_grade"), "中等偏普通")

    def test_zhang_xusen_pressure_reference_case_is_registered(self):
        case = self._case("bazi_ref_zhang_xusen_2001_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "张旭森")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "lunar")
        self.assertEqual(case.get("profile", {}).get("lunar_birth_date"), "2000-12-28")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "2001-01-22")
        self.assertEqual(case.get("profile", {}).get("birth_time_label"), "辰时")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "庚辰")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "己丑")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "乙酉")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "庚辰")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "乙")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master_strength"), "身弱")
        self.assertIn("身弱财官重", case.get("research_tags", []))
        self.assertIn("现实压力型", case.get("research_tags", []))

    def test_liu_man_pattern_reference_case_is_registered(self):
        case = self._case("bazi_ref_liu_man_1994_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "刘曼")
        self.assertEqual(case.get("profile", {}).get("gender"), "女")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "lunar")
        self.assertEqual(case.get("profile", {}).get("lunar_birth_date"), "1994-11-28")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "1994-12-30")
        self.assertEqual(case.get("profile", {}).get("birth_time_label"), "亥时")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "甲戌")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "丙子")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "庚寅")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "丁亥")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "庚")
        self.assertEqual(case.get("standard_time_chart", {}).get("pattern"), "伤官格带财官")
        self.assertIn("身弱有根", case.get("research_tags", []))
        self.assertIn("女命官杀透出", case.get("research_tags", []))

    def test_ren_yujie_night_zi_reference_case_is_registered(self):
        case = self._case("bazi_ref_ren_yujie_1996_2026")
        self.assertTrue(case)
        self.assertEqual(case.get("name"), "任昱洁")
        self.assertEqual(case.get("profile", {}).get("gender"), "女")
        self.assertEqual(case.get("profile", {}).get("calendar_type"), "solar")
        self.assertEqual(case.get("profile", {}).get("birth_date"), "1996-09-04")
        self.assertEqual(case.get("profile", {}).get("birth_time_label"), "夜子时")
        self.assertEqual(case.get("time_calibration", {}).get("night_zi_rule"), "23点后按次日日柱起时")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("year"), "丙子")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("month"), "丙申")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("day"), "乙巳")
        self.assertEqual(case.get("standard_time_chart", {}).get("pillars", {}).get("hour"), "丙子")
        self.assertEqual(case.get("standard_time_chart", {}).get("day_master"), "乙")
        self.assertEqual(case.get("standard_time_chart", {}).get("pattern"), "正官格带伤官")
        self.assertIn("夜子时五鼠遁校准", case.get("research_tags", []))
        self.assertIn("伤官见官", case.get("research_tags", []))
        self.assertIn("6月冲中有财", case.get("distilled_2026_monthly_report", {}).get("key_corrections", []))
        self.assertIn("11月巳亥冲", case.get("distilled_2026_monthly_report", {}).get("key_corrections", []))

    def test_standard_and_true_solar_hour_pillars_are_kept_for_calibration(self):
        case = self._case("bazi_ref_tang_rui_1997_2026")
        self.assertEqual(case["standard_time_chart"]["pillars"]["hour"], "辛巳")
        self.assertEqual(case["true_solar_time_chart_reference"]["pillars"]["hour"], "庚辰")
        self.assertEqual(case["time_calibration"]["standard_time_hour_branch"], "巳")
        self.assertEqual(case["time_calibration"]["true_solar_time_hour_branch"], "辰")

    def test_2026_monthly_reference_has_twelve_months(self):
        for case in self.data.get("cases", []):
            months = case.get("year_2026_monthly_events", [])
            self.assertEqual([item.get("month") for item in months], list(range(1, 13)), case.get("case_id"))
            for item in months:
                self.assertGreaterEqual(len(item.get("main_events", [])), 3)
                self.assertTrue(item.get("pillar"))
                self.assertTrue(item.get("note"))

    def test_reference_case_has_sources_and_usage_policy(self):
        for case in self.data.get("cases", []):
            self.assertGreaterEqual(len(case.get("source_ids", [])), 3)
            self.assertTrue(case.get("usage_policy", {}).get("do_not_override_main_rules"))
            self.assertIn("健康内容不得替代医学诊断或治疗建议", case.get("usage_policy", {}).get("risk_control", []))


if __name__ == "__main__":
    unittest.main()
