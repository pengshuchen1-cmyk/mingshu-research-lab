"""八字排盘页面 —— 对标测测 app 的高密度卡片布局。"""

from __future__ import annotations

from ui.styles import (
    ELEMENT_COLORS, ELEMENT_EMOJIS, card_style, element_tag,
    info_card_html, metric_card_html,
)
from core.ten_god_explanations import get_ten_god_explanation, get_ten_god_html
from core.chart_type import classify_chart, get_combination_html
from core.di_shi_explanations import get_di_shi_explanation, get_di_shi_color


def _render_element_donut(five_elements: dict, col) -> None:
    """五行环图（Altair donut）。"""
    import altair as alt
    import pandas as pd
    total = sum(float(v) for v in five_elements.values()) or 1
    df = pd.DataFrame([
        {"五行": elem, "分数": float(score), "占比": round(float(score) / total * 100, 1)}
        for elem, score in sorted(five_elements.items(), key=lambda x: -float(x[1]))
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=45, outerRadius=90, stroke="#FAF7F4", strokeWidth=2)
        .encode(
            theta=alt.Theta("分数:Q").stack(True),
            color=alt.Color(
                "五行:N",
                scale=alt.Scale(
                    domain=list(ELEMENT_COLORS.keys()),
                    range=list(ELEMENT_COLORS.values()),
                ),
                legend=alt.Legend(orient="right", title=None, labelFontSize=11, symbolSize=120),
            ),
            tooltip=["五行", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=240)
    )
    col.altair_chart(chart, width='stretch')


def _render_ten_god_donut(counts: dict, col) -> None:
    """十神环图（Altair donut）。"""
    import altair as alt
    import pandas as pd
    total = sum(counts.values()) or 1
    df = pd.DataFrame([
        {"十神": k, "数量": v, "占比": round(v / total * 100, 1)}
        for k, v in sorted(counts.items(), key=lambda x: -x[1])
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=40, outerRadius=85, stroke="#FAF7F4", strokeWidth=2)
        .encode(
            theta=alt.Theta("数量:Q").stack(True),
            color=alt.Color(
                "十神:N",
                scale=alt.Scale(scheme="goldorange"),
                legend=alt.Legend(orient="right", title=None, labelFontSize=10, symbolSize=100),
            ),
            tooltip=["十神", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=220)
    )
    col.altair_chart(chart, width='stretch')


def _render_current_luck_snapshot(chart: dict, col) -> None:
    """在当前命盘页面显示大运/流年快照。"""
    import streamlit as st
    from datetime import date
    from core.yearly_engine import get_year_pillar
    current_year = date.today().year
    year_pillar = get_year_pillar(current_year)
    try:
        from core.luck_engine import get_luck_cycles
        luck_data = get_luck_cycles(chart.get("profile", {}), chart)
        dayun_list = luck_data.get("dayun_list", [])
        current_luck = None
        for d in dayun_list:
            if int(d.get("start_year", 0)) <= current_year <= int(d.get("end_year", 0)):
                current_luck = d
                break
        if current_luck:
            stage = current_luck.get("stage_level", "")
            col.markdown(
                f'<div style="{card_style()}text-align:center;padding:12px;">'
                f'<div style="font-size:11px;color:#8C7A64;">当前大运</div>'
                f'<div style="font-size:18px;font-weight:700;color:#3D2B1A;'
                f'font-family:\'Noto Serif SC\',serif;">{current_luck.get("pillar", "")}</div>'
                f'<div style="font-size:12px;color:#5C4A32;">'
                f'{current_luck.get("start_age","")}-{current_luck.get("end_age","")}岁'
                f'（{current_luck.get("start_year","")}-{current_luck.get("end_year","")}年）</div>'
                f'<div style="font-size:11px;color:#B8860B;margin-top:2px;">{stage}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass


def _render_element_donut(five_elements: dict, col) -> None:
    """五行环图（Altair donut）。"""
    import altair as alt
    import pandas as pd
    total = sum(float(v) for v in five_elements.values()) or 1
    df = pd.DataFrame([
        {"五行": elem, "分数": float(score), "占比": round(float(score) / total * 100, 1)}
        for elem, score in sorted(five_elements.items(), key=lambda x: -float(x[1]))
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=45, outerRadius=90, stroke="#FAF7F4", strokeWidth=2)
        .encode(
            theta=alt.Theta("分数:Q").stack(True),
            color=alt.Color(
                "五行:N",
                scale=alt.Scale(
                    domain=list(ELEMENT_COLORS.keys()),
                    range=list(ELEMENT_COLORS.values()),
                ),
                legend=alt.Legend(orient="right", title=None, labelFontSize=11, symbolSize=120),
            ),
            tooltip=["五行", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=240)
    )
    col.altair_chart(chart, width='stretch')


def _render_ten_god_donut(counts: dict, col) -> None:
    """十神环图（Altair donut）。"""
    import altair as alt
    import pandas as pd
    total = sum(counts.values()) or 1
    df = pd.DataFrame([
        {"十神": k, "数量": v, "占比": round(v / total * 100, 1)}
        for k, v in sorted(counts.items(), key=lambda x: -x[1])
    ])
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=40, outerRadius=85, stroke="#FAF7F4", strokeWidth=2)
        .encode(
            theta=alt.Theta("数量:Q").stack(True),
            color=alt.Color(
                "十神:N",
                scale=alt.Scale(scheme="goldorange"),
                legend=alt.Legend(orient="right", title=None, labelFontSize=10, symbolSize=100),
            ),
            tooltip=["十神", alt.Tooltip("占比:Q", format=".1f")],
        )
        .properties(height=220)
    )
    col.altair_chart(chart, width='stretch')


def _render_current_luck_snapshot(chart: dict, col) -> None:
    """在当前命盘页面显示大运快照。"""
    from datetime import date
    from core.yearly_engine import get_year_pillar
    current_year = date.today().year
    try:
        from core.luck_engine import get_luck_cycles
        luck_data = get_luck_cycles(chart.get("profile", {}), chart)
        for d in luck_data.get("dayun_list", []):
            if int(d.get("start_year", 0)) <= current_year <= int(d.get("end_year", 0)):
                stage = d.get("stage_level", "")
                col.markdown(
                    f'<div style="{card_style()}text-align:center;padding:12px;">'
                    f'<div style="font-size:11px;color:#8C7A64;">当前大运</div>'
                    f'<div style="font-size:18px;font-weight:700;color:#3D2B1A;'
                    f'font-family:\'Noto Serif SC\',serif;">{d.get("pillar", "")}</div>'
                    f'<div style="font-size:12px;color:#5C4A32;">'
                    f'{d.get("start_age","")}-{d.get("end_age","")}岁'
                    f'（{d.get("start_year","")}-{d.get("end_year","")}年）</div>'
                    f'<div style="font-size:11px;color:#B8860B;margin-top:2px;">{stage}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                break
    except Exception:
        pass


def _hidden_text(items: list[dict]) -> str:
    return "、".join(f"{item.get('gan', '')}({item.get('ten_god', '')})" for item in items)


def render_pillar_card(col, pillar: dict, ten_god_gan: str, hidden_stems: list,
                       is_day: bool = False) -> None:
    """单柱卡片渲染。"""
    border = "2px solid #B8860B" if is_day else "1px solid #EDE6DC"
    na_yin = pillar.get("na_yin", "")
    xun_kong = pillar.get("xun_kong", "")
    di_shi = pillar.get("di_shi", "")
    di_shi_color = get_di_shi_color(di_shi)

    hidden_html = ""
    if hidden_stems:
        items = []
        for h in hidden_stems:
            items.append(f'{h["gan"]}({h["ten_god"]})')
        hidden_html = (
            f'<div style="font-size:11px;color:#5C4A32;margin-top:4px;line-height:1.5;">'
            f'藏：{"、".join(items)}</div>'
        )

    extra_html = ""
    if na_yin:
        extra_html += f'<span style="font-size:11px;color:#B8860B;">{na_yin}</span>'
    if xun_kong:
        extra_html += f'<span style="font-size:10px;color:#8C7A64;margin-left:6px;">空{xun_kong}</span>'
    if di_shi:
        extra_html += (
            f'<span style="font-size:10px;color:{di_shi_color};margin-left:6px;">'
            f'{di_shi}</span>'
        )

    day_label = '<div style="font-size:10px;color:#B8860B;margin-top:2px;">★ 日主</div>' if is_day else ""

    html = (
        f'<div style="background:#FAF7F4;border-radius:10px;padding:14px 8px;'
        f'text-align:center;{border}box-shadow:0 1px 3px rgba(0,0,0,0.06),'
        f'0 1px 2px rgba(0,0,0,0.04);">'
        f'<div style="font-size:12px;color:#8C7A64;margin-bottom:2px;">{pillar["name"]}</div>'
        f'<div style="font-size:24px;font-weight:700;color:#3D2B1A;'
        f'font-family:\'Noto Serif SC\',serif;letter-spacing:4px;">'
        f'{pillar["pillar"]}</div>'
        f'<div style="margin:2px 0 4px;">{extra_html}</div>'
        f'<div style="font-size:12px;color:#B8860B;font-weight:500;">{ten_god_gan}</div>'
        f'{hidden_html}'
        f'{day_label}'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def render_bazi_page() -> None:
    """渲染八字排盘页面。"""
    import streamlit as st
    import pandas as pd

    chart = st.session_state.get("current_chart")
    report = st.session_state.get("current_report", {})
    if not chart:
        st.info("请先在「新建命盘」页面生成命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    profile = chart.get("profile", {})

    # ============== 1. 基础信息 ==============
    rows = [
        ("姓名", profile.get("name", "") or "未命名"),
        ("性别", profile.get("gender", "")),
        ("公历", f'{profile.get("birth_date", "")} {profile.get("birth_hour", 0):02d}:{profile.get("birth_minute", 0):02d}'),
    ]
    lunar = chart.get("lunar_text", "")
    if lunar:
        rows.append(("农历", lunar))
    st.markdown(info_card_html("基础信息", rows), unsafe_allow_html=True)

    # ============== 2. 四柱八字卡片 ==============
    st.markdown("## 八字排盘")
    st.markdown("### 四柱八字")
    cols = st.columns(4)
    for i, key in enumerate(["year", "month", "day", "hour"]):
        pillar = chart["pillars"][key]
        ten_god_gan = chart["ten_gods"][key]["gan"]
        stems = chart.get("hidden_stems", {}).get(key, [])
        render_pillar_card(cols[i], pillar, ten_god_gan, stems, is_day=(key == "day"))

    # ============== 3. 日主总览 ==============
    strength = chart.get("day_master_strength", {})
    day_master = chart.get("day_master", "")
    day_element = ELEMENT_COLORS.get(
        {"甲": "木", "乙": "木", "丙": "火", "丁": "火",
         "戊": "土", "己": "土", "庚": "金", "辛": "金",
         "壬": "水", "癸": "水"}.get(day_master, ""), "#3D2B1A"
    )
    day_emoji = {"甲": "🌳", "乙": "🌿", "丙": "🔥", "丁": "✨",
                 "戊": "⛰️", "己": "🌱", "庚": "⚔️", "辛": "💎",
                 "壬": "🌊", "癸": "💧"}.get(day_master, "✦")

    st.markdown("### 日主总览")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div style="{card_style()}text-align:center;">'
            f'<div style="font-size:32px;margin-bottom:4px;">{day_emoji}</div>'
            f'<div style="font-size:14px;font-weight:600;color:#3D2B1A;">{day_master}</div>'
            f'<div style="font-size:22px;font-weight:700;color:{day_element};">'
            f'{"甲乙丙丁戊己庚辛壬癸".index(day_master) // 2 if day_master in "甲乙丙丁戊己庚辛壬癸" else ""}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            metric_card_html("强弱", strength.get("strength", "—"),
                             f"净评分 {strength.get('net_score', 0):+.1f}"),
            unsafe_allow_html=True,
        )
    with c3:
        de_ling = strength.get("de_ling", {})
        st.markdown(
            metric_card_html("得令", f"{de_ling.get('score', 0):+.1f}"),
            unsafe_allow_html=True,
        )
    with c4:
        de_di = strength.get("de_di", {})
        st.markdown(
            metric_card_html("得地", f"{de_di.get('score', 0):+.1f}"),
            unsafe_allow_html=True,
        )

    # 喜忌标签
    favorable = strength.get("favorable_elements", [])
    unfavorable = strength.get("unfavorable_elements", [])
    if favorable or unfavorable:
        fav_html = "".join(f'<span style="{element_tag(e)}">{e}</span>' for e in favorable)
        unfav_html = "".join(f'<span style="{element_tag(e)}">{e}</span>' for e in unfavorable)
        st.markdown(
            f'<div style="margin:8px 0;font-size:13px;line-height:2;">'
            f'<span style="color:#5C4A32;">喜用：</span>{fav_html}'
            f'<span style="color:#5C4A32;margin-left:20px;">忌神：</span>{unfav_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
    # 得势
    de_shi = strength.get("de_shi", {})
    st.caption(
        f"生扶 {de_shi.get('support_score', 0):+.1f} / "
        f"克泄耗 {de_shi.get('pressure_score', 0):+.1f}"
    )

    # ============== 4. 命盘类型 ==============
    st.markdown("### 命盘类型")
    try:
        ct = classify_chart(chart)
        tags = []
        if ct.get("basic_pattern"):
            tags.append(ct["basic_pattern"])
        if ct.get("element_pattern"):
            tags.append(ct["element_pattern"])
        if ct.get("ten_god_pattern"):
            tags.append(f'{ct["ten_god_pattern"]}格')
        for sc in ct.get("special_combinations", []):
            tags.append(sc)

        tag_html = "".join(
            f'<span style="display:inline-block;background:#EDE6DC;color:#3D2B1A;'
            f'border-radius:12px;padding:3px 12px;font-size:13px;margin:3px 4px;'
            f'font-weight:500;">{t}</span>'
            for t in tags
        )
        st.markdown(
            f'<div style="{card_style()}margin:8px 0;">{tag_html}</div>',
            unsafe_allow_html=True,
        )
        summary = ct.get("summary", "")
        if summary:
            st.markdown(
                f'<div style="background:#FAF7F4;border-radius:8px;padding:10px 14px;'
                f'border-left:3px solid #B8860B;font-size:13px;color:#3D2B1A;'
                f'line-height:1.6;">{summary}</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    # ============== 5. 命宫/身宫 + 大运/流年快照 ==============
    ming_gong = chart.get("ming_gong", "")
    shen_gong = chart.get("shen_gong", "")
    tai_yuan = chart.get("tai_yuan", "")
    tai_xi = chart.get("tai_xi", "")
    st.markdown("### 命宫 · 大运 · 流年")
    c_a, c_b, c_c, c_d = st.columns(4)
    with c_a:
        st.markdown(metric_card_html("命宫", ming_gong) if ming_gong else metric_card_html("命宫", "—"), unsafe_allow_html=True)
    with c_b:
        st.markdown(metric_card_html("身宫", shen_gong) if shen_gong else metric_card_html("身宫", "—"), unsafe_allow_html=True)
    with c_c:
        _render_current_luck_snapshot(chart, c_c)
    with c_d:
        # 流年快照
        from datetime import date
        from core.yearly_engine import get_year_pillar
        cy = date.today().year
        yp = get_year_pillar(cy)
        st.markdown(
            f'<div style="{card_style()}text-align:center;padding:12px;">'
            f'<div style="font-size:11px;color:#8C7A64;">当前流年</div>'
            f'<div style="font-size:18px;font-weight:700;color:#3D2B1A;'
            f'font-family:\'Noto Serif SC\',serif;">{yp}</div>'
            f'<div style="font-size:12px;color:#5C4A32;">{cy}年</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    # 胎元/胎息 以一行caption展示
    if tai_yuan or tai_xi:
        st.caption(f"胎元：{tai_yuan or '—'}　胎息：{tai_xi or '—'}")

    # ============== 6. 五行能量（环图 + 进度条） ==============
    five_elements = chart.get("five_elements", {})
    if five_elements:
        st.markdown("### 五行能量")
        col_donut, col_bars = st.columns([3, 2])
        with col_donut:
            _render_element_donut(five_elements, col_donut)
        with col_bars:
            total = sum(float(v) for v in five_elements.values()) or 1
            sorted_els = sorted(five_elements.items(), key=lambda x: -float(x[1]))
            bar_html_parts = []
            for elem, score in sorted_els:
                pct = round(float(score) / total * 100, 1)
                color = ELEMENT_COLORS.get(elem, "#8C7A64")
                emoji = ELEMENT_EMOJIS.get(elem, "")
                bar_html_parts.append(
                    f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
                    f'<span style="width:28px;font-size:13px;text-align:right;">{emoji}</span>'
                    f'<span style="width:16px;font-size:12px;color:#5C4A32;">{elem}</span>'
                    f'<div style="flex:1;height:10px;background:#EDE6DC;border-radius:5px;overflow:hidden;">'
                    f'<div style="width:{pct}%;height:100%;background:{color};border-radius:5px;"></div></div>'
                    f'<span style="width:36px;font-size:11px;color:#5C4A32;text-align:right;">{pct}%</span>'
                    f'</div>'
                )
            st.markdown(
                f'<div style="{card_style()}padding:12px 16px;">'
                f'{"".join(bar_html_parts)}</div>',
                unsafe_allow_html=True,
            )

    # ============== 7. 十神分布（环图 + 柱状图 + 词条） ==============
    counts = chart.get("ten_god_counts", {})
    if counts:
        st.markdown("### 十神分布")
        tg_df = pd.DataFrame([
            {"十神": k, "数量": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ])
        # Row: donut chart + bar chart
        col_donut, col_bar = st.columns([3, 3])
        with col_donut:
            _render_ten_god_donut(counts, col_donut)
        with col_bar:
            import altair as alt
            chart_viz = (
                alt.Chart(tg_df)
                .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, size=22)
                .encode(
                    x=alt.X("数量:Q", title=None),
                    y=alt.Y("十神:N", sort="-x", title=None),
                    color=alt.Color("数量:Q", scale=alt.Scale(scheme="goldorange"), legend=None),
                    tooltip=["十神", "数量"],
                )
                .properties(height=220)
            )
            st.altair_chart(chart_viz, width='stretch')
        
        # 词条卡片
        st.markdown("#### 十神详解")
        cols_kw = st.columns(2)
        top_tgs = tg_df["十神"].tolist()[:10]
        half = (len(top_tgs) + 1) // 2
        for col_idx, batch in enumerate([top_tgs[:half], top_tgs[half:]]):
            with cols_kw[col_idx]:
                for tg in batch:
                    html = get_ten_god_html(tg)
                    if html:
                        st.markdown(
                            f'<div style="background:#FAF7F4;border-radius:8px;padding:10px 12px;'
                            f'margin-bottom:6px;box-shadow:0 1px 2px rgba(0,0,0,0.03);">'
                            f'{html}</div>',
                            unsafe_allow_html=True,
                        )

    # ============== 8. 专项解读 ==============
    st.markdown("### 专项解读")
    sections = [
        ("性格倾向", "personality_text"),
        ("事业倾向", "career_text"),
        ("财富倾向", "wealth_text"),
        ("关系倾向", "love_text"),
        ("风险提醒", "risk_text"),
    ]
    for label, key in sections:
        text = report.get(key, "")
        if text:
            with st.expander(label):
                st.markdown(text)

    # 藏干完整详情
    with st.expander("📂 完整藏干详情"):
        for key in ["year", "month", "day", "hour"]:
            stems = chart.get("hidden_stems", {}).get(key, [])
            if stems:
                st.markdown(
                    f'<span style="color:#5C4A32;font-weight:500;">'
                    f'{chart["pillars"][key]["name"]}：</span>{_hidden_text(stems)}',
                    unsafe_allow_html=True,
                )
