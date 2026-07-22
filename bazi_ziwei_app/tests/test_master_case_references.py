"""Tests for real-world master case references used for calibration."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "rules" / "master_case_references.json"
SOURCE_PATH = ROOT / "rules" / "source_registry.json"
CHEN_REPORT_PATH = ROOT / "docs" / "reports" / "master_case_chen_pengshu_2026_distillation.md"
ZHOU_REPORT_PATH = ROOT / "docs" / "reports" / "master_case_zhou_huimin_2026_distillation.md"


class MasterCaseReferenceTests(unittest.TestCase):
    def setUp(self):
        with CASE_PATH.open(encoding="utf-8") as f:
            self.data = json.load(f)
        with SOURCE_PATH.open(encoding="utf-8") as f:
            self.sources = json.load(f)
        with (ROOT / "rules" / "monthly_event_ontology.json").open(encoding="utf-8") as f:
            self.ontology = json.load(f)

    def test_chen_pengshu_2026_case_is_registered(self):
        cases = self.data.get("rules", [])
        case = next((item for item in cases if item.get("case_id") == "chen_pengshu_2026_master_monthly"), None)
        self.assertIsNotNone(case)
        self.assertEqual(case.get("profile_name"), "陈芃澍")
        self.assertEqual(case.get("year"), 2026)
        self.assertEqual(case.get("bazi_pillars"), ["辛巳", "乙未", "壬申", "己卯"])
        self.assertIn("/Users/uni/Downloads/6959.JPG", case.get("image_paths", []))
        self.assertIn("master_case_chen_pengshu_2026", case.get("source_ids", []))

    def test_master_source_is_registered(self):
        self.assertIn("master_case_chen_pengshu_2026", self.sources)
        source = self.sources["master_case_chen_pengshu_2026"]
        self.assertEqual(source.get("category"), "命例参考")
        self.assertIn("真实师傅流月样本", source.get("used_for", []))

    def test_zhou_huimin_2026_case_is_registered(self):
        cases = self.data.get("rules", [])
        case = next((item for item in cases if item.get("case_id") == "zhou_huimin_2026_master_monthly"), None)
        self.assertIsNotNone(case)
        self.assertEqual(case.get("profile_name"), "周惠敏")
        self.assertEqual(case.get("year"), 2026)
        self.assertEqual(case.get("bazi_pillars"), ["甲寅", "戊戌", "己丑", "庚午"])
        self.assertIn("/Users/uni/Downloads/6229.JPG", case.get("image_paths", []))
        self.assertIn("master_case_zhou_huimin_2026", case.get("source_ids", []))
        self.assertIn(4, case.get("profile_match", {}).get("known_profile_ids", []))

    def test_zhou_master_source_is_registered(self):
        self.assertIn("master_case_zhou_huimin_2026", self.sources)
        source = self.sources["master_case_zhou_huimin_2026"]
        self.assertEqual(source.get("category"), "命例参考")
        self.assertIn("真实师傅流月样本", source.get("used_for", []))

    def test_case_has_six_two_month_periods_with_event_mapping(self):
        expected_ranges = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]]
        for case in self.data.get("rules", []):
            periods = case.get("monthly_periods", [])
            self.assertEqual(len(periods), 6, case.get("case_id"))
            self.assertEqual([item.get("months") for item in periods], expected_ranges)
            for period in periods:
                with self.subTest(case=case.get("case_id"), period=period.get("months")):
                    self.assertGreaterEqual(len(period.get("confirmed_notes", [])), 3)
                    self.assertGreaterEqual(len(period.get("mapped_event_types", [])), 3)
                    self.assertGreaterEqual(len(period.get("distilled_reasoning", [])), 2)
                    self.assertIn(period.get("confidence"), {"high", "medium", "low"})

    def test_case_keeps_uncertain_transcription_out_of_hard_rules(self):
        for case in self.data.get("rules", []):
            self.assertTrue(case.get("calibration_policy", {}).get("do_not_override_main_rules"))
            for period in case.get("monthly_periods", []):
                self.assertIn("needs_user_review", period)
                self.assertIsInstance(period.get("needs_user_review"), list)

    def test_mapped_event_types_exist_in_event_ontology(self):
        for case in self.data.get("rules", []):
            for period in case.get("monthly_periods", []):
                for event_type in period.get("mapped_event_types", []):
                    with self.subTest(case=case.get("case_id"), period=period.get("period_id"), event_type=event_type):
                        self.assertIn(event_type, self.ontology)

    def test_zhou_sample_promotes_dangling_terms_to_event_types(self):
        case = next(item for item in self.data.get("rules", []) if item.get("case_id") == "zhou_huimin_2026_master_monthly")
        mapped = {event_type for period in case.get("monthly_periods", []) for event_type in period.get("mapped_event_types", [])}
        required = {
            "sudden_change_warning",
            "trapped_commitment",
            "short_term_cooperation",
            "female_friend_social",
            "business_procedure_handling",
            "child_family_responsibility",
            "partner_tolerance",
        }
        self.assertTrue(required <= mapped)
        self.assertTrue(required <= set(self.ontology))

    def test_chen_distillation_report_exists_and_names_key_patterns(self):
        text = CHEN_REPORT_PATH.read_text(encoding="utf-8")
        required_terms = [
            "酒友",
            "开车",
            "项目",
            "招募合作",
            "资金会被套住",
            "防破财",
            "忽然有奇迹",
            "小心小人",
            "房、店、车",
            "110",
            "逢财置物",
        ]
        for term in required_terms:
            self.assertIn(term, text)

    def test_chen_dialogue_learning_records_growth_power_without_storage(self):
        case = next(item for item in self.data.get("rules", []) if item.get("case_id") == "chen_pengshu_2026_master_monthly")
        notes = case.get("dialogue_learning_notes", [])

        self.assertGreaterEqual(len(notes), 1)
        note = notes[-1]
        self.assertEqual(note.get("topic"), "天干十二长生有生旺无墓库")
        self.assertIn("己土", note.get("stems_reviewed", {}))
        self.assertEqual(note["stems_reviewed"]["己土"]["growth"], "巳")
        self.assertEqual(note["stems_reviewed"]["己土"]["storage"], "丑")
        self.assertEqual(note["stems_reviewed"]["壬水"]["growth"], "申")
        self.assertEqual(note["stems_reviewed"]["壬水"]["storage"], "辰")
        self.assertEqual(note["stems_reviewed"]["辛金"]["prosperity"], "申")
        self.assertEqual(note["stems_reviewed"]["辛金"]["storage"], "辰")
        self.assertEqual(note["stems_reviewed"]["乙木"]["storage"], "未")
        self.assertIn("财印官有生旺但缺归库", note.get("research_tags", []))
        self.assertIn("后天造库", note.get("practical_calibration", ""))

    def test_zhou_distillation_report_exists_and_names_key_patterns(self):
        text = ZHOU_REPORT_PATH.read_text(encoding="utf-8")
        required_terms = [
            "2号、12号、22号",
            "110",
            "有项目",
            "不投资",
            "买房买车",
            "情感问题",
            "被套住",
            "焦虑",
            "签字",
            "短合",
            "闺蜜",
            "办业务",
            "子女事",
            "内耗状态",
            "女神太太",
        ]
        for term in required_terms:
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
