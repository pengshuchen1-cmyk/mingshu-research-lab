import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(name: str) -> str:
    return (ROOT / "ui" / name).read_text(encoding="utf-8")


def test_homepage_renders_one_immersive_hero_in_reading_order():
    tree = ast.parse(_source("homepage_components.py"))
    render = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "render_homepage_landing"
    )
    calls = [
        node.func.id
        for node in sorted(ast.walk(render), key=lambda item: getattr(item, "lineno", 0))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id.startswith("_render")
    ]
    assert calls == ["_render_immersive_hero"]


def test_homepage_uses_project_owned_background_and_origin_inspired_copy():
    source = _source("homepage_components.py")

    assert 'assets" / "hero-sky-v1.png"' in source
    assert "useorigin.com" not in source
    assert "<em>看见</em>你的命数。" in source
    assert "从命盘出发，回答此刻真正关心的问题。" in source
    assert "本地排盘 · 隐私优先 · 结论仅供参考" in source


def test_homepage_uses_one_shadcn_input_and_one_submit_button():
    source = _source("homepage_components.py")

    assert "import streamlit_shadcn_ui as shadcn" in source
    assert "shadcn.input(" in source
    assert "shadcn.badge(" not in source
    assert source.count("shadcn.button(") == 1
    assert '"↑"' in source
    assert 'max_length=2000' in source
    assert 'width="stretch"' in source


def test_homepage_exposes_only_the_three_typewriter_questions():
    source = _source("homepage_components.py")

    assert "今天我的运势如何？" in source
    assert "如何推算我的命盘？" in source
    assert "今年是我的本命年，我的事业和爱情怎么样？" in source
    assert "TYPEWRITER_QUESTIONS" in source
    assert "或者从一个常见问题开始" not in source


def test_homepage_queues_questions_for_existing_ai_route():
    source = _source("homepage_components.py")

    assert "PENDING_QUESTION_KEY" in source
    assert 'st.session_state["navigate_to"] = "AI问答"' in source
    assert "st.rerun()" in source
    assert "len(normalized) > 2000" in source


def test_homepage_glass_visual_contract_is_scoped_and_responsive():
    css = _source("homepage_styles.py")

    for token in [
        'body:has(.st-key-ms2-home)',
        'backdrop-filter: blur(24px)',
        'border-radius: 999px',
        '.st-key-ms2-question-composer',
        'min-height: 100dvh',
        '@media (max-width: 768px)',
        'prefers-reduced-motion: reduce',
    ]:
        assert token in css
    assert '.st-key-editorial-product-nav' not in css
    assert '> div[data-testid="stColumn"]:last-child' in css
    assert 'position: absolute !important' in css
    assert "Origin" not in css.split('"""', 2)[-1]


def test_homepage_background_has_fixed_dimensions_before_paint():
    css = _source("homepage_styles.py")

    assert '.st-key-ms2-hero [data-testid="stImage"]' in css
    assert "height: 100%" in css
    assert "object-fit: cover" in css
    assert "overflow-x" not in css
