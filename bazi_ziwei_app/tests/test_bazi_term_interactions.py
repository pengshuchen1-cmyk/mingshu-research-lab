"""个人摘要术语按钮的真实交互与安全展示契约。"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "ui" / "life_overview_page.py"
STYLES_PATH = ROOT / "ui" / "styles.py"


def test_collect_term_ids_combines_identity_terms_and_recognized_evidence_once():
    from core.bazi_term_glossary import collect_term_ids

    result = collect_term_ids(
        ["day-master", "strength", "day-master"],
        ["财星2个，正财与偏财都有。", "正财落月柱；印星提供学习支持。"],
    )

    assert result == [
        "day-master",
        "strength",
        "wealth-star",
        "ten-god-direct-wealth",
        "ten-god-indirect-wealth",
        "resource-star",
    ]


def test_one_real_click_immediately_marks_the_only_expanded_term():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string(
        """
from ui.life_overview_page import _render_term_dictionary
_render_term_dictionary(["day-master", "wealth-star"], chart=None)
"""
    ).run()

    app.button[1].click().run()

    assert [button.label for button in app.button] == ["日主", "✓ 财星 · 已展开"]
    assert sum('class="ms-term-detail"' in item.value for item in app.markdown) == 1


def test_term_detail_escapes_every_dynamic_value_before_html_render(monkeypatch):
    import ui.life_overview_page as page

    rendered: list[str] = []
    monkeypatch.setattr(page, "build_term_view", lambda *_args, **_kwargs: {
        "term_id": "wealth-star",
        "label": "<财星>",
        "definition": "<script>alert(1)</script>",
        "observation_scope": "收入 & 资源",
        "boundary": '不能替代 "现实决策"',
    })
    monkeypatch.setattr(page.st, "markdown", lambda body, **_kwargs: rendered.append(str(body)))

    page._render_term_detail("wealth-star", chart=None)

    html = rendered[-1]
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "收入 &amp; 资源" in html
    assert "&quot;现实决策&quot;" in html


def test_base_term_detail_renders_semantic_fact_labels_not_ten_god_counts(monkeypatch):
    import ui.life_overview_page as page

    chart = {
        "day_master": "甲",
        "pillars": {
            "year": {"gan": "戊", "zhi": "辰"},
            "month": {"gan": "己", "zhi": "丑"},
            "day": {"gan": "甲", "zhi": "子"},
            "hour": {"gan": "丙", "zhi": "寅"},
        },
        "day_master_strength": {
            "strength": "身弱",
            "favorable_elements": ["水", "木"],
            "unfavorable_elements": ["火", "土"],
        },
        "ten_god_counts": {"偏财": 2, "正财": 2, "比肩": 2, "食神": 1, "正印": 1},
        "five_elements": {"木": 2, "火": 1, "土": 4, "金": 0, "水": 1},
        "ten_gods": {
            "year": {"gan": "偏财"},
            "month": {"gan": "正财"},
            "day": {"gan": "比肩"},
            "hour": {"gan": "食神"},
        },
        "hidden_stems": {"year": [], "month": [], "day": [], "hour": []},
        "pattern_analysis": {"pattern": "正财格"},
    }
    rendered: list[str] = []
    monkeypatch.setattr(page.st, "markdown", lambda body, **_kwargs: rendered.append(str(body)))

    page._render_term_detail("strength-weak", chart)

    html = rendered[-1]
    assert "当前判断" in html
    assert "身弱" in html
    assert "出现数量" not in html
    assert "所在位置" not in html


def test_page_uses_streamlit_buttons_and_accessible_term_styles():
    page_source = PAGE_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    assert "_render_term_dictionary(" in page_source
    assert "st.button(" in page_source
    assert "ms-term-detail" in page_source
    assert "ms-term-detail" in styles
    assert "ms_term_button_" in page_source
    assert "min-height: 44px" in styles
    assert "margin-bottom: 8px" in styles
    assert "focus-visible" in styles
    assert "aria-expanded" in page_source
    assert "aria-controls" in page_source
    assert "restore_focus_to" in page_source
    assert "scrollWidth" not in page_source
    assert "max-width: 100%" in styles
    assert "overflow-wrap: anywhere" in styles
    assert "点击术语查看定义与命盘中的对应信息；同一时间只展开一项。" in page_source
    assert "查看定义与命盘中的具体位置" not in page_source


def test_dom_semantics_script_sets_aria_controls_and_restores_focus(monkeypatch):
    import ui.life_overview_page as page

    rendered_scripts: list[str] = []
    monkeypatch.setattr(
        page.components,
        "html",
        lambda body, **_kwargs: rendered_scripts.append(str(body)),
    )

    page._sync_term_button_semantics(
        [
            {"term_id": "day-master", "label": "日主"},
            {"term_id": "wealth-star", "label": "财星"},
        ],
        active_term_id="wealth-star",
        restore_focus_to="term-chip-day-master",
    )

    script = rendered_scripts[-1]
    assert 'setAttribute("aria-expanded"' in script
    assert 'setAttribute("aria-controls"' in script
    assert 'button.focus({ preventScroll: true })' in script
    assert "term-detail-wealth-star" in script
    assert "term-chip-day-master" in script
