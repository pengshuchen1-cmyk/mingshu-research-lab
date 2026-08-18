"""命数研究室 Streamlit 主入口。"""

from __future__ import annotations

from html import escape
import os

try:
    import streamlit as st
except ModuleNotFoundError:
    print("缺少 streamlit，请先运行：python -m pip install -r requirements.txt")
    raise SystemExit(1)

from ui.archive_page import render_archive_page
from ui.acceptance_page import render_acceptance_page
from ui.backup_page import render_backup_page
from ui.compatibility_page import render_compatibility_page
from ui.bazi_page import render_bazi_page
from ui.inquiry_page import render_inquiry_page
from ui.five_element_page import render_five_element_page
from ui.life_overview_page import render_life_overview_page
from ui.luck_page import render_luck_page
from ui.my_page import render_my_page
from ui.profile_form import render_profile_form
from ui.report_page import render_report_page
from ui.settings_page import render_settings_page
from ui.sixty_jiazi_page import render_sixty_jiazi_page
from ui.special_reports_page import render_special_reports_page
from ui.styles import get_global_css
from ui.yearly_page import render_yearly_page
from ui.ziwei_page import render_ziwei_page
from utils.database import init_db
from utils.navigation_state import (
    DEFAULT_APP_PAGE,
    enter_app,
)
from utils.runtime_mode import is_public_mode
from utils.release_privacy import assert_public_release_safe
from utils.session_privacy import maintain_private_session


PUBLIC_PAGE_NAMES = ("今日/年度建议", "个人命盘", "AI问答", "简明报告", "设置/档案")
PRODUCT_NAV_ITEMS = (
    ("今日", "今日/年度建议"),
    ("命盘", "个人命盘"),
    ("问AI", "AI问答"),
    ("报告", "简明报告"),
    ("我的", "设置/档案"),
)
PRODUCT_NAV_KEYS = {
    "今日/年度建议": "today",
    "个人命盘": "chart",
    "AI问答": "inquiry",
    "简明报告": "report",
    "设置/档案": "account",
}
PRODUCT_NAV_GROUPS = {
    "今日/年度建议": {"年度运程"},
    "个人命盘": {
        "新建命盘",
        "八字排盘",
        "命盘总览",
        "五行喜忌",
        "六十甲子",
        "大运流年",
        "紫微斗数",
        "合婚匹配",
    },
    "AI问答": {"综合问盘"},
    "简明报告": {"专项报告", "报告导出"},
    "设置/档案": {"命盘档案", "数据备份", "设置"},
}


def _request_navigation(target: str) -> None:
    import streamlit as st
    enter_app(st.session_state)
    st.session_state["navigate_to"] = target
    st.rerun()


def _render_navigation_scroll_reset() -> None:
    """Reset route scroll once without fighting Streamlit's incremental render."""
    script = """
    <script>
    (() => {
      const parentWindow = window.parent;
      const main = parentWindow.document.querySelector(".stMain");
      if (!main) return;

      // Streamlit updates a route in several DOM commits. Repeated scroll resets
      // fight browser scroll anchoring and visibly shake the viewport, so reset
      // exactly once after the current paint and then restore normal anchoring.
      main.style.overflowAnchor = "none";
      parentWindow.requestAnimationFrame(() => {
        main.scrollTo({ top: 0, left: 0, behavior: "auto" });
        parentWindow.requestAnimationFrame(() => {
          main.style.removeProperty("overflow-anchor");
        });
      });
    })();
    </script>
    """
    with st.container(key="ms-navigation-reset-bridge"):
        st.iframe(script, height=1, width=1, tab_index=-1)


def _resolve_active_page(
    navigation_target: str | None,
    persisted_active_page: str | None,
    sidebar_selection: str,
    pages: dict,
    sidebar_pages: dict,
    *,
    sidebar_changed: bool = False,
) -> str:
    """Keep internal routes stable across reruns unless the user changes sidebar page."""
    if navigation_target in pages:
        return navigation_target
    if (
        persisted_active_page in pages
        and not sidebar_changed
        and persisted_active_page not in sidebar_pages
    ):
        return persisted_active_page
    return sidebar_selection if sidebar_selection in pages else DEFAULT_APP_PAGE


def render_product_navigation(active_page: str | None) -> None:
    import streamlit as st
    st.markdown("[跳到主要内容](#ms-main)")
    with st.container(key="editorial-product-nav"):
        items = st.columns(len(PRODUCT_NAV_ITEMS))
        for column, (label, target) in zip(items, PRODUCT_NAV_ITEMS):
            with column:
                is_active = (
                    active_page == target
                    or active_page in PRODUCT_NAV_GROUPS.get(target, set())
                )
                nav_key = PRODUCT_NAV_KEYS[target]
                if st.button(label, key=f"editorial_nav_{nav_key}",
                             type="primary" if is_active else "secondary",
                             use_container_width=True):
                    _request_navigation(target)


def render_main_content_anchor() -> None:
    """Provide one stable skip-link destination for every routed page."""
    st.markdown('<div id="ms-main" tabindex="-1"></div>', unsafe_allow_html=True)


def render_compliance_footer() -> None:
    """Show mainland filing numbers when configured by the operator."""
    filing_links: list[str] = []
    icp_number = os.getenv("MINGSHU_ICP_NUMBER", "").strip()
    public_security_number = os.getenv(
        "MINGSHU_PUBLIC_SECURITY_NUMBER", ""
    ).strip()
    if icp_number:
        filing_links.append(
            '<a href="https://beian.miit.gov.cn/" target="_blank" '
            f'rel="noopener noreferrer">{escape(icp_number)}</a>'
        )
    if public_security_number:
        filing_links.append(
            '<a href="https://beian.mps.gov.cn/" target="_blank" '
            f'rel="noopener noreferrer">{escape(public_security_number)}</a>'
        )
    if not filing_links:
        return
    st.markdown(
        '<div style="margin-top:48px;padding:18px 0;text-align:center;'
        'border-top:1px solid rgba(61,43,26,.12);font-size:12px;'
        'color:#8C7A64;">'
        + " · ".join(filing_links)
        + "</div>",
        unsafe_allow_html=True,
    )


def get_pages() -> dict:
    """返回全部可访问页面。"""
    pages = {
        "今日/年度建议": render_yearly_page,
        "个人命盘": render_life_overview_page,
        "简明报告": render_report_page,
        "AI问答": render_inquiry_page,
        "设置/档案": render_my_page,
        "验收中心": render_acceptance_page,
        "新建命盘": render_profile_form,
        "八字排盘": render_bazi_page,
        "命盘总览": render_life_overview_page,
        "综合问盘": render_inquiry_page,
        "五行喜忌": render_five_element_page,
        "六十甲子": render_sixty_jiazi_page,
        "大运流年": render_luck_page,
        "年度运程": render_yearly_page,
        "专项报告": render_special_reports_page,
        "紫微斗数": render_ziwei_page,
        "报告导出": render_report_page,
        "命盘档案": render_archive_page,
        "合婚匹配": render_compatibility_page,
        "数据备份": render_backup_page,
        "设置": render_settings_page,
    }
    if is_public_mode():
        for local_only_page in ("命盘档案", "数据备份"):
            pages.pop(local_only_page, None)
    return pages


def get_sidebar_pages(pages: dict) -> dict:
    """返回大众使用版左侧导航页面。"""
    return {name: pages[name] for name in PUBLIC_PAGE_NAMES}


def main() -> None:
    """启动 Streamlit 应用。"""
    st.set_page_config(page_title="命数研究室", layout="wide", page_icon="✦")
    if is_public_mode():
        from pathlib import Path

        assert_public_release_safe(Path(__file__).resolve().parent)
        maintain_private_session(st.session_state)
    else:
        init_db()

    # 注入全局 CSS
    st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)

    pages = get_pages()
    sidebar_pages = get_sidebar_pages(pages)

    # 产品直接进入“今日”；侧栏只保留为键盘/辅助技术回退入口。
    nav_target = st.session_state.pop("navigate_to", None)
    enter_app(st.session_state)
    if nav_target in sidebar_pages:
        st.session_state["sidebar_navigation"] = nav_target
    elif st.session_state.get("sidebar_navigation") not in sidebar_pages:
        st.session_state["sidebar_navigation"] = DEFAULT_APP_PAGE

    st.sidebar.markdown(
        '<div class="sidebar-title">命数研究室</div>'
        '<div class="sidebar-subtitle">八字 · 紫微 · 命理分析</div>',
        unsafe_allow_html=True,
    )
    previous_sidebar = st.session_state.get("last_sidebar_navigation")
    selected = st.sidebar.radio(
        "导航",
        list(sidebar_pages.keys()),
        key="sidebar_navigation",
        label_visibility="collapsed",
    )
    sidebar_changed = previous_sidebar is not None and selected != previous_sidebar
    st.session_state["last_sidebar_navigation"] = selected
    active_page = _resolve_active_page(
        nav_target,
        st.session_state.get("active_product_page"),
        selected,
        pages,
        sidebar_pages,
        sidebar_changed=sidebar_changed,
    )
    st.session_state["active_product_page"] = active_page
    navigation_changed = nav_target in pages or sidebar_changed
    render_product_navigation(active_page)
    render_main_content_anchor()
    pages[active_page]()
    render_compliance_footer()
    if navigation_changed:
        _render_navigation_scroll_reset()


if __name__ == "__main__":
    main()
