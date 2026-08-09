"""Immersive public homepage components."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Callable

import streamlit as st
import streamlit_shadcn_ui as shadcn

from ui.homepage_styles import get_homepage_css
from ui.homepage_typing_effect import render_question_typing_effect
from utils.navigation_state import enter_app
from utils.session_privacy import PENDING_INQUIRY_KEY as PENDING_QUESTION_KEY
from utils.session_privacy import touch_private_session


HOME_VERSION = "v3.0.0"
HOME_CACHE_VERSION_LABEL = "v3-immersive-inquiry-hero"
HERO_BACKGROUND = Path(__file__).resolve().parents[1] / "assets" / "hero-sky-v1.png"
TYPEWRITER_QUESTIONS = (
    "今天我的运势如何？",
    "如何推算我的命盘？",
    "今年是我的本命年，我的事业和爱情怎么样？",
)


def _html(markup: str) -> None:
    """Render compact static HTML without Markdown code-block indentation."""
    normalized = "\n".join(line.strip() for line in dedent(markup).strip().splitlines())
    st.markdown(normalized, unsafe_allow_html=True)


def _queue_inquiry(question: str) -> bool:
    """Queue one question for the existing guarded AI inquiry flow."""
    normalized = str(question or "").strip()
    if not normalized:
        st.warning("请先输入一个问题。")
        return False
    if len(normalized) > 2000:
        st.warning("问题最多 2000 字，请精简后再试。")
        return False
    st.session_state[PENDING_QUESTION_KEY] = normalized
    touch_private_session(st.session_state)
    enter_app(st.session_state)
    st.session_state["navigate_to"] = "AI问答"
    st.rerun()
    return True


def _render_question_composer() -> None:
    """Render the enlarged Shadcn-powered question field."""
    with st.container(key="ms2-question-composer"):
        question_column, submit_column = st.columns([7, 1], vertical_alignment="bottom")
        with question_column:
            question = shadcn.input(
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
            _queue_inquiry(question)


def _render_immersive_hero() -> None:
    """Render the Origin-inspired hero using an original project-owned image."""
    with st.container(key="ms2-hero"):
        st.image(str(HERO_BACKGROUND), width="stretch")
        with st.container(key="ms2-hero-content"):
            _html(
                """
                <section class="ms2-hero-copy" id="ms2-main" tabindex="-1">
                  <h1><em>看见</em>你的命数。</h1>
                  <p class="ms2-hero-lede"><strong>从命盘出发，回答此刻真正关心的问题。</strong><br>
                  结合本地规则与 AI 分析，看见趋势、机遇与选择空间。</p>
                </section>
                """
            )
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
