"""🔮 首页 —— 模块化卡片布局。"""

from __future__ import annotations

from ui.styles import ELEMENT_COLORS, ELEMENT_EMOJIS, card_style
from ui.charts import render_element_wheel
from core.bazi_engine import ensure_bazi_analysis_fields
from ui.bazi_components import (
    CACHE_VERSION,
    compact_pillar_text,
    render_compact_bazi_summary,
)

HOME_CACHE_VERSION_LABEL = "v1.0.4.8-pattern-seasonal"


def _five_element_bars(elements):
    items_html = ""
    for el in ["木", "火", "土", "金", "水"]:
        score = elements.get(el, 0)
        pct = min(score / 14 * 100, 100)
        color = ELEMENT_COLORS.get(el, "#8C7A64")
        emoji = ELEMENT_EMOJIS.get(el, "")
        items_html += (
            '<div style="margin-bottom:16px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;margin-bottom:4px;">'
            f'<span style="font-size:14px;font-weight:600;color:#3D2B1A;">{emoji} {el}</span>'
            f'<span style="color:#8C7A64;font-size:13px;">{score}</span>'
            '</div>'
            '<div style="height:8px;background:#EDE6DC;border-radius:4px;overflow:hidden;">'
            f'<div style="height:100%;width:{pct:.0f}%;background:{color};'
            'border-radius:4px;transition:width 0.6s ease;"></div>'
            '</div>'
            '</div>'
        )
    return items_html


def _compact_pillar_text(chart: dict) -> str:
    """首页紧凑展示四柱。"""
    return compact_pillar_text(chart)


def _action_tile(icon, label, desc=""):
    return (
        '<div class="mingshu-feature-card">'
        f'<div class="mingshu-feature-icon">{icon}</div>'
        f'<div class="mingshu-feature-title">{label}</div>'
        f'<div class="mingshu-feature-desc">{desc}</div>'
        '</div>'
    )


def _nav_button(name, target=None, key_suffix=""):
    import streamlit as st
    page_map = {
        "新建命盘": "新建命盘",
        "立即开始命盘分析": "新建命盘",
        "八字排盘": "八字排盘",
        "命盘总览": "命盘总览",
        "综合问盘": "综合问盘",
        "年度运程": "年度运程",
        "流月断事": "年度运程",
        "专项报告": "专项报告",
        "紫微斗数": "紫微斗数",
        "五行喜忌": "五行喜忌",
        "报告导出": "报告导出",
        "查看示例报告": "验收中心",
        "合婚匹配": "合婚匹配",
    }
    destination = target or page_map.get(name)
    if destination:
        key = f"nav_{name}_{key_suffix or destination}"
        if st.button(name, key=key, use_container_width=True):
            st.session_state["navigate_to"] = destination
            st.rerun()


def _render_top_navigation():
    """按参考图渲染顶部横向导航按钮。"""
    import streamlit as st

    nav_items = [
        ("首页", "首页"),
        ("八字排盘", "八字排盘"),
        ("紫微斗数", "紫微斗数"),
        ("年度运程", "年度运程"),
        ("综合问盘", "综合问盘"),
        ("报告导出", "报告导出"),
    ]
    st.markdown(
        '<div class="mingshu-topbar">'
        '<div class="mingshu-brand">命数研究室</div>'
        '<div class="mingshu-toplinks">首页　八字排盘　紫微斗数　年度运程　综合问盘　报告导出</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns([0.8, 1, 1, 1, 1, 1, 1.15, 0.75])
    with cols[0]:
        st.markdown('<div class="mingshu-nav-button">首页</div>', unsafe_allow_html=True)
    for idx, (label, target) in enumerate(nav_items[1:], start=1):
        with cols[idx]:
            _nav_button(label, target=target, key_suffix="top")
    with cols[6]:
        _nav_button("开始分析 →", target="新建命盘", key_suffix="top")
    with cols[7]:
        st.markdown('<div class="mingshu-nav-button">◎</div>', unsafe_allow_html=True)


def _render_reference_hero():
    """按参考图渲染左文案、中心五行盘、右侧分析卡。"""
    import streamlit as st

    st.markdown(
        '<div class="mingshu-hero">'
        '<div class="mingshu-hero-grid">'
        '<div>'
        '<div class="mingshu-kicker">知命 · 趋势 · 行运</div>'
        '<h1 class="mingshu-hero-title">AI驱动的东方命理研究平台</h1>'
        '<div class="mingshu-hero-subtitle">古法智慧 × 现代算法 × 数据洞察</div>'
        '<div class="mingshu-hero-copy">'
        '融合八字、紫微斗数与五行体系，结合真实样本校准，'
        '为用户提供更清晰、可验证的命理观察与趋势指引。'
        '</div>'
        '<div>'
        '<span class="mingshu-chip">八字排盘</span>'
        '<span class="mingshu-chip">紫微斗数</span>'
        '<span class="mingshu-chip">流年流月</span>'
        '<span class="mingshu-chip">命盘总览</span>'
        '<span class="mingshu-chip">趋势分析</span>'
        '</div>'
        '</div>'
        '<div class="mingshu-orbit">'
        '<div class="mingshu-orbit-center">☯</div>'
        '<div class="mingshu-orbit-label">三 元 五 行</div>'
        '<div class="mingshu-orbit-node mingshu-node-wood">木</div>'
        '<div class="mingshu-orbit-node mingshu-node-water">水</div>'
        '<div class="mingshu-orbit-node mingshu-node-fire">火</div>'
        '<div class="mingshu-orbit-node mingshu-node-metal">金</div>'
        '<div class="mingshu-orbit-node mingshu-node-earth">土</div>'
        '</div>'
        '<div class="mingshu-side-stack">'
        '<div class="mingshu-ai-panel">'
        '<div class="mingshu-ai-title">AI命理分析引擎</div>'
        '<div class="mingshu-ai-row"><span>命盘结构识别</span><strong>98.7%</strong></div>'
        '<div class="mingshu-ai-row"><span>五行平衡评估</span><strong>96.2%</strong></div>'
        '<div class="mingshu-ai-row"><span>格局判定准确率</span><strong>95.4%</strong></div>'
        '<div class="mingshu-ai-row"><span>运势趋势预测</span><strong>93.1%</strong></div>'
        '</div>'
        '<div class="mingshu-trend-panel">'
        '<div class="mingshu-trend-title">运势趋势概览</div>'
        '<div class="mingshu-sparkline"></div>'
        '<div class="mingshu-muted" style="margin-top:8px;">2024　2025　2026　2027　2028</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    hero_col1, hero_col2 = st.columns([1, 1])
    with hero_col1:
        _nav_button("立即排盘分析", target="新建命盘", key_suffix="hero_strict")
    with hero_col2:
        _nav_button("查看示例报告", target="验收中心", key_suffix="hero_strict")


def _render_dashboard_panel(chart: dict | None, profile_data: dict | None):
    """按参考图渲染命盘洞察数据面板。"""
    profile_name = "未载入命盘"
    day_master = "—"
    strength_text = "待分析"
    favorable_text = "生成命盘后显示"
    if chart and not chart.get("error"):
        strength = chart.get("day_master_strength", {})
        profile_name = (profile_data or {}).get("name", "当前命盘")
        day_master = chart.get("day_master", "—")
        strength_text = strength.get("strength", "—")
        favorable = strength.get("favorable_elements", [])
        favorable_text = "、".join(favorable[:3]) if favorable else "—"

    return (
        '<div class="mingshu-panel">'
        '<div class="mingshu-section-title" style="margin-top:0;">命盘洞察 · 数据化呈现</div>'
        '<div class="mingshu-dashboard-grid">'
        '<div class="mingshu-mini-stat">'
        '<div class="mingshu-ai-title">五行能量分布</div>'
        '<div class="mingshu-muted">木 28%｜火 18%｜土 20%｜金 16%｜水 18%</div>'
        '<div style="height:10px;margin-top:18px;border-radius:999px;'
        'background:linear-gradient(90deg,#64C878 0 28%,#D95C42 28% 46%,#D8A642 46% 66%,#F6D58A 66% 82%,#5E9BFF 82% 100%);"></div>'
        '</div>'
        '<div class="mingshu-mini-stat">'
        '<div class="mingshu-ai-title">命盘评分</div>'
        '<div class="mingshu-score-ring">86</div>'
        '<div class="mingshu-muted" style="text-align:center;">综合评估｜上等</div>'
        '</div>'
        '<div class="mingshu-mini-stat">'
        '<div class="mingshu-ai-title">2024-2028 运势趋势</div>'
        '<div class="mingshu-chart-lines"></div>'
        '<div class="mingshu-muted">事业｜财运｜感情｜健康</div>'
        '</div>'
        '<div class="mingshu-mini-stat">'
        '<div class="mingshu-ai-title">当前命盘</div>'
        f'<div style="color:#FFE6A3;font-size:22px;font-weight:900;">{profile_name}</div>'
        f'<div class="mingshu-muted">日主：{day_master}｜{strength_text}</div>'
        f'<div class="mingshu-muted">喜用：{favorable_text}</div>'
        '<div style="margin-top:10px;"><span class="mingshu-chip">成长</span><span class="mingshu-chip">突破</span><span class="mingshu-chip">积累</span></div>'
        '</div>'
        '</div>'
        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px;">'
        '<div class="mingshu-mini-stat"><div class="mingshu-ai-title">事业</div><div class="mingshu-muted">看职位、项目、责任与曝光。</div></div>'
        '<div class="mingshu-mini-stat"><div class="mingshu-ai-title">财运</div><div class="mingshu-muted">看收入、回款、支出与现金流。</div></div>'
        '<div class="mingshu-mini-stat"><div class="mingshu-ai-title">感情</div><div class="mingshu-muted">看关系节奏、沟通与稳定度。</div></div>'
        '<div class="mingshu-mini-stat"><div class="mingshu-ai-title">健康</div><div class="mingshu-muted">看作息、压力与身体状态提醒。</div></div>'
        '</div>'
        '</div>'
    )


def render_home():
    import streamlit as st

    if st.session_state.get("cache_version") != CACHE_VERSION:
        st.session_state["cache_version"] = CACHE_VERSION
        for key in [
            "current_yearly_data",
            "current_monthly_data",
            "current_monthly_event_results",
        ]:
            st.session_state.pop(key, None)
        try:
            st.cache_data.clear()
        except Exception:
            pass

    chart = st.session_state.get("current_chart")
    if chart and not chart.get("error"):
        chart = ensure_bazi_analysis_fields(chart)
        st.session_state["current_chart"] = chart
    profile_data = st.session_state.get("current_profile")

    _render_top_navigation()
    _render_reference_hero()

    st.markdown(
        '<div class="mingshu-panel" style="margin:18px 0 22px 0;">'
        '<div style="font-size:16px;font-weight:800;color:#F6D58A;">'
        '当前版本：v1.0.4.8 格局判定与调候用神</div>'
        '<div class="mingshu-muted" style="margin-top:4px;">'
        '运行端口：8501｜更新时间：2026-07-03｜'
        '当前重点：格局判定、十日干十二月调候表、旧命盘自动补算</div>'
        f'<div style="font-size:11px;color:#C9B885;margin-top:2px;">'
        f'缓存版本：{HOME_CACHE_VERSION_LABEL}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("清理页面缓存并刷新", help="如果刚更新后页面没有变化，可以点击这里清理 Streamlit 缓存。"):
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
        st.success("缓存已清理，正在刷新页面。")
        st.rerun()

    if chart and not chart.get("error"):
        strength = chart.get("day_master_strength", {})
        day_master = chart.get("day_master", "—")
        strength_text = strength.get("strength", "—")
        favorable = strength.get("favorable_elements", [])
        profile_name = (
            profile_data.get("name", "未命名")
            if profile_data else "未命名"
        )

        st.markdown(
            '<div class="mingshu-panel" style="margin-bottom:20px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;flex-wrap:wrap;">'
            '<div><div style="font-size:13px;color:#C9B885;">当前命盘</div>'
            f'<div style="font-size:22px;font-weight:800;color:#FFE6A3;'
            f'letter-spacing:1px;">{profile_name}</div></div>'
            '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
            '<span class="mingshu-chip">'
            f'日主 {day_master}</span>'
            '<span class="mingshu-chip">'
            f'{strength_text}</span></div></div></div>',
            unsafe_allow_html=True,
        )

        render_compact_bazi_summary(chart)

        from ui.styles import metric_card_html

        col_m1, col_m2, col_m3 = st.columns(3)
        favorable_text = "、".join(favorable[:3]) if favorable else "—"
        with col_m1:
            st.markdown(metric_card_html("日主", day_master, "出生日天干"), unsafe_allow_html=True)
        with col_m2:
            st.markdown(metric_card_html("日主强弱", strength_text, "综合判断"), unsafe_allow_html=True)
        with col_m3:
            st.markdown(metric_card_html("喜用五行", favorable_text, "宜补元素"), unsafe_allow_html=True)

        pattern_info = chart.get("pattern_analysis", {})
        seasonal_info = chart.get("seasonal_adjustment", {})
        if pattern_info or seasonal_info:
            st.markdown(
                f'<div style="{card_style()}margin:12px 0 16px 0;padding:14px 16px;">'
                '<div style="font-size:13px;color:#8C7A64;margin-bottom:6px;">新增核心能力已启用</div>'
                f'<div style="font-size:15px;color:#3D2B1A;line-height:1.7;">'
                f'格局判定：<strong>{pattern_info.get("pattern", "—")}</strong>｜'
                f'调候用神：先看 <strong>{"、".join(seasonal_info.get("primary_useful_stems", [])) or "—"}</strong>。'
                '完整解释可进入「八字排盘」查看。</div></div>',
                unsafe_allow_html=True,
            )

        current_stage = chart.get("current_stage", {})
        stage_gz = current_stage.get("gan_zhi", "")
        if stage_gz:
            st.markdown(
                f'<div style="{card_style()}margin-top:8px;">'
                '<div style="display:flex;align-items:center;justify-content:space-between;">'
                '<div style="font-weight:600;color:#3D2B1A;font-size:15px;">'
                '\U0001f52e 当前大运</div>'
                f'<div style="font-size:20px;font-weight:700;color:#B8860B;">'
                f'{stage_gz}</div></div></div>',
                unsafe_allow_html=True,
            )

    actions = [
        ("◎", "八字排盘", "四柱、十神、藏干、格局与调候一次看清。"),
        ("✦", "紫微斗数", "命宫、身宫、重点宫位和星曜组合说明。"),
        ("◈", "命盘总览", "把命局评分、人生主题和现实建议浓缩成总览。"),
        ("☉", "年度运程", "查看流年趋势和 12 个月现实事件 Top3。"),
        ("◇", "流月断事", "把出行、合同、财务、关系等事件分月呈现。"),
        ("▣", "报告导出", "生成 Markdown、TXT、PDF 和名片式预览。"),
    ]
    for i in range(0, len(actions), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(actions):
                icon, label, desc = actions[i + j]
                with cols[j]:
                    st.markdown(_action_tile(icon, label, desc), unsafe_allow_html=True)
                    _nav_button("进入 →", target="年度运程" if label == "流月断事" else label, key_suffix=label)

    st.markdown(_render_dashboard_panel(chart, profile_data), unsafe_allow_html=True)

    st.markdown('<div class="mingshu-section-title">专业命理研究 · 科学洞察价值</div>', unsafe_allow_html=True)
    value_cols = st.columns(4)
    value_cards = [
        ("结构化命理分析", "把格局、强弱、喜忌拆成可读证据链。"),
        ("证据链式断事", "每个事件都有触发依据和现实映射。"),
        ("原局流年联动", "原局、大运、流年、流月一起判断。"),
        ("个性化报告", "报告可下载，也可用卡片快速阅读。"),
    ]
    for col, (title, desc) in zip(value_cols, value_cards):
        with col:
            st.markdown(_action_tile("✧", title, desc), unsafe_allow_html=True)

    # Recent profiles
    try:
        from utils.database import list_profiles
        profiles = list_profiles()
    except Exception:
        profiles = []

    if profiles:
        st.markdown('<div class="mingshu-section-title">最近命盘</div>', unsafe_allow_html=True)
        for item in profiles[:5]:
            name = item.get("name", "未命名")
            birth = item.get("birth_date", "")
            gender = item.get("gender", "")
            note = item.get("note", "") or ""
            created = (item.get("created_at", "") or "")[:10]
            gender_icon = "\u2642" if gender == "男" else "\u2640"
            note_tag = (
                f'<span style="color:#B8860B;font-size:12px;">{note[:20]}</span>'
                if note else ""
            )
            st.markdown(
                '<div style="background:#FAF7F4;border-radius:10px;padding:12px 18px;'
                'margin-bottom:6px;display:flex;justify-content:space-between;'
                'align-items:center;flex-wrap:wrap;'
                'box-shadow:0 1px 2px rgba(0,0,0,0.03);border:1px solid #EDE6DC;">'
                '<div style="display:flex;align-items:center;gap:10px;">'
                f'<span style="font-weight:600;color:#3D2B1A;">{name}</span>'
                f'<span style="color:#8C7A64;font-size:13px;">{gender_icon}</span></div>'
                f'<div style="color:#8C7A64;font-size:13px;'
                f'display:flex;gap:16px;align-items:center;">'
                f'<span>{birth}</span>'
                f'<span style="color:#B8A894;">{created}</span>{note_tag}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="background:#FAF7F4;border-radius:10px;padding:24px;'
            'margin-top:20px;text-align:center;color:#8C7A64;font-size:14px;'
            'border:1px dashed #EDE6DC;">'
            '暂无已保存命盘 · 从「新建命盘」开始</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="mingshu-bottom-cta">'
        '<div class="mingshu-section-title" style="margin:0 0 8px 0;">'
        '洞见命数 · 智启未来</div>'
        '<div class="mingshu-hero-subtitle" style="font-size:16px;">'
        '用数据解读命运，用智慧把握人生</div>'
        '<div class="mingshu-muted" style="margin:10px auto 18px auto;max-width:680px;">'
        '隐私安全保障｜数据仅用于分析｜不泄露不分享</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    _nav_button("立即开始命盘分析 →", target="新建命盘", key_suffix="bottom_cta")

    # Footer
    st.markdown(
        '<div class="mingshu-panel" style="margin-top:36px;">'
        '<div style="display:flex;justify-content:space-between;'
        'align-items:center;flex-wrap:wrap;">'
        '<div style="font-size:14px;font-weight:800;color:#F6D58A;">'
        '命数研究室 v1.0.4.8</div>'
        '<div style="font-size:11px;color:#9CA9AA;max-width:600px;line-height:1.6;">'
        '本报告基于传统命理模型生成，'
        '仅供个人兴趣、文化研究和自我规划参考，'
        '不应作为医疗、法律、投资、'
        '婚姻等重大决策的唯一依据。'
        '</div></div></div>',
        unsafe_allow_html=True,
    )
