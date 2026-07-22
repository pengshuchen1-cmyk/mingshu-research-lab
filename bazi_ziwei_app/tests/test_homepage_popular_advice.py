import ast
from pathlib import Path
from unittest.mock import patch


def test_homepage_renders_focused_daily_public_advice_section():
    text = Path(__file__).resolve().parents[1].joinpath("ui", "homepage_components.py").read_text(encoding="utf-8")

    assert "build_daily_advice" in text
    assert "build_daily_guidance_view" in text
    assert "def _daily_advice_card_markup" in text
    assert "今日宜穿" in text
    assert "今日注意" in text
    assert "大众参考" in text
    assert 'daily["wearing_colors"][:3]' in text
    assert "build_yearly_popular_advice" not in text
    assert "_render_product_preview" not in text


def test_public_advice_is_inside_hero_before_the_single_primary_action():
    text = Path(__file__).resolve().parents[1].joinpath(
        "ui", "homepage_components.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }

    render_function = functions["render_homepage_landing"]
    render_calls = [
        node.func.id
        for node in sorted(ast.walk(render_function), key=lambda item: getattr(item, "lineno", 0))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    ]
    assert [name for name in render_calls if name.startswith("_render")] == [
        "_render_editorial_hero",
    ]

    hero_source = ast.get_source_segment(text, functions["_render_editorial_hero"])
    assert "_daily_advice_card_markup(daily)" in hero_source
    assert 'st.container(key="ms2-hero")' in hero_source
    assert "st.columns([1.08, 0.92]" in hero_source
    assert hero_source.index("with hero_left:") < hero_source.index("_render_hero_action()")
    assert hero_source.index("_render_hero_action()") < hero_source.index("with hero_right:")
    action_source = ast.get_source_segment(text, functions["_render_hero_action"])
    assert '"\u5f00\u59cb\u63a2\u7d22\u547d\u6570"' in action_source
    assert "primary=True" in action_source


def test_homepage_has_no_unlabelled_fixed_personal_results():
    text = Path(__file__).resolve().parents[1].joinpath(
        "ui", "homepage_components.py"
    ).read_text(encoding="utf-8")

    for fixed_claim in [
        "98.7%",
        "96.2%",
        "95.4%",
        "93.1%",
        "命盘评分",
        "甲辰运",
        "正官格",
        "事业上升期",
    ]:
        assert fixed_claim not in text


def test_homepage_renders_a_truthful_empty_card_when_daily_calendar_is_unavailable():
    from core.popular_advice_engine import PopularAdviceUnavailableError
    from ui import homepage_components

    with patch.object(
        homepage_components,
        "build_daily_advice",
        side_effect=PopularAdviceUnavailableError("calendar unavailable"),
    ):
        assert homepage_components._load_daily_advice() is None

    markup = homepage_components._daily_advice_card_markup(None)
    assert "今日内容暂不可用" in markup
    assert "不会为你编造今日结论" in markup
    assert "这是大众参考，不读取出生资料" in markup
