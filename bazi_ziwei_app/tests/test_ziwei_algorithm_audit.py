"""紫微算法复核测试。"""

from __future__ import annotations

import unittest


class ZiweiAlgorithmAuditTests(unittest.TestCase):
    """复核五行局、十四主星、辅星煞星和大限。"""

    def test_year_branch_uses_birth_year_not_year_gan_shortcut(self) -> None:
        from core.ziwei_engine import build_ziwei_chart

        chart = build_ziwei_chart({
            "name": "年支复核",
            "gender": "女",
            "birth_date": "2000-06-15",
            "birth_hour": 14,
            "birth_minute": 30,
        })

        self.assertEqual(chart.get("year_gan"), "庚")
        self.assertEqual(chart.get("year_branch"), "辰")

    def test_validation_case_b_five_element_bureau_is_resolved(self) -> None:
        from core.ziwei_validation_engine import load_ziwei_validation_cases, validate_ziwei_case

        cases = load_ziwei_validation_cases()
        case_b = next(case for case in cases if case["case_id"] == "zw_known_b")
        result = validate_ziwei_case(case_b)

        self.assertEqual(case_b["expected"]["five_element_bureau"], "土5局")
        self.assertEqual(result["chart_status"], "盘面校验通过")
        self.assertIn("丁亥", result["chart"].get("algorithm_evidence", [""])[0])

    def test_algorithm_audit_summarizes_core_modules(self) -> None:
        from core.ziwei_algorithm_audit import audit_ziwei_algorithms

        audit = audit_ziwei_algorithms()

        self.assertIn("summary", audit)
        self.assertIn("five_element_review", audit)
        self.assertIn("main_star_review", audit)
        self.assertIn("minor_fierce_review", audit)
        self.assertIn("daxian_review", audit)
        self.assertGreaterEqual(audit["summary"]["known_cases"], 2)
        self.assertIn("样例B", " ".join(audit["summary"]["resolved_issues"]))

    def test_fierce_and_daxian_audit_has_boundaries(self) -> None:
        from core.ziwei_algorithm_audit import audit_ziwei_algorithms

        audit = audit_ziwei_algorithms()
        text = str(audit)

        self.assertIn("辅星", text)
        self.assertIn("煞星", text)
        self.assertIn("大限", text)
        self.assertIn("仍需真实盘例继续校验", text)


if __name__ == "__main__":
    unittest.main()
