"""八字展示公共组件，避免四柱信息在多个页面重复堆叠。"""

from __future__ import annotations

import streamlit as st

from core.di_shi_explanations import get_di_shi_color
from ui.styles import card_style


CACHE_VERSION = "v1.0.4.8-pattern-seasonal"

PILLAR_KEYS = ["year", "month", "day", "hour"]
PILLAR_LABELS = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}


def compact_pillar_text(chart: dict, with_labels: bool = False) -> str:
    """生成紧凑四柱摘要。"""
    pillars = chart.get("pillars", {}) if chart else {}
    parts = []
    for key in PILLAR_KEYS:
        pillar = pillars.get(key, {})
        value = pillar.get("pillar", "")
        if not value:
            continue
        if with_labels:
            parts.append(f"{PILLAR_LABELS[key]}：{value}")
        else:
            parts.append(value)
    separator = "｜" if with_labels else " · "
    return separator.join(parts)


def _element_list_text(elements: list[str]) -> str:
    return "、".join(elements) if elements else "需结合大运流年进一步判断"


def render_compact_bazi_summary(chart: dict) -> None:
    """只显示一行紧凑四柱摘要，主要用于首页命盘名片。"""
    text = compact_pillar_text(chart, with_labels=True)
    if not text:
        return
    st.markdown(
        f'<div class="ms-bazi-card" style="margin:-6px 0 16px 0;">'
        f'<div class="ms-bazi-label" style="margin-bottom:4px;">四柱摘要</div>'
        f'<div class="ms-bazi-value" style="font-size:18px;letter-spacing:1px;">{text}</div>'
        f'<div class="ms-bazi-muted" style="margin-top:4px;">'
        f'首页作为命盘名片展示；完整四柱请到「八字排盘」。</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_rule_summary(chart: dict) -> None:
    """Render the eight approved customer-facing rule conclusions."""
    summary = chart.get("public_summary", {}) if chart else {}
    if not summary:
        return
    st.markdown("### 四柱规则摘要")
    for label, value in summary.items():
        if isinstance(value, list):
            text = "；".join(str(item) for item in value if item) or "待分析"
        else:
            text = str(value or "待分析")
        st.markdown(f"**{label}**：{text}")


def render_loaded_profile_hint(profile: dict | None, chart: dict) -> None:
    """在非排盘页显示简短命盘提示，不重复完整四柱。"""
    profile = profile or chart.get("profile", {}) or {}
    strength = chart.get("day_master_strength", {}) or {}
    current_stage = chart.get("current_stage", {}) or {}
    name = profile.get("name", "未命名")
    day_master = chart.get("day_master", "—")
    chart_type = strength.get("strength", "—")
    favorable = _element_list_text(strength.get("favorable_elements", []))
    unfavorable = _element_list_text(strength.get("unfavorable_elements", []))
    stage = current_stage.get("gan_zhi") or current_stage.get("pillar") or "可在大运流年页查看"
    st.markdown(
        f'<div style="{card_style()}margin-bottom:14px;padding:12px 16px;">'
        f'<div class="ms-bazi-label" style="margin-bottom:4px;">当前已加载命盘</div>'
        f'<div class="ms-bazi-text" style="font-size:14px;line-height:1.8;">'
        f'姓名：<strong>{name}</strong>｜日主：<strong>{day_master}</strong>｜'
        f'命盘类型：<strong>{chart_type}</strong>｜喜用：<strong>{favorable}</strong>｜'
        f'忌神：<strong>{unfavorable}</strong>｜当前大运：<strong>{stage}</strong>'
        f'</div>'
        f'<div class="ms-bazi-muted" style="margin-top:4px;">'
        f'如需查看年柱、月柱、日柱、时柱、藏干、十神、纳音、旬空和十二长生，请前往「八字排盘」。'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _hidden_text(items: list[dict]) -> str:
    return "、".join(f"{item.get('gan', '')}({item.get('ten_god', '')})" for item in items)


def render_full_bazi_chart(chart: dict) -> None:
    """只在八字排盘页和导出报告中使用，显示完整四柱。"""
    pillars = chart.get("pillars", {}) or {}
    ten_gods = chart.get("ten_gods", {}) or {}
    hidden_stems = chart.get("hidden_stems", {}) or {}

    st.caption("这里是唯一完整展示四柱的位置，便于集中查看天干地支、藏干、十神、纳音、旬空和十二长生。")
    cols = st.columns(4)
    for index, key in enumerate(PILLAR_KEYS):
        pillar = pillars.get(key, {}) or {}
        gan_ten_god = (ten_gods.get(key, {}) or {}).get("gan", "")
        hidden = hidden_stems.get(key, []) or (ten_gods.get(key, {}) or {}).get("hidden_stems", []) or []
        name = pillar.get("name") or PILLAR_LABELS[key]
        na_yin = pillar.get("na_yin", "")
        xun_kong = pillar.get("xun_kong", "")
        di_shi = pillar.get("di_shi", "")
        di_shi_color = get_di_shi_color(di_shi)
        hidden_line = _hidden_text(hidden) if hidden else "—"
        day_label = (
            '<div class="ms-bazi-accent" style="font-size:10px;margin-top:2px;">★ 日主</div>'
            if key == "day"
            else ""
        )
        card_class = "ms-bazi-pillar-card day" if key == "day" else "ms-bazi-pillar-card"
        with cols[index]:
            st.markdown(
                f'<div class="{card_class}">'
                f'<div class="ms-bazi-label" style="margin-bottom:2px;">{name}</div>'
                f'<div class="ms-bazi-value">'
                f'{pillar.get("pillar", "—")}</div>'
                f'<div class="ms-bazi-accent" style="font-size:12px;margin-top:4px;">'
                f'{gan_ten_god or "—"}</div>'
                f'<div class="ms-bazi-text" style="font-size:11px;line-height:1.6;margin-top:4px;">'
                f'藏干：{hidden_line}</div>'
                f'<div class="ms-bazi-muted" style="font-size:11px;line-height:1.6;margin-top:4px;">'
                f'纳音：{na_yin or "—"}｜旬空：{xun_kong or "—"}</div>'
                f'<div style="font-size:11px;color:{di_shi_color};line-height:1.6;">'
                f'十二长生：{di_shi or "—"}</div>'
                f'{day_label}'
                f'</div>',
                unsafe_allow_html=True,
            )
