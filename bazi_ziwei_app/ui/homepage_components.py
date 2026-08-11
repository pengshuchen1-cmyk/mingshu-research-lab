"""Cinematic public homepage components."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Callable

import streamlit as st
import streamlit_shadcn_ui as shadcn

from ui.homepage_styles import get_homepage_css
from ui.homepage_helix_effect import render_helix_background
from ui.homepage_typing_effect import render_question_typing_effect
from utils.navigation_state import enter_app
from utils.session_privacy import PENDING_INQUIRY_KEY as PENDING_QUESTION_KEY


HOME_VERSION = "v4.1.0"
HOME_CACHE_VERSION_LABEL = "v4-animated-celestial-helix"
HERO_BACKGROUND = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "hero-celestial-helix-v1.webp"
)
TYPEWRITER_QUESTIONS = (
    "今天我的运势如何？",
    "如何推算我的命盘？",
    "今年是我的本命年，我的事业和爱情怎么样？",
)

def _html(markup: str) -> None:
    """Render compact static HTML without Markdown code-block indentation."""
    normalized = "\n".join(line.strip() for line in dedent(markup).strip().splitlines())
    st.markdown(normalized, unsafe_allow_html=True)


def _open_product_page(target: str) -> None:
    """Enter the product on one explicit top-level destination."""
    st.session_state.pop(PENDING_QUESTION_KEY, None)
    enter_app(st.session_state)
    st.session_state["navigate_to"] = target
    st.rerun()


def _render_question_composer() -> None:
    """Render the enlarged Shadcn-powered question field."""
    with st.container(key="ms2-question-composer"):
        question_column, submit_column = st.columns([7, 1], vertical_alignment="bottom")
        with question_column:
            shadcn.input(
                "",
                key="ms2_home_question",
                placeholder=TYPEWRITER_QUESTIONS[0],
                max_length=2000,
                width="stretch",
            )
        with submit_column:
            submitted = shadcn.button(
                "↑",
                key="ms2_home_submit",
                variant="secondary",
                size="lg",
                width="stretch",
            )
        if submitted:
            _open_product_page("个人命盘")


def _render_start_action() -> None:
    """Render the primary CTA that enters the daily guidance page."""
    with st.container(key="ms2-start-action"):
        started = st.button(
            "GET STARTED →",
            key="ms2_home_start",
            type="secondary",
        )
    if started:
        _open_product_page("今日/年度建议")


def _render_masthead() -> None:
    """Render the single quiet brand requested for the public homepage."""
    _html(
        """
        <header class="ms2-masthead" aria-label="首页页眉">
          <div class="ms2-brand" aria-label="命数研究室">
            <svg viewBox="0 0 42 32" role="img" aria-hidden="true">
              <path d="M2 4c8 1 14 5 19 13C15 13 9 11 4 11" />
              <path d="M40 4c-8 1-14 5-19 13 6-4 12-6 17-6" />
              <path d="M21 17v11" />
            </svg>
            <span>命数研究室</span>
          </div>
        </header>
        """
    )


def _render_immersive_hero() -> None:
    """Render the focused hero over an animated celestial double helix."""
    with st.container(key="ms2-hero"):
        st.image(str(HERO_BACKGROUND), width="stretch")
        render_helix_background()
        with st.container(key="ms2-hero-content"):
            _render_masthead()
            with st.container(key="ms2-hero-stage"):
                with st.container(key="ms2-primary-panel"):
                    _html(
                        """
                        <section class="ms2-hero-copy" id="ms2-main" tabindex="-1">
                          <p class="ms2-hero-kicker">看见你的</p>
                          <h1>命数</h1>
                          <p class="ms2-hero-lede">从命盘出发，回答此刻真正关心的问题。</p>
                        </section>
                        """
                    )
                    _render_start_action()
                    _render_question_composer()
                    _html(
                        '<p class="ms2-trust-note">本地排盘 · 隐私优先 · 结论仅供参考</p>'
                    )


def render_homepage_landing(
    chart: dict | None = None,
    profile_data: dict | None = None,
    render_compact_summary: Callable[[dict], None] | None = None,
) -> None:
    """Render the focused public homepage; personal inputs stay out of this view."""
    del chart, profile_data, render_compact_summary
    _html(get_homepage_css())
    with st.container(key="ms2-home"):
        _render_immersive_hero()
        render_question_typing_effect(TYPEWRITER_QUESTIONS)
