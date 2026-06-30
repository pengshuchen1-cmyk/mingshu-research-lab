"""紫微人生说明书报告测试。"""

from __future__ import annotations

import json
import unittest


FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


def sample_profile() -> dict:
    return {
        "name": "紫微说明书测试",
        "gender": "女",
        "birth_date": "1993-03-15",
        "birth_hour": 10,
        "birth_minute": 0,
        "birth_place": "杭州",
    }


class ZiweiLifeManualReportTests(unittest.TestCase):
    """紫微报告要从术语列表升级为普通用户能读的人生说明书。"""

    def test_report_contains_five_life_manual_topics(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        report = generate_ziwei_report(build_ziwei_chart(sample_profile()))
        text = json.dumps(report, ensure_ascii=False)

        self.assertIn("紫微人生说明书", text)
        for title in ["事业说明书", "财富说明书", "关系说明书", "迁移说明书", "福德说明书"]:
            self.assertIn(title, text)

    def test_each_life_manual_topic_uses_plain_sections(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        report = generate_ziwei_report(build_ziwei_chart(sample_profile()))
        manual_sections = [
            section for section in report.get("sections", [])
            if section.get("title") in {"事业说明书", "财富说明书", "关系说明书", "迁移说明书", "福德说明书"}
        ]

        self.assertEqual(len(manual_sections), 5)
        for section in manual_sections:
            text = section.get("text", "")
            for phrase in ["这代表什么", "现实里怎么看", "优势", "需要注意", "行动建议", "命盘依据"]:
                self.assertIn(phrase, text)

    def test_life_manual_has_no_forbidden_absolute_words(self) -> None:
        from core.ziwei_engine import build_ziwei_chart
        from report.ziwei_report import generate_ziwei_report

        report = generate_ziwei_report(build_ziwei_chart(sample_profile()))
        text = json.dumps(report, ensure_ascii=False)

        for word in FORBIDDEN:
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
