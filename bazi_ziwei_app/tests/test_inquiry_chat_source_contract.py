from __future__ import annotations


def test_answer_source_labels_are_explicit_and_stable():
    from ui.inquiry_page import answer_source_label

    assert answer_source_label("cloud_validated") == "AI综合分析·本地规则校验"
    assert answer_source_label("local_rules") == "本地规则分析"
    assert answer_source_label("unexpected") == "本地规则分析"


def test_suggested_questions_cover_primary_customer_domains():
    from ui.inquiry_page import SUGGESTED_QUESTIONS

    text = "\n".join(SUGGESTED_QUESTIONS)
    for keyword in ("强弱", "财运", "事业", "姻缘", "未来一年"):
        assert keyword in text
