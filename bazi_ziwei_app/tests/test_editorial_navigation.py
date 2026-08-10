import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def test_product_navigation_uses_internal_named_routes_only():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'PUBLIC_PAGE_NAMES = ("今日/年度建议", "个人命盘", "AI问答", "简明报告", "设置/档案")' in source
    assert "PRODUCT_NAV_ITEMS" in source
    assert 'st.session_state["navigate_to"] = target' in source
    assert "def render_product_navigation" in source
    assert "?page=" not in source.split("def render_product_navigation", 1)[1]
    navigation = source.split("def render_product_navigation", 1)[1].split(
        "def render_compliance_footer", 1
    )[0]
    assert 'active_page in (None, "首页")' not in navigation


def test_request_navigation_sets_only_named_target_and_reruns(monkeypatch):
    app = importlib.import_module("app")
    rerun_calls = []
    fake_streamlit = SimpleNamespace(
        session_state={},
        rerun=lambda: rerun_calls.append(True),
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    app._request_navigation("简明报告")

    assert fake_streamlit.session_state == {
        "mingshu_app_entered": True,
        "navigate_to": "简明报告",
    }
    assert rerun_calls == [True]


def test_route_change_uses_one_stable_scroll_reset_without_observer_loop():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "def _render_navigation_scroll_reset" in source
    assert 'querySelector(".stMain")' in source
    assert 'main.scrollTo({ top: 0, left: 0, behavior: "auto" })' in source
    assert 'main.style.overflowAnchor = "none"' in source
    assert 'main.style.removeProperty("overflow-anchor")' in source
    scroll_reset = source.split("def _render_navigation_scroll_reset", 1)[1].split(
        "def _resolve_active_page", 1
    )[0]
    assert "MutationObserver" not in scroll_reset
    assert "setTimeout" not in scroll_reset
    assert scroll_reset.count(".scrollTo(") == 1
    assert 'navigation_changed = nav_target in pages or sidebar_changed' in source
    assert "if navigation_changed:" in source
    assert 'st.container(key="ms-navigation-reset-bridge")' in source
    assert ".st-key-ms-navigation-reset-bridge" in styles


def test_product_navigation_targets_are_named_pages():
    app = importlib.import_module("app")
    pages = app.get_pages()

    assert all(target in pages for _, target in app.PRODUCT_NAV_ITEMS)
    assert "新建命盘" in app.PRODUCT_NAV_GROUPS["个人命盘"]
    assert "报告导出" in app.PRODUCT_NAV_GROUPS["简明报告"]


def test_mobile_navigation_is_fixed_five_item_bar_with_content_clearance():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert 'st.container(key="editorial-product-nav")' in source
    assert ".st-key-editorial-product-nav" in styles
    assert "grid-template-columns: repeat(5, minmax(0, 1fr))" in styles
    assert "env(safe-area-inset-bottom)" in styles
    assert "padding-bottom: calc(6.25rem + env(safe-area-inset-bottom))" in styles
    assert (
        '.st-key-editorial-product-nav [data-testid="stHorizontalBlock"]\n'
        "        > div:has(.st-key-editorial_nav_inquiry) {"
    ) not in styles
    assert ".st-key-editorial_nav_inquiry { display: none !important; }" not in styles
    mobile_styles = styles.split("@media (max-width: 640px)", 1)[1]
    assert (
        '.st-key-editorial-product-nav [data-testid="stHorizontalBlock"] '
        "> div:first-child {\n            display: none !important;"
    ) not in mobile_styles
    assert "items = st.columns(len(PRODUCT_NAV_ITEMS))" in source
    assert "editorial_nav_home" not in source


def test_landing_is_outside_the_five_item_product_navigation():
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert '("今日", "今日/年度建议")' in source
    assert 'sidebar_changed = False\n        active_page = LANDING_PAGE_NAME' in source
    assert 'if active_page != LANDING_PAGE_NAME:' in source
    assert source.index('if active_page != LANDING_PAGE_NAME:') < source.index(
        "render_product_navigation(active_page)"
    )
    entered_branch = source.split("if has_entered_app(st.session_state):", 1)[1]
    assert entered_branch.index("st.sidebar.radio") < entered_branch.index("else:")


def test_skip_link_has_a_shared_target_before_every_page():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert 'st.markdown("[跳到主要内容](#ms-main)")' in source
    assert '<div id="ms-main" tabindex="-1"></div>' in source
    assert source.index("render_main_content_anchor()") < source.index(
        "pages[active_page]()"
    )
    assert 'div[data-testid="stElementContainer"]:has(a[href="#ms-main"])' in styles


def test_main_container_uses_current_streamlit_selector_without_default_top_gap():
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    homepage_styles = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

    assert '[data-testid="stMainBlockContainer"] {' in styles
    assert "padding-top: 20px !important" in styles
    assert 'header[data-testid="stHeader"],' in styles
    assert 'div[data-testid="stToolbar"],' in styles
    assert "display: none !important" in styles
    assert ".main .block-container" not in styles
    assert ".main .block-container" not in homepage_styles


def test_desktop_navigation_is_flat_and_stays_in_document_flow():
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    nav_rule = styles.split(".st-key-editorial-product-nav {", 1)[1].split("}", 1)[0]
    assert "position: relative" in nav_rule
    assert "border-radius: 0" in nav_rule
    assert "box-shadow: none" in nav_rule
    assert "backdrop-filter" not in nav_rule
    active_rule = styles.split(
        '.st-key-editorial-product-nav .stButton button[kind="primary"] {', 1
    )[1].split("}", 1)[0]
    assert "border-top: 0" in active_rule
    assert "border-right: 0" in active_rule
    assert "border-bottom: 2px solid var(--ms-action)" in active_rule
    assert "border-left: 0" in active_rule


def test_home_and_inner_pages_share_one_stable_content_width():
    homepage_styles = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "max-width: 1280px !important" in styles
    assert "max-width: 1200px !important" not in styles
    assert "padding: 0 !important" not in homepage_styles
