"""五行喜忌页面 —— 五行十神 + 日主喜忌（合并）。"""

from __future__ import annotations

import pandas as pd
import altair as alt
import streamlit as st

from core.five_elements import element_summary


from ui.charts import render_element_wheel
from ui.styles import ELEMENT_COLORS, element_tag

from ui.styles import ELEMENT_EMOJIS

ELEMENT_METADATA = {
    "木": {"tian_gan": "甲乙", "direction": "东", "season": "春"},
    "火": {"tian_gan": "丙丁", "direction": "南", "season": "夏"},
    "土": {"tian_gan": "戊己", "direction": "中", "season": "季末"},
    "金": {"tian_gan": "庚辛", "direction": "西", "season": "秋"},
    "水": {"tian_gan": "壬癸", "direction": "北", "season": "冬"},
}


def _sorted_elements(five_elements: dict) -> list:
    """按分数降序排列五行。"""
    return sorted(five_elements.items(), key=lambda x: -float(x[1]))


def _element_list_text(elements: list[str]) -> str:
    """格式化五行列表。"""
    return "、".join(elements) if elements else "需结合大运流年进一步判断"


def _render_element_bar_chart(five_elements: dict) -> None:
    """渲染五行柱状图（Altair）。"""
    df = pd.DataFrame([
        {"五行": elem, "权重": round(float(score), 2)}
        for elem, score in _sorted_elements(five_elements)
    ])
    base = alt.Chart(df).properties(height=240)
    chart = (
        base
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=36)
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
    )
    text = base.mark_text(
        align="left", dx=6, fontSize=13, fontWeight="bold", color="#E8E2D2",
    ).encode(
        x=alt.X("权重:Q", title=None),
        y=alt.Y("五行:N", sort="-x", title=None),
        text=alt.Text("权重:Q", format=".2f"),
    )
    final_chart = (
        (chart + text)
        .properties(background='transparent')
        .configure_axis(
            labelColor="#C9D2D0",
            gridColor="rgba(216, 185, 106, 0.10)",
            domainColor="rgba(216, 185, 106, 0.18)",
            tickColor="rgba(216, 185, 106, 0.18)",
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(final_chart, use_container_width=True)


def _render_element_donut_chart(five_elements: dict) -> None:
    """渲染五行占比环图（Altair）。"""
    total = sum(float(v) for v in five_elements.values()) or 1
    df = pd.DataFrame([
        {"五行": elem, "分数": float(score), "占比": round(float(score) / total * 100, 1)}
        for elem, score in _sorted_elements(five_elements)
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=55, outerRadius=110, stroke="#0D161B", strokeWidth=2)
        .encode(
            theta=alt.Theta("分数:Q").stack(True),
            color=alt.Color(
                "五行:N",
                scale=alt.Scale(
                    domain=list(ELEMENT_COLORS.keys()),
                    range=list(ELEMENT_COLORS.values()),
                ),
                legend=alt.Legend(
                    orient="right", title=None, labelFontSize=13, symbolSize=200,
                ),
            ),
            tooltip=["五行", "分数", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=300, background='transparent')
        .configure_legend(labelColor="#C9D2D0", titleColor="#E8E2D2")
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def _render_element_cards(summary: dict) -> None:
    """五行占比彩色卡片。"""
    cols = st.columns(5)
    for idx, (element, info) in enumerate(summary.items()):
        color = ELEMENT_COLORS.get(element, "#888")
        emoji = ELEMENT_EMOJIS.get(element, "")
        meta = ELEMENT_METADATA.get(element, {})
        ratio = info["ratio"]
        strength = info["strength"]
        tian_gan = meta.get("tian_gan", "")
        direction = meta.get("direction", "")
        season = meta.get("season", "")
        with cols[idx]:
            card_html = (
                f'<div class="ms-element-card" style="border-color:{color}55;">'
                f'<div style="font-size:28px;line-height:1.2;">{emoji}</div>'
                f'<div class="ms-element-label" style="color:{color};">{element}</div>'
                f'<div class="ms-element-ratio" style="color:{color};">{ratio}%</div>'
                f'<div class="ms-element-meta">{strength}</div>'
                f'<div class="ms-element-meta">{tian_gan} · {direction} · {season}</div>'
                f"</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)


def _render_strength_bars(five_elements: dict) -> None:
    """五行强弱水平进度条。"""
    scores = {k: float(v) for k, v in five_elements.items()}
    max_score = max(scores.values()) if scores else 1
    st.markdown("#### 五行强弱水平")
    cols = st.columns(5)
    for idx, (element, score) in enumerate(scores.items()):
        color = ELEMENT_COLORS.get(element, "#888")
        emoji = ELEMENT_EMOJIS.get(element, "")
        norm = round(score / max_score * 100, 1) if max_score else 0
        label = "偏旺" if norm >= 60 else "中等" if norm >= 30 else "偏弱"
        with cols[idx]:
            bar_html = (
                f'<div style="text-align:center;padding:6px 2px;">'
                f'<div style="font-size:15px;margin-bottom:4px;">{emoji} <strong>{element}</strong></div>'
                f'<div style="width:100%;height:10px;background:var(--ms-surface-2);border:1px solid var(--ms-border);border-radius:5px;overflow:hidden;">'
                f'<div style="width:{min(100, norm)}%;height:100%;background:{color};border-radius:5px;"></div>'
                f"</div>"
                f'<div style="font-size:12px;color:var(--ms-muted);margin-top:3px;">{label} · {norm:.0f}%</div>'
                f"</div>"
            )
            st.markdown(bar_html, unsafe_allow_html=True)


def _render_ten_god_chart(counts: dict) -> None:
    """十神分布水平条（Altair）。"""
    df = pd.DataFrame([
        {"十神": name, "数量": value}
        for name, value in sorted(counts.items(), key=lambda x: -x[1])
    ])
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=22)
        .encode(
            x=alt.X("数量:Q", title=None),
            y=alt.Y("十神:N", sort="-x", title=None),
            color=alt.Color("数量:Q", scale=alt.Scale(scheme="bluegreen"), legend=None),
            tooltip=["十神", "数量"],
        )
        .properties(height=240, background='transparent')
        .configure_axis(
            labelColor="#C9D2D0",
            gridColor="rgba(216, 185, 106, 0.10)",
            domainColor="rgba(216, 185, 106, 0.18)",
            tickColor="rgba(216, 185, 106, 0.18)",
        )
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_five_element_page() -> None:
    """渲染五行十神页面。"""
    chart = st.session_state.get("current_chart")
    report = st.session_state.get("current_report", {})
    if not chart:
        st.info('请先在「新建命盘」页面生成命盘。')
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    strength = chart.get("day_master_strength", {})
    five_elements = chart.get("five_elements", {})
    if not five_elements:
        st.info('五行数据暂不可用。')
        return

    summary = element_summary(five_elements)

    # —— 顶部：五行占比彩色卡片 ——
    st.markdown("## 五行喜忌")
    st.markdown("### 🌟 五行喜忌")
    _render_element_cards(summary)

    # —— 中间：动画轮盘 + 柱状图 ——
    col_left, col_right = st.columns([4, 3])
    with col_left:
        st.markdown(
            '<div class="ms-chart-title" style="text-align:center;">五行能量轮盘</div>',
            unsafe_allow_html=True,
        )
        render_element_wheel(five_elements, key="five_el_wheel", width=420, animated=False)
    with col_right:
        st.markdown(
            '<div class="ms-chart-title">五行细分数值</div>',
            unsafe_allow_html=True,
        )
        _render_element_bar_chart(five_elements)

    # —— 五行强弱水平条 ——
    _render_strength_bars(five_elements)

    # —— 日主强弱 ——
    st.markdown("### 🏆 日主强弱")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("日主强弱", strength.get("strength", "暂无法判断"))
    col2.metric("净评分", strength.get("net_score", 0.0))
    col3.metric("生扶力量", strength.get("support_score", 0.0))
    col4.metric("克泄耗力量", strength.get("pressure_score", 0.0))
    st.markdown(
        f"喜用五行：**{_element_list_text(strength.get('favorable_elements', []))}**　|　"
        f"忌神五行：**{_element_list_text(strength.get('unfavorable_elements', []))}**"
    )
    st.info(strength.get("explanation", "日主强弱初判暂不可用。"))

    st.markdown("#### 得令 · 得地 · 得势")
    de_ling = strength.get("de_ling", {})
    de_di = strength.get("de_di", {})
    de_shi = strength.get("de_shi", {})
    cd1, cd2, cd3 = st.columns(3)
    cd1.metric("得令", f"{de_ling.get('score', 0):+.1f}", help=de_ling.get("text", ""))
    cd2.metric("得地", f"{de_di.get('score', 0):+.1f}", help=de_di.get("text", ""))
    cd3.metric(
        "得势",
        f"生扶{de_shi.get('support_score', 0):+.1f} / 克泄{de_shi.get('pressure_score', 0):+.1f}",
        help=de_shi.get("text", ""),
    )

    # —— 十神分布 ——
    counts = chart.get("ten_god_counts", {})
    if counts:
        st.markdown("### 📊 十神分布")
        col_t1, col_t2 = st.columns([3, 2])
        with col_t1:
            _render_ten_god_chart(counts)
        with col_t2:
            rows = [{"十神": k, "数量": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # —— 五行结构深度报告（v1.2-F）——
    st.markdown("### 📖 五行深度解释")
    try:
        from report.five_element_deep_report import generate_five_element_deep_report
        luck_data = st.session_state.get("current_luck_data")
        deep_report = generate_five_element_deep_report(chart, luck_data)
        
        # 五行结构总览
        st.markdown(
            f'<div class="ms-readable-panel" style="margin-bottom:12px;border-left:4px solid var(--ms-accent);">'
            f'<b>五行结构总览：</b>{deep_report.get("element_overview", "")}'
            f'<br><br><b>强弱平衡：</b>{deep_report.get("element_balance_summary", "")}'
            f'<br><br><b>喜用五行：</b>{"、".join(deep_report.get("favorable_elements", [])) or "暂无"}'
            f'<br><b>忌神五行：</b>{"、".join(deep_report.get("unfavorable_elements", [])) or "暂无"}'
            f'</div>', unsafe_allow_html=True
        )
        
        # 五行详情卡片
        st.markdown("#### 五行详情")
        for element in ["木", "火", "土", "金", "水"]:
            detail = deep_report.get("element_details", {}).get(element, {})
            if not detail:
                continue
            level = detail.get("level", "")
            is_fav = detail.get("is_favorable", False)
            is_unfav = detail.get("is_unfavorable", False)
            status = f"[{level}]"
            if is_fav: status += " ✓喜用"
            if is_unfav: status += " ⚠忌神"
            with st.expander(f"{element} {status}", expanded=(level == "偏旺")):
                st.markdown(f"**基础含义：**{detail.get('basic_meaning', '')}")
                st.markdown(f"**命局情况：**{detail.get('in_this_chart', '')}")
                st.markdown("---")
                st.markdown(f"**事业意义：**{detail.get('career_meaning', '')}")
                st.markdown(f"**财富意义：**{detail.get('wealth_meaning', '')}")
                st.markdown(f"**感情意义：**{detail.get('relationship_meaning', '')}")
                st.markdown(f"**健康倾向：**{detail.get('health_tendency', '')}")
                st.markdown("---")
                st.markdown(f"**过旺表现：**{detail.get('when_too_strong', '')}")
                st.markdown(f"**过弱表现：**{detail.get('when_too_weak', '')}")
                st.markdown("---")
                st.markdown(f"**喜用建议：**{detail.get('if_favorable', '')}")
                st.markdown(f"**忌神建议：**{detail.get('if_unfavorable', '')}")
                advice_items = detail.get("real_life_advice", [])
                if advice_items:
                    st.markdown("**行为建议：**")
                    for a in advice_items:
                        st.markdown(f"- {a}")
        
        # 事业/财富/感情/健康影响
        st.markdown("#### 五行对主要领域的影响")
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            ci = deep_report.get('career_implications', '')[:200]
            st.info("**事业影响**\n\n" + ci)
            wi = deep_report.get('wealth_implications', '')[:200]
            st.info("**财运影响**\n\n" + wi)
        with w_col2:
            ri = deep_report.get('relationship_implications', '')[:200]
            st.info("**感情影响**\n\n" + ri)
            hi = deep_report.get('health_implications', '')[:200]
            st.info("**健康影响**\n\n" + hi)
        
        # 调整建议
        st.markdown("#### 🧭 调整建议")
        for a in deep_report.get("adjustment_advice", []):
            st.markdown(f"- {a}")
        
        # 参考来源
        sources = deep_report.get("source_titles", [])
        if sources:
            st.markdown(f"**参考来源：**{'、'.join(sources)}")
            
    except Exception as exc:
        st.write(report.get("five_element_text", "五行深度报告暂未生成。"))

    # —— 喜用五行细化（含分析引擎输出） ——
    st.markdown("### 🧭 喜用五行细化")
    try:
        from core.useful_god_engine import analyze_useful_god
        useful = analyze_useful_god(chart)
        summary = useful.get("summary", "")
        if summary:
            st.markdown(f'<div class="ms-readable-panel" style="margin-bottom:12px;border-left:4px solid var(--ms-accent);">{summary}</div>',
                        unsafe_allow_html=True)
        for item in useful.get("details", []):
            with st.expander(f"喜{item.get('element', '')}：{'、'.join(item.get('keywords', []))}"):
                st.write(f"事业建议：{item.get('career_advice', '')}")
                st.write(f"生活建议：{item.get('life_advice', '')}")
                st.write(f"风险提醒：{item.get('risk_advice', '')}")
    except Exception:
        st.write(report.get("useful_god_text", ""))
        for item in report.get("useful_god_details", []):
            with st.expander(f"喜{item.get('element', '')}：{'、'.join(item.get('keywords', []))}"):
                st.write(f"事业建议：{item.get('career_advice', '')}")
                st.write(f"生活建议：{item.get('life_advice', '')}")
                st.write(f"风险提醒：{item.get('risk_advice', '')}")

    # —— 十神解说 ——
    st.markdown("### 📚 十神解释")
    st.write(report.get("ten_god_text", ""))
