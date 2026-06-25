"""合婚匹配页面 —— 支持已保存命盘的双人配对分析。"""

from __future__ import annotations

from ui.styles import card_style


def render_compatibility_page() -> None:
    """渲染合婚匹配页面。"""
    import streamlit as st
    import pandas as pd
    from core.bazi_engine import build_bazi_chart
    from core.compatibility import analyze_compatibility
    from utils.database import list_profiles, save_profile

    st.markdown("## 💑 合婚匹配")
    st.markdown(
        f'<div style="{card_style()}margin-bottom:16px;font-size:13px;color:#5C4A32;'
        f'line-height:1.6;">'
        f'从已保存的命盘中选择两位进行八字合盘分析。'
        f'基于日主五行、地支关系、五行互补、十神互参等维度做综合评判。</div>',
        unsafe_allow_html=True,
    )

    # 从数据库获取已保存的命盘
    try:
        profiles = list_profiles()
    except Exception:
        profiles = []

    if len(profiles) < 2:
        st.info("需要至少保存两个命盘才能进行合婚匹配。请先在「新建命盘」页面创建并保存命盘。")
        return

    # 创建选择器
    col1, col2 = st.columns(2)
    profile_options = {f"{p.get('name','未命名')} ({p.get('birth_date','')})": p for p in profiles}

    with col1:
        st.markdown("**甲方（命主）**")
        selected_1 = st.selectbox(
            "选择第一个命盘",
            list(profile_options.keys()),
            key="compat_p1",
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**乙方（对方）**")
        selected_2 = st.selectbox(
            "选择第二个命盘",
            list(profile_options.keys()),
            key="compat_p2",
            label_visibility="collapsed",
        )

    if st.button("开始合盘分析", type="primary"):
        if selected_1 == selected_2:
            st.warning("请选择两个不同的命盘进行合婚匹配。")
            return

        profile1 = profile_options[selected_1]
        profile2 = profile_options[selected_2]

        chart1 = build_bazi_chart(profile1)
        chart2 = build_bazi_chart(profile2)

        if chart1.get("error") or chart2.get("error"):
            st.error(f"命盘生成失败：{chart1.get('error', '')} {chart2.get('error', '')}")
            return

        result = analyze_compatibility(chart1, chart2)

        show_ = lambda name, chart: f"{name}：{chart.get('day_master','')}日 {'、'.join(p.get('pillar','') for p in chart.get('pillars',{}).values())}"

        st.markdown(f"<div style='margin:16px 0;'></div>", unsafe_allow_html=True)

        # 总分卡片
        score = result["overall_score"]
        level = result["level"]
        color = "#8BA888" if score >= 70 else "#B8860B" if score >= 55 else "#B85C4A" if score < 40 else "#C4A882"

        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:12px;padding:20px;'
            f'text-align:center;border:2px solid {color};margin-bottom:16px;">'
            f'<div style="font-size:14px;color:#8C7A64;margin-bottom:4px;">合婚匹配总分</div>'
            f'<div style="font-size:42px;font-weight:800;color:{color};">{score}</div>'
            f'<div style="font-size:16px;color:#3D2B1A;font-weight:600;margin:6px 0;">等级：{level}</div>'
            f'<div style="font-size:13px;color:#5C4A32;margin-top:4px;">{result["summary"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 维度详情
        st.markdown("### 📊 各维度评分")
        dim_rows = []
        for dim in result["dimensions"]:
            pct = int(dim["score"] / dim["max_score"] * 100)
            dim_rows.append({
                "维度": dim["label"],
                "得分": f'{dim["score"]}/{dim["max_score"]}',
                "百分比": pct,
                "说明": dim["text"],
            })

        for dim in dim_rows:
            pct = dim["百分比"]
            bar_color = "#8BA888" if pct >= 70 else "#B8860B" if pct >= 50 else "#B85C4A"
            st.markdown(
                f'<div style="margin:8px 0;">'
                f'<div style="display:flex;justify-content:space-between;font-size:13px;color:#5C4A32;">'
                f'<span>{dim["维度"]}</span>'
                f'<span>{dim["得分"]}</span></div>'
                f'<div style="height:8px;background:#EDE6DC;border-radius:4px;overflow:hidden;margin:2px 0;">'
                f'<div style="width:{pct}%;height:100%;background:{bar_color};border-radius:4px;"></div></div>'
                f'<div style="font-size:12px;color:#8C7A64;">{dim["说明"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 命盘详情
        st.markdown("### 📜 双方命盘")
        c1, c2 = st.columns(2)
        for col, name, chart in [(c1, "甲方", chart1), (c2, "乙方", chart2)]:
            with col:
                profile = chart.get("profile", {})
                pillars = chart.get("pillars", {})
                dm = chart.get("day_master", "")
                strength = chart.get("day_master_strength", {})
                st.markdown(
                    f'<div style="background:#FAF7F4;border-radius:10px;padding:12px;'
                    f'box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
                    f'<div style="font-weight:600;color:#3D2B1A;margin-bottom:6px;">{name}</div>'
                    f'<div style="font-size:12px;color:#5C4A32;line-height:1.6;">'
                    f'{profile.get("name","")} &middot; {profile.get("birth_date","")}<br>'
                    f'日主: {dm} &middot; {strength.get("strength","")}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-top:8px;">',
                    unsafe_allow_html=True,
                )
                cols = st.columns(4)
                for i, key in enumerate(["year", "month", "day", "hour"]):
                    p = pillars.get(key, {})
                    with cols[i]:
                        st.markdown(
                            f'<div style="text-align:center;background:#EDE6DC;'
                            f'border-radius:6px;padding:4px 2px;">'
                            f'<div style="font-size:11px;color:#8C7A64;">{p.get("name","")}</div>'
                            f'<div style="font-size:16px;font-weight:700;color:#3D2B1A;">{p.get("pillar","")}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("</div></div>", unsafe_allow_html=True)

        # 维度详情展开
        st.markdown("### 📖 各维度详解")
        for dim in result["dimensions"]:
            with st.expander(f"{dim['label']}（{dim['score']}/{dim['max_score']}分）"):
                st.markdown(dim["text"])
                if dim.get("detail"):
                    st.caption(dim["detail"])

        st.caption("本合婚分析基于传统八字命理模型，仅供个人兴趣和文化研究参考，不应作为重大决策的唯一依据。")
