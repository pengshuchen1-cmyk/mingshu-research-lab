"""Editorial public homepage components."""

from __future__ import annotations

from html import escape
from textwrap import dedent
from typing import Callable

import streamlit as st

from core.popular_advice_engine import (
    PopularAdviceUnavailableError,
    build_daily_advice,
)
from core.presentation_models import build_daily_guidance_view
from ui.homepage_dot_field import render_homepage_dot_field
from ui.homepage_styles import get_homepage_css


HOME_VERSION = "v2.0.0"
HOME_CACHE_VERSION_LABEL = "v2-editorial-public-guidance"

_COLOR_CLASSES = {
    "青绿": "green",
    "浅蓝": "light-blue",
    "红色": "red",
    "暖橙": "orange",
    "米黄": "sand",
    "大地色": "earth",
    "白色": "white",
    "金色": "gold",
    "黑色": "black",
    "深蓝": "deep-blue",
}

NAV_TARGETS = {
    "首页": "首页",
    "今日/年度建议": "今日/年度建议",
    "个人命盘": "个人命盘",
    "简明报告": "简明报告",
    "设置/档案": "设置/档案",
    "新建命盘": "新建命盘",
}


def _html(markup: str) -> None:
    """Render compact HTML without Streamlit code-block indentation."""
    normalized = "\n".join(line.strip() for line in dedent(markup).strip().splitlines())
    st.markdown(normalized, unsafe_allow_html=True)


def _go(target: str, key: str, label: str, *, primary: bool = False) -> None:
    """Navigate within the Streamlit application."""
    button_type = "primary" if primary else "secondary"
    if st.button(label, key=key, use_container_width=True, type=button_type):
        st.session_state["navigate_to"] = target
        st.rerun()


def _render_product_nav() -> None:
    _html(
        """
        <header class="ms2-product-nav">
          <p class="ms2-brand">命数研究室</p>
          <p class="ms2-nav-caption">PUBLIC GUIDANCE · PERSONAL READING</p>
        </header>
        """
    )
    st.markdown("[跳到主要内容](#ms2-main)")
    columns = st.columns(4)
    entries = [
        ("今日/年度建议", "ms2_nav_public", "今日/年度建议"),
        ("个人命盘", "ms2_nav_profile", "个人命盘"),
        ("简明报告", "ms2_nav_report", "简明报告"),
        ("设置/档案", "ms2_nav_archive", "设置/档案"),
    ]
    for column, (target, key, label) in zip(columns, entries):
        with column:
            _go(target, key, label)


def _daily_advice_card_markup(daily: dict | None) -> str:
    if daily is None:
        return """
            <aside class="ms2-daily-advice" aria-label="大众今日建议">
              <div class="ms2-advice-heading">
                <p class="ms2-kicker">PUBLIC · DAILY</p><p>今日 · 传统历法</p>
              </div>
              <h2>今日内容暂不可用</h2>
              <div class="ms2-advice-section"><span>五行主题</span><strong>待更新</strong></div>
              <div class="ms2-advice-section"><span>今日重点</span><strong>保持原有节奏</strong></div>
              <div class="ms2-advice-section"><span>今日宜穿</span><p>历法数据恢复后将显示 2–3 个颜色名。</p></div>
              <div class="ms2-advice-section"><span>今日注意</span><p>请稍后再试，不会为你编造今日结论。</p></div>
              <div class="ms2-primary-action"><span>主要行动</span><strong>保持原有节奏</strong></div>
              <p class="ms2-boundary-note">这是大众参考，不读取出生资料。</p>
            </aside>
            """

    color_chips = "".join(
        (
            '<span class="ms2-color-chip">'
            f'<i class="ms2-color-dot ms2-color-{_COLOR_CLASSES.get(color, "neutral")}" '
            'aria-hidden="true"></i>'
            f"{escape(str(color))}</span>"
        )
        for color in daily["wearing_colors"][:3]
    )
    cautions = "".join(
        f'<p class="ms2-caution-item">{escape(str(item))}</p>'
        for item in daily["cautions"][:2]
    )
    if not cautions:
        cautions = '<p class="ms2-caution-item">避免过度消耗</p>'

    return f"""
        <aside class="ms2-daily-advice" aria-label="大众今日建议">
          <div class="ms2-advice-heading">
            <p class="ms2-kicker">PUBLIC · DAILY</p>
            <p>{escape(str(daily['date']))} · {escape(str(daily['day_pillar']))}</p>
          </div>
          <h2>{escape(str(daily['title']))}</h2>
          <div class="ms2-advice-section ms2-element-theme">
            <span>五行主题</span><strong>{escape(str(daily['element_theme']))}</strong>
          </div>
          <div class="ms2-advice-section ms2-daily-focus">
            <span>今日重点</span><strong>{escape(str(daily['focus']))}</strong>
          </div>
          <div class="ms2-advice-section">
            <span>今日宜穿</span><div class="ms2-color-list">{color_chips}</div>
            <p>{escape(str(daily['wearing_advice']))}</p>
          </div>
          <div class="ms2-advice-section"><span>今日注意</span>{cautions}</div>
          <div class="ms2-primary-action">
            <span>主要行动</span><strong>{escape(str(daily['primary_action']))}</strong>
          </div>
          <p class="ms2-boundary-note"><strong>大众参考</strong>{escape(str(daily['boundary_note']))}</p>
        </aside>
        """


def _render_editorial_hero(daily: dict | None) -> None:
    _render_product_nav()
    advice_card = _daily_advice_card_markup(daily)
    with st.container(key="ms2-hero"):
        hero_left, hero_right = st.columns([1.08, 0.92], vertical_alignment="top")
        with hero_left:
            _html(
                """
                <section class="ms2-hero-copy" id="ms2-main" tabindex="-1">
            <p class="ms2-kicker">命数研究室 · DAILY GUIDANCE</p>
            <h1>认识命数<br>活出选择</h1>
            <p class="ms2-hero-lede">用结构化的命数体系，理解人生的底层逻辑，
            在每一个当下，做更清醒的选择。</p>
                </section>
                """
            )
            _render_hero_action()
        with hero_right:
            _html(advice_card)


def _render_hero_action() -> None:
    _go("新建命盘", "ms2_hero_personal", "开始探索命数", primary=True)


def _load_daily_advice() -> dict | None:
    try:
        return build_daily_guidance_view(advice=build_daily_advice())
    except PopularAdviceUnavailableError:
        return None


def render_homepage_landing(
    chart: dict | None = None,
    profile_data: dict | None = None,
    render_compact_summary: Callable[[dict], None] | None = None,
) -> None:
    """Render the focused public homepage; personal inputs stay out of this view."""
    daily = _load_daily_advice()
    element_theme = str(daily["element_theme"]) if daily else ""
    _html(get_homepage_css(element_theme))
    with st.container(key="ms2-home"):
        _render_editorial_hero(daily)
    render_homepage_dot_field()
