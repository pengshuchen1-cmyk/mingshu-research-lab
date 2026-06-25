"""年度运程页面 —— 参考专业命理师流月报告布局。"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from core.monthly_engine import analyze_monthly_fortune
from core.yearly_engine import analyze_yearly_fortune
from core.enhanced_monthly_engine import build_enhanced_month_item, get_direction, get_enhanced_events
from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.ten_gods import get_ten_god


from ui.styles import ELEMENT_COLORS, card_style
from ui.charts import render_yearly_scores_chart

RELATION_COLORS = {
    "喜用相关": "#8BA888",
    "忌神相关": "#B85C4A",
    "平稳观察": "#C4A882",
    "喜忌混杂": "#B8860B",
}


def _tags_text(tags):
    return "、".join(tags) if tags else "平稳观察"


def _split_gan_zhi(pillar):
    """拆分干支。"""
    if len(pillar) >= 2:
        return pillar[0], pillar[1]
    return "", ""


def _build_enhanced_monthly_list(chart, target_year, monthly_data):
    """基于现有月度数据构建增强版流月列表，匹配参考图格式。"""
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    day_master = chart.get("day_master", "")
    enhanced = []

    for item in monthly_data:
        gan = item.get("gan", "")
        zhi = item.get("zhi", "")
        gan_element = STEM_ELEMENTS.get(gan, "")
        zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
        ten_god = get_ten_god(day_master, gan) if gan else "未知"

        elements = [e for e in [gan_element, zhi_element] if e]
        score = 0
        for e in elements:
            if e in favorable:
                score += 1
            if e in unfavorable:
                score -= 1
        relation = "喜用相关" if score > 0 else "忌神相关" if score < 0 else "平稳观察"

        branch_rels = item.get("branch_relations", analyze_year_branch_relations(chart, zhi))

        ei = build_enhanced_month_item(
            month=item.get("month"),
            month_name=item.get("month_name"),
            pillar=item.get("pillar"),
            gan=gan, zhi=zhi,
            gan_element=gan_element, zhi_element=zhi_element,
            ten_god=ten_god,
            relation=relation,
            branch_relations=branch_rels,
        )
        enhanced.append(ei)
    return enhanced


def render_yearly_page():
    """渲染年度运程与流月分析页面，参考专业命理报告布局。"""
    chart = st.session_state.get("current_chart")
    if not chart:
        st.info("请先在新建命盘页面生成命盘，或从命盘档案中加载一个命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    profile = chart.get("profile") or st.session_state.get("current_profile", {})
    current_year = date.today().year
    target_year = st.number_input("选择分析年份", min_value=1900, max_value=2100, value=current_year, step=1)
    target_year = int(target_year)
    luck_data = st.session_state.get("current_luck_data")
    yearly_data = analyze_yearly_fortune(chart, target_year, luck_data)
    monthly_data = analyze_monthly_fortune(chart, target_year)
    st.session_state["current_yearly_data"] = yearly_data
    st.session_state["current_monthly_data"] = monthly_data

    # Build enhanced monthly list with more specific content
    enhanced_months = _build_enhanced_monthly_list(chart, target_year, monthly_data)

    # ====== 年度总览 ======
    st.title(f"{target_year}年 年度运程")
    st.caption(
        f"命盘：{profile.get('name', '未命名')} | 日主：{chart.get('day_master', '')} | "
        f"流年：{yearly_data.get('pillar', '')}")
    st.divider()

    # 年度概要卡片
    st.markdown("### 📋 年度概要")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:12px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="font-size:12px;color:#8C7A64;">流年干支</div>'
            f'<div style="font-size:22px;font-weight:700;">{yearly_data.get("pillar", "")}</div>'
            f"</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:12px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="font-size:12px;color:#8C7A64;">流年十神</div>'
            f'<div style="font-size:22px;font-weight:700;">{yearly_data.get("ten_god", "")}</div>'
            f"</div>", unsafe_allow_html=True)
    with col3:
        rel = yearly_data.get("relation_to_favorable", "")
        rel_color = RELATION_COLORS.get(rel, "#888")
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:12px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="font-size:12px;color:#8C7A64;">喜忌关系</div>'
            f'<div style="font-size:18px;font-weight:700;color:{rel_color};">{rel}</div>'
            f"</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:12px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
            f'<div style="font-size:12px;color:#8C7A64;">年度倾向</div>'
            f'<div style="font-size:22px;font-weight:700;">{yearly_data.get("overall_level", "")}</div>'
            f"</div>", unsafe_allow_html=True)

    # 年度评分图
    try:
        scores = {}
        fr = yearly_data.get("favorable_elements", [])
        yr = yearly_data.get("unfavorable_elements", [])
        scores["事业能量"] = min(90, 50 + len(fr) * 10) if fr else 50
        scores["财运机遇"] = min(90, 40 + len(fr) * 12) if fr else 40
        scores["人际和谐"] = min(90, 55 - len(yr) * 8) if yr else 60
        opposite = [e for e in yr if e in fr]
        scores["总体运势"] = min(90, 45 + (len(fr) - len(opposite)) * 10)
        if scores:
            st.markdown("### 🎯 年度评分")
            fig = render_yearly_scores_chart(scores)
            st.altair_chart(fig, width='stretch')
    except Exception:
        pass

    st.markdown("""---""")

    # 年度关键词
    keywords = yearly_data.get("annual_keywords", yearly_data.get("keywords", []))
    if keywords:
        st.markdown("### 🏷 年度关键词")
        tags_html = "".join(
            f'<span style="display:inline-block;background:#EDE6DC;color:#5C4A32;border-radius:12px;padding:4px 12px;font-size:14px;margin:3px 4px;">{kw}</span>'
            for kw in keywords
        )
        st.markdown(tags_html, unsafe_allow_html=True)

    # 年度总览文字
    st.markdown(yearly_data.get("overall_text", ""))

    # 专项分析
    st.markdown("### 📊 年度专项分析")
    tab1, tab2, tab3, tab4 = st.tabs(["💼 事业", "💰 财运", "💞 关系", "🏥 健康"])
    with tab1:
        grp_start = '<div class="sect-card" style="{}">'.format(card_style())
        st.markdown(f'{grp_start}', unsafe_allow_html=True)
        st.markdown(yearly_data.get("career_text", ""))
        # 月份解析
        cg = yearly_data.get("career_good_months", [])
        cb = yearly_data.get("career_bad_months", [])
        if cg:
            st.markdown("**📈 利好月份**")
            tags = "".join(f'<span style="display:inline-block;background:#8BA888;color:#F0F4EC;border-radius:10px;padding:2px 10px;font-size:12px;margin:2px 3px;">{m}</span>' for m in cg)
            st.markdown(tags, unsafe_allow_html=True)
        if cb:
            st.markdown("**⚠️ 谨慎月份**")
            tags = "".join(f'<span style="display:inline-block;background:#B85C4A;color:#FCF0EC;border-radius:10px;padding:2px 10px;font-size:12px;margin:2px 3px;">{m}</span>' for m in cb)
            st.markdown(tags, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        grp_start = '<div class="sect-card" style="{}">'.format(card_style())
        st.markdown(f'{grp_start}', unsafe_allow_html=True)
        st.markdown(yearly_data.get("wealth_text", ""))
        wg = yearly_data.get("wealth_good_months", [])
        wb = yearly_data.get("wealth_bad_months", [])
        if wg:
            st.markdown("**💰 财机月份**")
            tags = "".join(f'<span style="display:inline-block;background:#8BA888;color:#F0F4EC;border-radius:10px;padding:2px 10px;font-size:12px;margin:2px 3px;">{m}</span>' for m in wg)
            st.markdown(tags, unsafe_allow_html=True)
        if wb:
            st.markdown("**⚠️ 谨慎月份**")
            tags = "".join(f'<span style="display:inline-block;background:#B85C4A;color:#FCF0EC;border-radius:10px;padding:2px 10px;font-size:12px;margin:2px 3px;">{m}</span>' for m in wb)
            st.markdown(tags, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        grp_start = '<div class="sect-card" style="{}">'.format(card_style())
        st.markdown(f'{grp_start}', unsafe_allow_html=True)
        st.markdown(yearly_data.get("relationship_text", ""))
        peach = yearly_data.get("peach_months", [])
        if peach:
            st.markdown("**🌸 桃花月份**")
            tags = "".join(f'<span style="display:inline-block;background:#D4A843;color:#3D2B1A;border-radius:10px;padding:2px 10px;font-size:12px;margin:2px 3px;">{m}</span>' for m in peach)
            st.markdown(tags, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        grp_start = '<div class="sect-card" style="{}">'.format(card_style())
        st.markdown(f'{grp_start}', unsafe_allow_html=True)
        st.markdown(yearly_data.get("health_text", ""))
        hc = yearly_data.get("health_concerns", [])
        if hc:
            st.markdown("**🏥 健康提醒**")
            for c in hc:
                st.markdown(f"- {c}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 风险与行动
    st.markdown("### ⚠ 风险与行动建议")
    risk_text = yearly_data.get("risk_text", "")
    advice_text = yearly_data.get("advice_text", "")
    if risk_text:
        st.warning(risk_text)
    if advice_text:
        st.info(advice_text)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("**✅ 适合做：**")
        for item in yearly_data.get("suitable_actions", []):
            st.markdown(f"- {item}")
    with col_a2:
        st.markdown("**❌ 不适合做：**")
        for item in yearly_data.get("actions_to_avoid", []):
            st.markdown(f"- {item}")

    # 高关注月份和机会月份
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        high_attention = yearly_data.get("high_attention_months", [])
        if high_attention:
            st.markdown("### 🔴 高关注月份")
            st.write(_tags_text(high_attention))
    with col_m2:
        opportunities = yearly_data.get("opportunity_months", [])
        if opportunities:
            st.markdown("### 🟢 机会月份")
            st.write(_tags_text(opportunities))

    st.markdown("""---""")

    # ====== 12个月流月详细分析 ======
    st.markdown(f"## 📅 {target_year}年 十二个月流月分析")

    # 参考图风格：每个月一个卡片式区块
    for em in enhanced_months:
        month_num = em["month"]
        month_name = em["month_name"]
        pillar = em["pillar"]
        gan = em["gan"]
        zhi = em["zhi"]
        gan_el = em["gan_element"]
        zhi_el = em["zhi_element"]
        ten_god = em["ten_god"]
        relation = em["relation"]
        direction = em["direction"]
        events = em["events"]
        advices = em["advices"]
        gan_advice = em["gan_advice"]
        has_clash = em["has_clash"]
        branch_rels = em["branch_relations"]

        # Pillar display
        gan_color = ELEMENT_COLORS.get(gan_el, "#888")
        zhi_color = ELEMENT_COLORS.get(zhi_el, "#888")
        rel_color = RELATION_COLORS.get(relation, "#888")

        border = "2px solid #B85C4A" if has_clash else "1px solid #EDE6DC"
        bg = "#FAF7F4" if not has_clash else "#B85C4A08"

        st.markdown(
            f'<div style="background:{bg};border:{border};border-radius:14px;padding:16px;margin-bottom:16px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
            f'<span style="font-size:20px;font-weight:700;">{month_name}</span>'
            f'<span style="font-size:18px;font-weight:700;letter-spacing:2px;">{pillar}</span>'
            f'<span style="font-size:14px;color:{gan_color};">天干:{gan}({gan_el})</span>'
            f'<span style="font-size:14px;color:{zhi_color};">地支:{zhi}({zhi_el})</span>'
            f'<span style="font-size:14px;">十神:{ten_god}</span>'
            f'<span style="font-size:14px;color:{rel_color};font-weight:600;">{relation}</span>'
            + ('<span style="color:#FF5722;font-weight:700;">⚠六冲</span>' if has_clash else "")
            + f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        with st.expander(f"📖 {month_name} 详细分析", expanded=False):
            # 大方向
            st.markdown(f"#### 🎯 本月大方向")
            st.info(direction)

            # 大概率事件
            st.markdown(f"#### 📌 大概率事件")
            for evt in events:
                st.markdown(f"- {evt}")

            # 地支关系提醒
            if branch_rels:
                st.markdown("#### 🔗 地支关系")
                for br in branch_rels:
                    st.markdown(f"- {br.get('text', '')}")

            # 行动建议
            st.markdown(f"#### 💡 行动建议")
            for ad in advices:
                st.markdown(f"- {ad}")

            # 天干五行补充
            st.markdown(f"#### 🌿 五行提示")
            st.caption(gan_advice)

    st.markdown("""---""")

    # ====== 月度数据表（保留参考）======
    st.markdown("### 📊 十二个月速览表")
    df_rows = [
        {
            "月份": em["month_name"],
            "月柱": em["pillar"],
            "天干五行": em["gan_element"],
            "地支五行": em["zhi_element"],
            "十神": em["ten_god"],
            "喜忌": em["relation"],
            "本月方向": em["direction"],
            "冲": "⚠" if em["has_clash"] else "",
        }
        for em in enhanced_months
    ]
    st.dataframe(pd.DataFrame(df_rows), width='stretch', hide_index=True)

    # 底部导航备注
    st.caption("本报告基于传统命理模型生成，仅供个人兴趣和文化研究参考。")
