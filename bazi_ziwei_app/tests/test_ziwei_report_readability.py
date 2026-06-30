"""紫微报告可读性与边界测试。"""

from __future__ import annotations

import json
import unittest


FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


def sample_profile() -> dict:
    return {
        "name": "紫微报告测试",
        "gender": "女",
        "birth_date": "1993-03-15",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "杭州",
    }


class ZiweiReportReadabilityTests(unittest.TestCase):
    """紫微报告也要像说明书，而不是术语清单。"""

    def test_report_uses_plain_guide_sections(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        report = generate_ziwei_report(build_ziwei_chart(sample_profile()))
        text = json.dumps(report, ensure_ascii=False)

        for phrase in ["命宫说明", "身宫说明", "事业宫说明", "财帛宫说明", "夫妻宫说明"]:
            self.assertIn(phrase, text)
        for phrase in ["一句话先懂", "生活里怎么看", "可以怎么做", "边界提醒"]:
            self.assertIn(phrase, text)
        self.assertIn("主星落宫怎么看", text)

    def test_report_contains_capability_boundary_without_forbidden_words(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        report = generate_ziwei_report(build_ziwei_chart(sample_profile()))
        text = json.dumps(report, ensure_ascii=False)

        self.assertIn("算法完成度说明", text)
        self.assertIn("飞化", text)
        self.assertIn("紫微流年流月", text)
        self.assertIn("不会把未接入内容包装成结论", text)
        for word in FORBIDDEN:
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
