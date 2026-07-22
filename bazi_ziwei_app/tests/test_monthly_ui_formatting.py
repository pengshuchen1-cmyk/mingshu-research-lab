import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class MonthlyUiFormattingTests(unittest.TestCase):
    def test_dict_fields_are_not_rendered_as_raw_python_text(self):
        from ui.yearly_page import format_monthly_event_for_display

        event = {
            "event_type": "contract_document",
            "label": "合同文书/文件审批",
            "probability_level": "较高",
            "reason": "官杀或文书规则被引动。",
            "trigger_factors": ["十神<正官>主事件池"],
            "advice": "重要事项建议落到文字。",
            "source_ids": ["sanming_tonghui"],
            "score": 70,
        }

        text = format_monthly_event_for_display(event)

        forbidden = [
            "{'event_type'",
            "'source_ids'",
            "'trigger_factors'",
            "probability_level':",
            "'score'",
            "🔴",
            "🟡",
            "🟢",
            "💡",
        ]
        for word in forbidden:
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
