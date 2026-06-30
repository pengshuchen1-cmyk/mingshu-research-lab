"""命数研究室 Streamlit 主入口。"""

from __future__ import annotations

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
from ui.home import render_home
from ui.luck_page import render_luck_page
from ui.profile_form import render_profile_form
from ui.report_page import render_report_page
from ui.settings_page import render_settings_page
from ui.special_reports_page import render_special_reports_page
from ui.styles import get_global_css
from ui.yearly_page import render_yearly_page
from ui.ziwei_page import render_ziwei_page
from utils.database import init_db


def get_pages() -> dict:
    """返回左侧导航页面。"""
    return {
        "首页": render_home,
        "验收中心": render_acceptance_page,
        "新建命盘": render_profile_form,
        "八字排盘": render_bazi_page,
        "命盘总览": render_life_overview_page,
        "综合问盘": render_inquiry_page,
        "五行喜忌": render_five_element_page,
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


def main() -> None:
    """启动 Streamlit 应用。"""
    st.set_page_config(page_title="命数研究室", layout="wide", page_icon="✦")
    init_db()

    # 注入全局 CSS
    st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)

    pages = get_pages()

    # 自定义侧边栏标题
    st.sidebar.markdown(
        '<div class="sidebar-title">命数研究室</div>'
        '<div class="sidebar-subtitle">八字 · 紫微 · 命理分析</div>',
        unsafe_allow_html=True,
    )

    # 支持首页快捷按钮导航，同时始终保留左侧导航。
    nav_target = st.session_state.pop("navigate_to", None)
    if nav_target and nav_target in pages:
        st.session_state["sidebar_navigation"] = nav_target
    elif st.session_state.get("sidebar_navigation") not in pages:
        st.session_state["sidebar_navigation"] = list(pages.keys())[0]

    selected = st.sidebar.radio(
        "导航",
        list(pages.keys()),
        key="sidebar_navigation",
        label_visibility="collapsed",
    )
    pages[selected]()


if __name__ == "__main__":
    main()
