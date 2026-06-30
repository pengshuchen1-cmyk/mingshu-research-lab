"""🔮 首页 —— 模块化卡片布局。"""

from __future__ import annotations

from ui.styles import ELEMENT_COLORS, ELEMENT_EMOJIS, card_style
from ui.charts import render_element_wheel
from ui.bazi_components import (
    CACHE_VERSION,
    compact_pillar_text,
    render_compact_bazi_summary,
)

HOME_CACHE_VERSION_LABEL = "v1.0.2-professional-monthly-events"


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
    desc_html = (
        f'<div style="font-size:12px;color:#8C7A64;margin-top:2px;">{desc}</div>'
        if desc else ""
    )
    return (
        '<div style="background:#FAF7F4;border-radius:12px;padding:16px 14px;'
        'text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.05);'
        'border:1px solid #EDE6DC;height:100%;">'
        f'<div style="font-size:28px;margin-bottom:6px;">{icon}</div>'
        f'<div style="font-size:14px;font-weight:600;color:#3D2B1A;">{label}</div>'
        f'{desc_html}</div>'
    )


def _nav_button(name):
    import streamlit as st
    page_map = {
        "新建命盘": "新建命盘",
        "八字排盘": "八字排盘",
        "综合问盘": "综合问盘",
        "紫微斗数": "紫微斗数",
        "五行喜忌": "五行喜忌",
    }
    if name in page_map:
        key = f"nav_{name}"
        if st.button(name, key=key, use_container_width=True):
            st.session_state["navigate_to"] = page_map[name]
            st.rerun()


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
    profile_data = st.session_state.get("current_profile")

    # Hero
    st.markdown(
        '<div style="background:linear-gradient(135deg,#3D2B1A 0%,#5C4A32 100%);'
        'border-radius:16px;padding:32px 36px;margin-bottom:28px;'
        'box-shadow:0 4px 12px rgba(61,43,26,0.15);">'
        '<h1 style="color:#FCF8F0;font-size:32px;letter-spacing:4px;'
        'font-weight:700;margin:0 0 6px 0;">\U0001f52e 命数研究室</h1>'
        '<p style="color:#D4C5B0;font-size:15px;margin:0 0 18px 0;letter-spacing:1px;">'
        '八字 · 紫微斗数 · 命理分析</p>'
        '<div style="display:flex;gap:12px;flex-wrap:wrap;">'
        '<span style="background:rgba(255,255,255,0.1);color:#D4C5B0;'
        'padding:4px 14px;border-radius:20px;font-size:12px;">\u2726 本机离线</span>'
        '<span style="background:rgba(255,255,255,0.1);color:#D4C5B0;'
        'padding:4px 14px;border-radius:20px;font-size:12px;">\u2726 数据不上传</span>'
        '<span style="background:rgba(255,255,255,0.1);color:#D4C5B0;'
        'padding:4px 14px;border-radius:20px;font-size:12px;">\u2726 多维度交叉分析</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="background:#FAF7F4;border:1px solid #D4C5B0;'
        'border-radius:12px;padding:14px 18px;margin:-12px 0 22px 0;">'
        '<div style="font-size:16px;font-weight:700;color:#3D2B1A;">'
        '当前版本：v1.0.2 专业流月断事增强</div>'
        '<div style="font-size:13px;color:#5C4A32;line-height:1.8;margin-top:4px;">'
        '运行端口：8501｜更新时间：2026-06-27｜'
        '当前重点：流月对象化事件、五行深度解释、报告差异化</div>'
        f'<div style="font-size:11px;color:#8C7A64;margin-top:2px;">'
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

    # Dashboard with wheel chart
    if chart and not chart.get("error"):
        strength = chart.get("day_master_strength", {})
        day_master = chart.get("day_master", "—")
        strength_text = strength.get("strength", "—")
        favorable = strength.get("favorable_elements", [])
        five_elements_raw = chart.get("five_elements", {})
        profile_name = (
            profile_data.get("name", "未命名")
            if profile_data else "未命名"
        )

        st.markdown(
            f'<div style="{card_style()}margin-bottom:20px;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;flex-wrap:wrap;">'
            '<div><div style="font-size:13px;color:#8C7A64;">当前命盘</div>'
            f'<div style="font-size:22px;font-weight:700;color:#3D2B1A;'
            f'letter-spacing:1px;">{profile_name}</div></div>'
            '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
            '<span style="background:#EDE6DC;padding:4px 12px;'
            'border-radius:6px;font-size:12px;color:#5C4A32;">'
            f'日主 {day_master}</span>'
            '<span style="background:#EDE6DC;padding:4px 12px;'
            'border-radius:6px;font-size:12px;color:#5C4A32;">'
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

        # ★ 五行轮盘 + 详情并排
        col_left, col_right = st.columns([4, 3])
        with col_left:
            st.markdown(
                '<div style="font-weight:600;color:#3D2B1A;font-size:16px;'
                'margin-bottom:8px;text-align:center;">\U0001f300 五行轮盘</div>',
                unsafe_allow_html=True,
            )
            render_element_wheel(five_elements_raw, key="home_wheel", width=420, animated=True)

        with col_right:
            st.markdown(
                f'<div style="{card_style()}height:100%;">'
                '<div style="font-weight:600;color:#3D2B1A;font-size:15px;'
                'margin-bottom:12px;">\u2696 五行分布详情</div>'
                f'{_five_element_bars(five_elements_raw)}</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div style="font-weight:600;color:#3D2B1A;font-size:14px;'
                'margin:16px 0 8px 0;">快捷分析</div>',
                unsafe_allow_html=True,
            )
            _nav_button("五行喜忌")

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

    # Feature tiles
    st.markdown(
        '<div style="font-weight:600;color:#3D2B1A;font-size:18px;'
        'margin:32px 0 16px 0;">功能总览</div>',
        unsafe_allow_html=True,
    )

    actions = [
        ("\U0001f4cb", "新建命盘", "录入个人信息"),
        ("\U0001f4ca", "八字排盘", "四柱八字分析"),
        ("\U0001f4c8", "综合问盘", "多维度综合解读"),
        ("\U0001f525", "五行喜忌", "五行强弱与调候"),
        ("\U0001f52e", "紫微斗数", "十四主星宫位盘"),
        ("\u2764\ufe0f", "合婚匹配", "双人命盘对比"),
    ]
    for i in range(0, len(actions), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(actions):
                icon, label, desc = actions[i + j]
                with cols[j]:
                    st.markdown(_action_tile(icon, label, desc), unsafe_allow_html=True)

    # Recent profiles
    try:
        from utils.database import list_profiles
        profiles = list_profiles()
    except Exception:
        profiles = []

    if profiles:
        st.markdown(
            '<div style="font-weight:600;color:#3D2B1A;font-size:18px;'
            'margin:32px 0 16px 0;">最近命盘</div>',
            unsafe_allow_html=True,
        )
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

    # Footer
    st.markdown(
        '<div style="margin-top:36px;padding:16px 20px;background:#3D2B1A;'
        'border-radius:12px;">'
        '<div style="display:flex;justify-content:space-between;'
        'align-items:center;flex-wrap:wrap;">'
        '<div style="font-size:14px;font-weight:600;color:#D4C5B0;">'
        '命数研究室 v1.0.2</div>'
        '<div style="font-size:11px;color:#8C7A64;max-width:600px;line-height:1.6;">'
        '本报告基于传统命理模型生成，'
        '仅供个人兴趣、文化研究和自我规划参考，'
        '不应作为医疗、法律、投资、'
        '婚姻等重大决策的唯一依据。'
        '</div></div></div>',
        unsafe_allow_html=True,
    )
