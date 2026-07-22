import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_sections_follow_editorial_reading_order():
    tree = ast.parse((ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8"))
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
    assert calls == [
        "_render_editorial_hero",
    ]


def test_homepage_contains_one_public_daily_card_and_no_legacy_sections():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    for expected in [
        "build_daily_advice",
        "build_daily_guidance_view",
        "今日宜穿",
            "今日注意",
            "今日重点",
            "主要行动",
        "五行主题",
        "大众参考",
        'daily["wearing_colors"][:3]',
        'daily["cautions"][:2]',
    ]:
        assert expected in source
    for forbidden in [
        "_render_value_strip",
        "_render_product_preview",
        "_render_entry_choices",
        "_render_loaded_chart_hint",
        "_render_method_boundary",
        "_render_footer_action",
    ]:
        assert forbidden not in source


def test_homepage_title_uses_two_unpunctuated_lines():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

    assert "认识命数<br>活出选择" in source
    assert "认识命数，" not in source
    assert "活出选择。" not in source


def test_daily_advice_card_labels_every_required_public_field():
    from ui.homepage_components import _daily_advice_card_markup

    markup = _daily_advice_card_markup(
        {
            "date": "2026-07-14",
            "day_pillar": "己丑",
            "title": "今日建议",
        "element_theme": "土",
        "focus": "保持稳定节奏",
        "wearing_colors": ["米黄", "大地色"],
            "wearing_advice": "选择稳定质感的物件",
            "cautions": ["拖延堆积", "过度担忧"],
            "primary_action": "整理财务",
            "boundary_note": "不读取姓名或出生资料。",
        }
    )

    for expected in [
        "2026-07-14",
        "己丑",
        "五行主题",
        "今日宜穿",
        "米黄",
        "大地色",
        "今日注意",
        "拖延堆积",
        "今日重点",
        "保持稳定节奏",
        "主要行动",
        "整理财务",
        "大众参考",
        "不读取姓名或出生资料",
    ]:
        assert expected in markup


def test_homepage_uses_real_streamlit_columns_for_hero_and_keeps_cta_left():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    hero = functions["_render_editorial_hero"]
    hero_source = ast.get_source_segment(source, hero)
    landing_source = ast.get_source_segment(source, functions["render_homepage_landing"])

    assert 'st.container(key="ms2-hero")' in hero_source
    assert "st.columns([1.08, 0.92]" in hero_source
    assert "with hero_left:" in hero_source
    assert "with hero_right:" in hero_source
    assert hero_source.index("with hero_left:") < hero_source.index("with hero_right:")
    assert hero_source.index("_render_hero_action()") > hero_source.index("with hero_left:")
    assert hero_source.index("_render_hero_action()") < hero_source.index("with hero_right:")
    assert "<section class=\"ms2-hero\"" not in hero_source
    assert "<main class=\"ms2-home\"" not in landing_source
    assert "</main>" not in landing_source


def test_homepage_primary_cta_css_targets_the_actual_left_streamlit_column():
    css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

    selector = (
        '.st-key-ms2-hero div[data-testid="stHorizontalBlock"] '
        '> div[data-testid="stColumn"]:first-child .stButton > button[kind="primary"]'
    )
    assert selector in css
    scoped_rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "#EC4899" in scoped_rule
    assert "min-height: 44px" in scoped_rule


def test_hero_columns_use_a_streamlit_supported_vertical_alignment():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    hero = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_render_editorial_hero"
    )
    columns_call = next(
        node
        for node in ast.walk(hero)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "columns"
    )
    alignment = next(
        keyword.value.value
        for keyword in columns_call.keywords
        if keyword.arg == "vertical_alignment" and isinstance(keyword.value, ast.Constant)
    )

    assert alignment in {"top", "center", "bottom"}


def test_hero_title_css_targets_the_rendered_hero_copy():
    css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

    assert ".ms2-hero-copy h1" in css
    assert ".ms2-hero h1" not in css


def test_homepage_css_uses_approved_editorial_system():
    css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
    for expected in [
        "#FAFAFA",
        "#18181B",
        "#EC4899",
        "def get_homepage_css(element_theme: str = \"\")",
        ".ms2-daily-advice",
        ".ms2-color-dot",
        "opacity: .035",
        "grid-template-columns: 1fr",
        "min-height: 44px",
        "prefers-reduced-motion: reduce",
    ]:
        assert expected in css
    for forbidden in [
        "#05080A",
        "#D8B96A",
        "gradient",
        "v106c-orbit",
        ".ms2-value-strip",
        ".ms2-product-preview",
        "🌳",
        "🔥",
        "💧",
    ]:
        assert forbidden not in css
