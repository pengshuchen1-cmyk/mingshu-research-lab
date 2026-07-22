from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ai_question_page_has_chat_controls_and_safe_limits():
    source = (ROOT / "ui" / "inquiry_page.py").read_text(encoding="utf-8")

    assert "st.chat_message" in source
    assert "st.chat_input" in source
    assert "清空对话" in source
    assert "validate_question" in source
    assert "render_rule_summary" in source
    assert "新建命盘" in source
    assert "repr(exc)" not in source
    assert "str(exc)" not in source


def test_ai_question_page_is_reachable_from_product_navigation():
    import app

    assert app.get_pages()["AI问答"].__name__ == "render_inquiry_page"
    assert ("问答", "AI问答") in app.PRODUCT_NAV_ITEMS
