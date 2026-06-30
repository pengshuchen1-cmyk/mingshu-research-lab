"""紫微盘例校验阶段测试。"""

from __future__ import annotations

import unittest


class ZiweiValidationCaseTests(unittest.TestCase):
    """盘例校验必须区分算法盘面与真实反馈，不伪造现实命中。"""

    def test_loads_three_to_five_validation_cases(self) -> None:
        from core.ziwei_validation_engine import load_ziwei_validation_cases

        cases = load_ziwei_validation_cases()

        self.assertGreaterEqual(len(cases), 3)
        self.assertLessEqual(len(cases), 5)
        for case in cases:
            self.assertIn("case_id", case)
            self.assertIn("name", case)
            self.assertIn("profile", case)
            self.assertIn("validation_scope", case)

    def test_known_chart_cases_have_expected_chart_checks(self) -> None:
        from core.ziwei_validation_engine import load_ziwei_validation_cases, validate_ziwei_case

        cases = load_ziwei_validation_cases()
        known_cases = [case for case in cases if case.get("expected")]

        self.assertGreaterEqual(len(known_cases), 2)
        for case in known_cases:
            result = validate_ziwei_case(case)
            self.assertGreaterEqual(len(result["chart_checks"]), 3)
            self.assertIn(result["chart_status"], {"盘面校验通过", "盘面需复核"})
            if result["chart_status"] == "盘面需复核":
                self.assertGreater(result["summary"]["failed_checks"], 0)

    def test_missing_real_feedback_is_marked_pending(self) -> None:
        from core.ziwei_validation_engine import load_ziwei_validation_cases, validate_ziwei_case

        cases = load_ziwei_validation_cases()
        pending_cases = [case for case in cases if not case.get("real_feedback")]

        self.assertGreaterEqual(len(pending_cases), 1)
        for case in pending_cases:
            result = validate_ziwei_case(case)
            self.assertEqual(result["feedback_status"], "待补充真实反馈")
            self.assertIn("不把待验证内容当成已验证结论", result["boundary"])

    def test_validate_all_cases_returns_summary(self) -> None:
        from core.ziwei_validation_engine import validate_ziwei_cases

        result = validate_ziwei_cases()

        self.assertIn("summary", result)
        self.assertIn("cases", result)
        self.assertGreaterEqual(result["summary"]["total_cases"], 3)
        self.assertGreaterEqual(result["summary"]["known_chart_cases"], 2)
        self.assertIn("现实反馈", result["summary"]["next_action"])

    def test_acceptance_center_exposes_validation_section(self) -> None:
        from pathlib import Path

        source = Path("ui/acceptance_page.py").read_text(encoding="utf-8")

        self.assertIn("validate_ziwei_cases", source)
        self.assertIn("紫微盘例校验", source)
        self.assertIn("真实反馈", source)


if __name__ == "__main__":
    unittest.main()
