"""首页 —— v3 immersive AI question landing page。"""

from __future__ import annotations

from core.bazi_engine import ensure_bazi_analysis_fields
from ui.bazi_components import CACHE_VERSION, compact_pillar_text, render_compact_bazi_summary
from ui.homepage_components import (
    HOME_CACHE_VERSION_LABEL,
    HOME_VERSION,
    render_homepage_landing,
)


def _compact_pillar_text(chart: dict) -> str:
    """兼容旧测试：首页只提供紧凑四柱摘要。"""
    return compact_pillar_text(chart)


def _clear_home_cache(st) -> None:
    """清理首页相关旧缓存，避免视觉更新后仍显示旧月度数据。"""
    try:
        st.cache_data.clear()
    except Exception:
        pass
    for key in [
        "current_yearly_data",
        "current_monthly_data",
        "current_monthly_event_results",
    ]:
        st.session_state.pop(key, None)


def render_home():
    import streamlit as st

    cache_version = f"{CACHE_VERSION}-{HOME_CACHE_VERSION_LABEL}-{HOME_VERSION}"
    if st.session_state.get("cache_version") != cache_version:
        st.session_state["cache_version"] = cache_version
        _clear_home_cache(st)

    chart = st.session_state.get("current_chart")
    if chart and not chart.get("error"):
        chart = ensure_bazi_analysis_fields(chart)
        st.session_state["current_chart"] = chart

    profile_data = st.session_state.get("current_profile")

    render_homepage_landing(
        chart=chart,
        profile_data=profile_data,
        render_compact_summary=render_compact_bazi_summary,
    )
