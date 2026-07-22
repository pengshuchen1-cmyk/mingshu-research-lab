"""六十甲子知识层页面：解释干支、五行、纳音与立春边界，不作为断事核心。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.sixty_jiazi import get_jiazi_by_pillar, get_jiazi_by_year, load_sixty_jiazi


def _render_entry_card(entry: dict) -> None:
    sample_years = "、".join(str(year) for year in entry.get("sample_years", [])[-4:])
    st.markdown(
        f"""
        <div class="ms-report-panel">
            <div class="ms-section-kicker">六十甲子速查</div>
            <h2 style="border-bottom:none;margin:4px 0 8px 0 !important;">{entry["pillar"]} · {entry["nayin"]}</h2>
            <div class="ms-mini-metric-grid">
                <div class="ms-mini-metric"><span>天干</span><strong>{entry["gan"]}｜{entry["gan_element"]}</strong></div>
                <div class="ms-mini-metric"><span>地支</span><strong>{entry["zhi"]}｜{entry["zhi_element"]}</strong></div>
                <div class="ms-mini-metric"><span>纳音</span><strong>{entry["nayin"]}</strong></div>
                <div class="ms-mini-metric"><span>年份示例</span><strong>{sample_years}</strong></div>
            </div>
            <p>{entry["plain_explanation"]}</p>
            <p><strong>现实映射：</strong>{entry.get("reality_mapping", "可作为传统文化象意辅助理解。")}</p>
            <p><strong>使用建议：</strong>{entry.get("user_advice", "建议结合完整命盘综合理解。")}</p>
            <p><strong>立春边界：</strong>{entry["lichun_boundary_note"]}</p>
            <p class="ms-muted-text">说明：纳音适合作为传统文化象意和用户理解入口，不直接作为年度、流月断事的核心依据。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sixty_jiazi_page() -> None:
    """渲染六十甲子知识库页面。"""
    st.markdown(
        """
        <section class="v106c-page-hero">
            <div class="v106c-page-kicker">知识库 · 六十甲子与纳音</div>
            <h1>六十甲子知识库</h1>
            <p>把视频里的六十甲子表吸收为知识解释层：帮助用户理解干支、五行、纳音和立春边界，但不作为断事核心。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    current_year = st.number_input("选择年份", min_value=1900, max_value=2100, value=2026, step=1)
    entry = get_jiazi_by_year(int(current_year))
    _render_entry_card(entry)

    st.markdown("### 按干支查询")
    pillars = [row["pillar"] for row in load_sixty_jiazi()]
    selected_pillar = st.selectbox("选择干支", pillars, index=pillars.index(entry["pillar"]))
    selected_entry = get_jiazi_by_pillar(selected_pillar)
    if selected_entry:
        _render_entry_card(selected_entry)

    st.markdown("### 六十甲子全表")
    rows = load_sixty_jiazi()
    df = pd.DataFrame(
        [
            {
                "序号": row["index"],
                "干支": row["pillar"],
                "天干五行": row["gan_element"],
                "地支主气五行": row["zhi_element"],
                "纳音": row["nayin"],
                "关键词": "、".join(row.get("symbolic_keywords", [])[:4]),
                "年份示例": "、".join(str(year) for year in row["sample_years"][-3:]),
            }
            for row in rows
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("为什么要提醒立春边界？", expanded=False):
        st.write(
            "八字年柱通常按立春切换。比如某些年份的2月初，虽然公历已经进入新年，"
            "但如果还没有到立春，八字年柱仍可能按上一年计算。这个页面的年份查询适合做速查，"
            "真正排盘仍以系统的节气排盘逻辑为准。"
        )
