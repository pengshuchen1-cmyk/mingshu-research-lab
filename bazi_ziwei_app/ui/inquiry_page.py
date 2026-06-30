"""综合问盘页面 —— 一屏展示命盘所有核心信息。"""

from __future__ import annotations

from datetime import date

import pandas as pd
import altair as alt
import streamlit as st

from core.five_elements import element_summary

from ui.styles import ELEMENT_COLORS, ELEMENT_EMOJIS, card_style, element_tag

PILLAR_NAMES = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}


def _element_list_text(elements: list[str]) -> str:
    return "、".join(elements) if elements else "需结合大运流年进一步判断"


def _render_pillar_section(chart: dict) -> None:
    """四柱大卡片展示。"""
    pillars = chart.get("pillars", {})
    day_master = chart.get("day_master", "")
    lunar_text = chart.get("lunar_text", "")

    st.markdown("### 四柱八字")
    st.caption(f"农历：{lunar_text}" if lunar_text else "")

    cols = st.columns(5)
    pillar_keys = ["year", "month", "day", "hour"]
    for idx, key in enumerate(pillar_keys):
        p = pillars.get(key, {})
        gan = p.get("gan", "")
        zhi = p.get("zhi", "")
        pillar_str = p.get("pillar", "")
        name = PILLAR_NAMES.get(key, "")

        # Highlight the day pillar (日主)
        is_day = key == "day"
        border_color = "#B8860B" if is_day else "#EDE6DC"
        bg_color = "B8860B" if is_day else "FAF7F4"
        with cols[idx]:
            st.markdown(
                f'<div style="border:2px solid {border_color};border-radius:12px;'
                f'padding:14px 6px;text-align:center;background:#{bg_color}15;">'
                f'<div style="font-size:13px;color:#888;margin-bottom:4px;">{name}</div>'
                f'<div style="font-size:28px;font-weight:800;letter-spacing:2px;">{pillar_str}</div>'
                f'<div style="font-size:13px;color:#666;margin-top:4px;">'
                f'{gan} {ELEMENT_COLORS.get(chart.get("day_master_strength", {}).get("favorable_elements", [""])[0] if False else "", "#888")}'
                f'{_get_gan_element(gan)}<br>{zhi} {_get_zhi_element(zhi)}'
                f"</div>"
                f'<div style="font-size:12px;color:#999;margin-top:2px;">'
                f'{_get_ten_god_display(chart, key)}'
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with cols[4]:
        strength = chart.get("day_master_strength", {})
        st.markdown(
            f'<div style="border:2px solid #FF5722;border-radius:12px;'
            f'padding:14px 6px;text-align:center;background:#FF572215;">'
            f'<div style="font-size:13px;color:#888;margin-bottom:4px;">日主</div>'
            f'<div style="font-size:28px;font-weight:800;">{day_master}</div>'
            f'<div style="font-size:13px;font-weight:600;color:#FF5722;margin-top:4px;">'
            f'{strength.get("strength", "")}'
            f"</div>"
            f'<div style="font-size:11px;color:#999;margin-top:4px;">'
            f'净评分 {strength.get("net_score", 0):+.1f}'
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def _get_gan_element(gan: str) -> str:
    from core.bazi_constants import STEM_ELEMENTS
    return STEM_ELEMENTS.get(gan, "")


def _get_zhi_element(zhi: str) -> str:
    from core.bazi_constants import BRANCH_MAIN_ELEMENTS
    return BRANCH_MAIN_ELEMENTS.get(zhi, "")


def _get_ten_god_display(chart: dict, key: str) -> str:
    ten_gods = chart.get("ten_gods", {}).get(key, {})
    gan_tg = ten_gods.get("gan", "")
    hidden = ten_gods.get("hidden_stems", [])
    hidden_str = "、" . join(
        f'{h["gan"]}({h.get("ten_god", "")})' for h in hidden[:2]
    ) if hidden else ""
    parts = [gan_tg] if gan_tg else []
    if hidden_str:
        parts.append(hidden_str)
    return " | ".join(parts) if parts else ""


def _render_profile_card(profile: dict) -> None:
    """个人信息卡片。"""
    if not profile:
        return
    name = profile.get("name", "未命名")
    gender = profile.get("gender", "")
    birth = profile.get("birth_date", "")
    hour = profile.get("birth_hour", 0)
    minute = profile.get("birth_minute", 0)
    place = profile.get("birth_place", "")
    st.markdown(
        f'<div style="background:#f8f9fa;border-radius:12px;padding:12px 18px;'
        f'border:1px solid #e0e0e0;margin-bottom:8px;">'
        f'<span style="font-size:18px;font-weight:700;">{name}</span>'
        f'<span style="margin:0 12px;color:#ccc;">|</span>'
        f'{gender} · {birth} {hour:02d}:{minute:02d}'
        + (f" · {place}" if place else "")
        + f"</div>",
        unsafe_allow_html=True,
    )


def _render_element_visual(chart: dict) -> None:
    """五行可视化区块：环图 + 柱状图。"""
    five_elements = chart.get("five_elements", {})
    if not five_elements:
        return
    summary = element_summary(five_elements)

    st.markdown("### 🌟 五行概览")
    cards_html = ""
    for element, info in summary.items():
        color = ELEMENT_COLORS.get(element, "#888")
        emoji = ELEMENT_EMOJIS.get(element, "")
        ratio = info["ratio"]
        strength = info["strength"]
        cards_html += (
            f'<div style="flex:1;background:{color}15;border:1px solid {color}40;'
            f'border-radius:10px;padding:8px 4px;text-align:center;margin:0 3px;">'
            f'<div style="font-size:20px;">{emoji}</div>'
            f'<div style="font-size:14px;font-weight:700;color:{color};">{element}</div>'
            f'<div style="font-size:20px;font-weight:800;color:{color};">{ratio}%</div>'
            f'<div style="font-size:11px;color:#666;">{strength}</div>'
            f"</div>"
        )
    st.markdown(
        f'<div style="display:flex;gap:4px;">{cards_html}</div>',
        unsafe_allow_html=True,
    )
    st.caption("")

    # Donut + Bar side by side
    col_l, col_r = st.columns(2)
    with col_l:
        _render_donut(five_elements)
    with col_r:
        _render_bar(five_elements)


def _render_donut(five_elements: dict) -> None:
    """五行环图。"""
    total = sum(float(v) for v in five_elements.values()) or 1
    df = pd.DataFrame([
        {"五行": elem, "分数": float(score), "占比": round(float(score) / total * 100, 1)}
        for elem, score in sorted(five_elements.items(), key=lambda x: -float(x[1]))
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=50, outerRadius=100, stroke="#FFFFFF", strokeWidth=2)
        .encode(
            theta=alt.Theta("分数:Q").stack(True),
            color=alt.Color(
                "五行:N",
                scale=alt.Scale(
                    domain=list(ELEMENT_COLORS.keys()),
                    range=list(ELEMENT_COLORS.values()),
                ),
                legend=alt.Legend(orient="right", title=None, labelFontSize=12, symbolSize=160),
            ),
            tooltip=["五行", "分数", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True, key='inquiry_element_bar')


def _render_bar(five_elements: dict) -> None:
    """五行柱状图。"""
    df = pd.DataFrame([
        {"五行": elem, "权重": round(float(score), 2)}
        for elem, score in sorted(five_elements.items(), key=lambda x: -float(x[1]))
    ])
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=32)
        .encode(
            x=alt.X("权重:Q", title=None),
            y=alt.Y("五行:N", sort="-x", title=None),
            color=alt.Color(
                "五行:N",
                scale=alt.Scale(
                    domain=list(ELEMENT_COLORS.keys()),
                    range=list(ELEMENT_COLORS.values()),
                ),
                legend=None,
            ),
            tooltip=["五行", alt.Tooltip("权重:Q", format=".2f")],
        )
        .properties(height=260)
    )
    text = chart.mark_text(
        align="left", dx=5, fontSize=12, fontWeight="bold",
    ).encode(text=alt.Text("权重:Q", format=".2f"))
    st.altair_chart(chart + text, use_container_width=True, key='inquiry_element_bar_text')


def _render_strength_section(chart: dict) -> None:
    """日主强弱与喜忌。"""
    strength = chart.get("day_master_strength", {})
    if not strength:
        return

    st.markdown("### 🏆 日主强弱与喜忌")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
            f'<span><strong>强度</strong> {strength.get("strength", "")}</span>'
            f'<span><strong>净评分</strong> {strength.get("net_score", 0):+.1f}</span>'
            f'<span><strong>生扶</strong> {strength.get("support_score", 0):+.1f}</span>'
            f'<span><strong>克泄</strong> {strength.get("pressure_score", 0):+.1f}</span>'
            f"</div>"
            f'<div style="margin-top:6px;">'
            f'<span style="background:#4CAF5020;color:#2E7D32;padding:2px 8px;border-radius:4px;font-size:13px;">'
            f'喜用 {_element_list_text(strength.get("favorable_elements", []))}</span>&nbsp;'
            f'<span style="background:#FF572220;color:#BF360C;padding:2px 8px;border-radius:4px;font-size:13px;">'
            f'忌神 {_element_list_text(strength.get("unfavorable_elements", []))}</span>'
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col2:
        de_ling = strength.get("de_ling", {})
        de_di = strength.get("de_di", {})
        de_shi = strength.get("de_shi", {})
        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("得令", f"{de_ling.get('score', 0):+.1f}")
        s_col2.metric("得地", f"{de_di.get('score', 0):+.1f}")
        s_col3.metric("得势", f"{de_shi.get('support_score', 0):+.1f}/W{de_shi.get('pressure_score', 0):+.1f}")


def _render_luck_overview(chart: dict) -> None:
    """大运概览：当前大运 + 未来大运简表。"""
    from core.luck_engine import get_luck_cycles
    result = get_luck_cycles(chart.get("profile", {}), chart)
    if not result.get("available"):
        return

    dayun_list = result.get("dayun_list", [])
    current_year = date.today().year
    current_luck = None
    for item in dayun_list:
        if int(item.get("start_year", 0)) <= current_year <= int(item.get("end_year", 0)):
            current_luck = item
            break

    st.markdown("### 🔮 大运概览")

    if current_luck:
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown(
                f'<div style="background:#FF572215;border:1px solid #FF572240;'
                f'border-radius:12px;padding:14px;text-align:center;">'
                f'<div style="font-size:12px;color:#888;">当前大运</div>'
                f'<div style="font-size:26px;font-weight:800;margin:4px 0;">{current_luck.get("pillar", "")}</div>'
                f'<div style="font-size:13px;color:#B8860B;font-weight:600;">{current_luck.get("stage_level", "")}</div>'
                f'<div style="font-size:12px;color:#666;">'
                f'{current_luck.get("start_age", "")}-{current_luck.get("end_age", "")}岁'
                f'（{current_luck.get("start_year", "")}-{current_luck.get("end_year", "")}年）'
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.info(current_luck.get("stage_text", ""))
    else:
        st.caption("当前年份暂未匹配到大运阶段，可查看下方大运表。")

    with st.expander("📋 完整大运表"):
        rows = [
            {
                "大运": item.get("pillar", ""),
                "年龄": f'{item.get("start_age", "")}-{item.get("end_age", "")}',
                "年份": f'{item.get("start_year", "")}-{item.get("end_year", "")}',
                "天干": item.get("gan_element", ""),
                "地支": item.get("zhi_element", ""),
                "十神": item.get("ten_god", ""),
                "阶段": item.get("stage_level", ""),
            }
            for item in dayun_list
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Brief yearly list
    yearly_list = result.get("yearly_list", [])
    if yearly_list:
        with st.expander("📅 未来十年流年速览"):
            yr_rows = [
                {
                    "年份": item.get("year", ""),
                    "流年": item.get("pillar", ""),
                    "五行": f'{item.get("gan_element", "")}/{item.get("zhi_element", "")}',
                    "十神": item.get("ten_god", ""),
                    "喜忌": item.get("relation_to_favorable", ""),
                }
                for item in yearly_list
            ]
            st.dataframe(pd.DataFrame(yr_rows), use_container_width=True, hide_index=True)


def _render_ten_god_summary(chart: dict) -> None:
    """十神统计摘要。"""
    counts = chart.get("ten_god_counts", {})
    if not counts:
        return
    st.markdown("### 📊 十神分布")
    df = pd.DataFrame([
        {"十神": k, "数量": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])
    ])
    chart_viz = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=24)
        .encode(
            x=alt.X("数量:Q", title=None),
            y=alt.Y("十神:N", sort="-x", title=None),
            color=alt.Color("数量:Q", scale=alt.Scale(scheme="bluegreen"), legend=None),
            tooltip=["十神", "数量"],
        )
        .properties(height=200)
    )
    st.altair_chart(chart_viz, use_container_width=True, key='inquiry_ten_god_bar')


def _render_chart_tags(chart: dict) -> None:
    """命盘摘要标签。"""
    fp = _get_fingerprint(chart)
    if not fp:
        return
    tags = fp.get("chart_summary_tags", [])
    if not tags:
        return
    st.markdown("### 🏷️ 命盘标签")
    tag_html = ""
    for tag in tags:
        tag_html += (
            f'<span style="display:inline-block;background:#e8f5e9;color:#2E7D32;'
            f'border-radius:14px;padding:4px 12px;font-size:13px;margin:3px 4px;">{tag}</span>'
        )
    st.markdown(tag_html, unsafe_allow_html=True)
    st.caption("")


def _get_fingerprint(chart: dict) -> dict | None:
    try:
        from core.chart_fingerprint import build_chart_fingerprint
        return build_chart_fingerprint(chart)
    except Exception:
        return None


def _render_quick_nav() -> None:
    """快速导航到各详细页面。"""
    st.markdown("### 🔗 快速导航")
    nav_items = [
        ("📜 八字排盘", "八字排盘"),
        ("♻ 五行喜忌", "五行喜忌"),
        ("🔮 大运流年", "大运流年"),
        ("📅 年度运程", "年度运程"),
        ("📖 专项报告", "专项报告"),
    ]
    cols = st.columns(len(nav_items))
    for idx, (label, page_name) in enumerate(nav_items):
        with cols[idx]:
            if st.button(label, key=f"nav_{idx}", use_container_width=True):
                st.session_state["_nav_to"] = page_name


def render_inquiry_page() -> None:
    """渲染综合问盘页面。"""
    chart = st.session_state.get("current_chart")
    profile = st.session_state.get("current_profile", {})

    if not chart:
        st.info('请先在「新建命盘」页面生成命盘，或从命盘档案中加载一个命盘。')
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    # Check for navigation from quick nav
    nav_to = st.session_state.pop("_nav_to", None)

    st.title("🧿 综合问盘")
    st.caption("一屏查看命盘所有核心信息，点击快速导航跳转到详细页面。")

    # —— Profile + Four Pillars ——
    _render_profile_card(profile)
    _render_pillar_section(chart)

    # —— 命盘标签 ——
    _render_chart_tags(chart)

    # —— 五行可视化 ——
    _render_element_visual(chart)

    # —— 日主强弱 + 喜忌 ——
    _render_strength_section(chart)

    # —— 十神分布 ——
    _render_ten_god_summary(chart)

    # —— 大运概览 ——
    _render_luck_overview(chart)

    # —— 快速导航 ——
    st.divider()
    _render_quick_nav()

    # Handle navigation
    if nav_to:
        st.info(f"可切换到「{nav_to}」页面查看详细信息。")
