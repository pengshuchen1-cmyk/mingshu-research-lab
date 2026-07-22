"""Calibration audit between the Chen Pengshu master case and system Top 3."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class MasterCaseCalibrationAuditTests(unittest.TestCase):
    def test_builds_six_period_comparisons_against_current_top3(self):
        from tools.master_case_calibration_audit import build_master_case_calibration

        audit = build_master_case_calibration("chen_pengshu_2026_master_monthly")

        self.assertEqual("chen_pengshu_2026_master_monthly", audit["case_id"])
        self.assertEqual("陈芃澍", audit["profile_name"])
        self.assertEqual(2026, audit["year"])
        self.assertEqual(12, len(audit["system_months"]))
        self.assertEqual(6, len(audit["period_comparisons"]))

        for period in audit["period_comparisons"]:
            with self.subTest(period=period["period_id"]):
                self.assertIn("master_event_types", period)
                self.assertIn("system_top3_event_types", period)
                self.assertIn("exact_hit_event_types", period)
                self.assertIn("semantic_hit_event_types", period)
                self.assertIn("missed_event_types", period)
                self.assertGreaterEqual(period["coverage_rate"], 0)
                self.assertLessEqual(period["coverage_rate"], 1)
                self.assertGreaterEqual(len(period["tuning_recommendations"]), 1)

        missed = [
            event_type
            for period in audit["period_comparisons"]
            for event_type in period["missed_event_types"]
        ]
        self.assertGreater(len(set(missed)), 0)

    def test_writes_markdown_report_with_period_hits_and_misses(self):
        from tools.master_case_calibration_audit import (
            build_master_case_calibration,
            write_calibration_report,
        )

        audit = build_master_case_calibration("chen_pengshu_2026_master_monthly")
        report_path = write_calibration_report(audit)
        text = report_path.read_text(encoding="utf-8")

        self.assertIn("陈芃澍 2026 流月样本校准审计", text)
        self.assertIn("1-2 月", text)
        self.assertIn("3-4 月", text)
        self.assertIn("命中", text)
        self.assertIn("漏项", text)
        self.assertIn("调权建议", text)
        self.assertIn("合作机会", text)
        self.assertIn("酒友", text)
        self.assertIn("房、店、车", text)
        self.assertIn("110", text)
        self.assertNotIn("{'event_type'", text)

    def test_master_case_calibration_improves_key_gap_period(self):
        from tools.master_case_calibration_audit import build_master_case_calibration

        audit = build_master_case_calibration("chen_pengshu_2026_master_monthly")
        periods = {item["period_id"]: item for item in audit["period_comparisons"]}

        self.assertGreaterEqual(audit["overall"]["average_coverage_rate"], 0.72)
        self.assertGreaterEqual(periods["2026_m05_m06"]["coverage_rate"], 0.4)
        self.assertLess(
            len(periods["2026_m05_m06"]["missed_event_types"]),
            len(periods["2026_m05_m06"]["master_event_types"]),
        )

    def test_master_case_combination_weight_rules_exist(self):
        import json

        path = ROOT / "rules" / "master_case_combination_weights.json"
        self.assertTrue(path.exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("rules", data)
        case_ids = {item.get("case_id") for item in data.get("rules", [])}
        self.assertIn("chen_pengshu_2026_master_monthly", case_ids)
        self.assertIn("zhou_huimin_2026_master_monthly", case_ids)
        for item in data.get("rules", []):
            with self.subTest(pattern=item.get("pattern_id")):
                self.assertGreaterEqual(len(item.get("primary_events", [])), 2)
                self.assertGreaterEqual(float(item.get("score_bonus", 0)), 8)
                self.assertTrue(item.get("source_ids"))
                self.assertTrue(item.get("distilled_logic"))

    def test_zhou_master_case_combination_weights_raise_key_period_coverage(self):
        from tools.master_case_calibration_audit import build_master_case_calibration

        audit = build_master_case_calibration("zhou_huimin_2026_master_monthly")
        periods = {item["period_id"]: item for item in audit["period_comparisons"]}

        self.assertGreaterEqual(audit["overall"]["average_coverage_rate"], 0.68)
        self.assertGreaterEqual(periods["2026_m01_m02"]["coverage_rate"], 0.55)
        self.assertGreaterEqual(periods["2026_m09_m10"]["coverage_rate"], 0.70)
        self.assertGreaterEqual(periods["2026_m11_m12"]["coverage_rate"], 0.60)
        self.assertIn("sudden_change_warning", periods["2026_m01_m02"]["system_semantic_event_types"])
        self.assertIn("business_procedure_handling", periods["2026_m09_m10"]["system_semantic_event_types"])
        self.assertIn("partner_tolerance", periods["2026_m11_m12"]["system_semantic_event_types"])

    def test_chen_master_case_combination_weights_do_not_regress(self):
        from tools.master_case_calibration_audit import build_master_case_calibration

        audit = build_master_case_calibration("chen_pengshu_2026_master_monthly")
        self.assertGreaterEqual(audit["overall"]["average_coverage_rate"], 0.72)

    def test_zhou_huimin_case_can_be_audited_and_reported(self):
        from tools.master_case_calibration_audit import (
            build_master_case_calibration,
            write_calibration_report,
        )

        audit = build_master_case_calibration("zhou_huimin_2026_master_monthly")
        report_path = write_calibration_report(audit)
        text = report_path.read_text(encoding="utf-8")

        self.assertEqual("zhou_huimin_2026_master_monthly", audit["case_id"])
        self.assertEqual("周惠敏", audit["profile_name"])
        self.assertEqual(12, len(audit["system_months"]))
        self.assertEqual(6, len(audit["period_comparisons"]))
        self.assertIn("周惠敏 2026 流月样本校准审计", text)
        self.assertIn("110", text)
        self.assertIn("买房买车", text)
        self.assertIn("被套住", text)
        self.assertIn("签字", text)
        self.assertIn("闺蜜", text)
        self.assertIn("办业务", text)
        self.assertIn("子女事", text)
        self.assertNotIn("{'event_type'", text)


if __name__ == "__main__":
    unittest.main()
