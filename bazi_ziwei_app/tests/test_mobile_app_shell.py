from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_product_starts_on_today_without_landing_or_celestial_canvas():
    source = _source("app.py")

    assert 'DEFAULT_APP_PAGE' in source
    assert '"首页": render_home' not in source
    assert "render_product_background" not in source
    assert "homepage_helix_effect" not in source
    assert source.index("render_product_navigation(active_page)") < source.index(
        "pages[active_page]()"
    )


def test_five_item_navigation_is_fixed_and_reserves_safe_space():
    app = _source("app.py")
    css = _source("ui/styles.py")

    assert '("问AI", "AI问答")' in app
    assert "items = st.columns(len(PRODUCT_NAV_ITEMS))" in app
    assert "position: fixed !important" in css
    assert "grid-template-columns: repeat(5, minmax(0, 1fr))" in css
    assert "padding-bottom: calc(7.5rem + env(safe-area-inset-bottom))" in css
    assert 'bottom: calc(78px + env(safe-area-inset-bottom))' in css
    assert ".st-key-editorial_nav_inquiry" in css
    assert "min-height: 54px" in css
    assert '.stButton button[kind="secondary"]' in css


def test_light_shell_controls_do_not_fall_back_to_dark_or_orange():
    css = _source("ui/styles.py")
    controls = css.split(
        'body:not(:has(.st-key-ms2-home)) div[data-testid="stExpander"]', 1
    )[1].split('/* AI inquiry:', 1)[0]
    mobile_nav = css.split('@media (max-width: 640px)', 1)[1].split(
        'body:not(:has(.st-key-ms2-home)) .ms2-page-hero', 1
    )[0]

    for dark in ("rgba(11, 15, 26, .78)", "rgba(8, 12, 22, .86)", "#0C111D"):
        assert dark not in controls
    assert "var(--ms-panel)" in controls
    assert "var(--ms-accent-soft)" in controls
    assert "rgba(5, 8, 17, .92)" not in mobile_nav
    assert "rgba(242, 168, 95, .30)" not in mobile_nav


def test_today_score_and_reflection_use_only_local_guidance():
    source = _source("ui/yearly_page.py")

    assert "def _daily_score" in source
    assert "def build_reflection_cards" in source
    assert '"查看心理解读"' in source
    assert '("日", "周", "月", "年")' in source
    assert source.count('class="ms-reflection-card"') == 1
    assert "不是心理诊断，也不是确定预测" in source
    assert "build_daily_guidance_view" in source
    assert "generate(" not in source


def test_reflection_cards_are_stable_and_have_three_prompts():
    from ui.yearly_page import _daily_score, build_reflection_cards

    daily = {
        "date": "2026-08-13",
        "day_pillar": "己未",
        "focus": "整理目标",
        "reminder": "过度透支",
        "details": {"relaxation": "慢走十分钟"},
    }
    yearly = {"focus": "长期规划"}

    assert _daily_score(daily) == 88
    assert _daily_score(None) is None
    cards = build_reflection_cards(daily, yearly, "周")
    assert len(cards) == 3
    assert all(card["title"] and card["prompt"] for card in cards)
    assert "这一周" in cards[0]["prompt"]
    assert "整理目标" not in " ".join(card["prompt"] for card in cards)


def test_year_reflection_uses_yearly_fields_and_score_is_self_assessment():
    from ui.yearly_page import build_reflection_cards

    cards = build_reflection_cards(
        {"focus": "今日字段"},
        {"focus": "年度重点", "theme": "年度主题", "actions": ["年度行动"]},
        "年",
    )
    text = " ".join(card["prompt"] for card in cards)
    assert "年度主题" in text
    assert "年度重点" in text
    assert "年度行动" in text
    assert "今日字段" not in text
    source = _source("ui/yearly_page.py")
    assert "默认自评起点，可按现实感受理解，不是命理评分" in source
    assert "if score is None" in source
