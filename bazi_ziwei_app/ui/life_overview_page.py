"""命盘总览页面 —— v1.1-A2 命盘总体结论。"""

from __future__ import annotations

import streamlit as st

from core.life_overview_engine import analyze_life_overview
from core.chart_fingerprint import build_chart_fingerprint
from ui.styles import ELEMENT_COLORS, card_style


def _level_color(level: str) -> str:
    colors = {
        "偏强": "#8BA888", "中上": "#B8860B",
        "中等": "#7A9BAE", "需经营": "#C4A882",
        "波动较大": "#B85C4A",
    }
    return colors.get(level, "#8C7A64")


def _score_to_level(score: int) -> str:
    if score >= 80: return "偏强"
    elif score >= 65: return "中上"
    elif score >= 45: return "中等"
    elif score >= 30: return "需经营"
    else: return "波动较大"


def render_life_overview_page():
    """渲染命盘总览页面。"""
    chart = st.session_state.get("current_chart")
    if not chart:
        st.info("请先在「新建命盘」页面生成命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    profile = chart.get("profile", {})
    luck_data = st.session_state.get("current_luck_data")

    try:
        dp = analyze_life_overview(chart, luck_data)
    except Exception as e:
        st.error(f"命盘总览生成失败：{e}")
        return

    st.title("📊 命盘总览")
    st.caption(f"命盘：{profile.get('name', '未命名')} | {dp['overall_pattern']}")

    # ===== 1. 总体类型卡片 =====
    keywords = dp.get("life_keywords", [])
    tags_html = "".join(
        f'<span style="display:inline-block;background:#EDE6DC;color:#5C4A32;'
        f'border-radius:12px;padding:4px 12px;font-size:13px;margin:3px 4px;">{kw}</span>'
        for kw in keywords[:6]
    )
    st.markdown(
        f'<div style="background:#FAF7F4;border-radius:14px;padding:16px;'
        f'border:1px solid #EDE6DC;box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:16px;">'
        f'<div style="font-size:16px;font-weight:600;color:#3D2B1A;margin-bottom:8px;">'
        f'命盘总体类型：{dp["overall_pattern"]}</div>'
        f'<div style="font-size:13px;color:#5C4A32;line-height:1.7;margin-bottom:8px;">'
        f'{dp["overall_summary"]}</div>'
        f'<div>{tags_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ===== 2. 四个维度卡片 =====
    st.markdown("### 各维度总览")
    sections_data = [
        ("💰 财富潜力", dp["wealth_overview"], "wealth"),
        ("💞 桃花感情", dp["romance_overview"], "romance"),
        ("🏥 健康稳定", dp["health_overview"], "health"),
        ("💼 事业发展", dp["career_overview"], "career"),
    ]

    for label, data, key in sections_data:
        level = data.get(f"{key}_level" if key != "wealth" else "wealth_level",
                         data.get("wealth_level") or data.get("romance_level") or
                         data.get("health_stability_level") or data.get("career_type", "中等"))
        score = data.get(f"{key}_score" if key != "wealth" else "wealth_score",
                         data.get("wealth_score") or data.get("romance_score") or
                         data.get("health_score") or data.get("career_score", 50))
        summary = data.get(f"{key}_summary", data.get("wealth_summary") or "暂无")

        # Extract type
        wealth_type = data.get("wealth_type", "")
        romance_type = data.get("romance_type", "")
        career_type = data.get("career_type", "")
        stable_type = data.get("health_stability_level", "")
        subtype = wealth_type or romance_type or career_type or stable_type or ""

        color = _level_color(_score_to_level(score if isinstance(score, int) else 50))

        with st.expander(f"{label} — {_score_to_level(score if isinstance(score, int) else 50)}", expanded=False):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(
                    f'<div style="text-align:center;padding:12px;background:#FAF7F4;'
                    f'border-radius:10px;border:1px solid #EDE6DC;">'
                    f'<div style="font-size:28px;font-weight:700;color:{color};">'
                    f'{score if isinstance(score, int) else 50}</div>'
                    f'<div style="font-size:12px;color:#8C7A64;">{_score_to_level(score if isinstance(score, int) else 50)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(f"**类型**：{subtype}" if subtype else "")
                st.markdown(summary[:200] if len(summary) > 200 else summary)

            # Details
            details = data.get("details", {}) or {}
            if details:
                for detail_key, detail_items in details.items():
                    if detail_items:
                        st.markdown(f"**{detail_key}**")
                        for item in detail_items[:4]:
                            st.markdown(f"- {item}")

    # ===== 3. 五个评分 =====
    st.markdown("### 📈 五维评分")
    scores = dp.get("scores", {})
    cols = st.columns(5)
    score_labels = [
        ("💰 财富", "wealth", "#8BA888"),
        ("💞 感情", "romance", "#D4A843"),
        ("🏥 健康", "health_stability", "#7A9BAE"),
        ("💼 事业", "career", "#B8860B"),
        ("⚖ 平衡", "overall_balance", "#C4A882"),
    ]
    for i, (label, key, color) in enumerate(score_labels):
        val = scores.get(key, 50)
        level_name = _score_to_level(val)
        with cols[i]:
            st.markdown(
                f'<div style="text-align:center;padding:10px;background:#FAF7F4;'
                f'border-radius:10px;border:1px solid #EDE6DC;">'
                f'<div style="font-size:11px;color:#8C7A64;">{label}</div>'
                f'<div style="font-size:28px;font-weight:700;color:{color};">{val}</div>'
                f'<div style="font-size:12px;color:{color};">{level_name}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ===== 4. 优势与隐患 =====
    col_s, col_r = st.columns(2)
    with col_s:
        st.markdown("### ✅ 命盘优势")
        strengths = dp.get("key_strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"- {s}")
        else:
            st.markdown("暂无明显突出优势，需结合大运流年进一步观察。")

    with col_r:
        st.markdown("### ⚠️ 命盘隐患")
        risks = dp.get("key_risks", [])
        if risks:
            for r in risks:
                st.markdown(f"- {r}")
        else:
            st.markdown("暂无明显突出隐患，但仍建议结合现实情况谨慎决策。")

    # ===== 5. 长期建议 =====
    st.markdown("### 📋 长期建议")
    for advice in dp.get("long_term_advice", []):
        st.markdown(f"- {advice}")

    # ===== 6. 命理依据 =====
    with st.expander("📚 命理依据 / 参考来源", expanded=False):
        st.markdown("**判断依据**：")
        for ev in dp.get("evidence", []):
            st.markdown(f"- {ev}")
        st.markdown("")
        st.markdown(f"**参考来源**：{'、'.join(dp.get('source_titles', []))}")

    # ===== 7. 健康免责声明 =====
    health = dp.get("health_overview", {})
    disclaimer = health.get("medical_disclaimer", "")
    if disclaimer:
        st.caption(disclaimer)

    st.divider()
    st.caption("本报告基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考。")
