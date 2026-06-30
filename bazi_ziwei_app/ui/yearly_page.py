"""年度运程页面 —— 参考专业命理师流月报告布局。"""

from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from core.monthly_engine import analyze_monthly_fortune
from core.yearly_engine import analyze_yearly_fortune
from core.enhanced_monthly_engine import build_enhanced_month_item, get_direction, get_enhanced_events
from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.ten_gods import get_ten_god


from ui.styles import ELEMENT_COLORS, card_style
from core.monthly_event_inference_engine import build_year_monthly_event_results
from ui.charts import render_yearly_scores_chart
from ui.bazi_components import CACHE_VERSION, render_loaded_profile_hint

RELATION_COLORS = {
    "喜用相关": "#8BA888",
    "忌神相关": "#B85C4A",
    "平稳观察": "#C4A882",
    "喜忌混杂": "#B8860B",
}


def _tags_text(tags):
    return "、".join(tags) if tags else "平稳观察"


def format_monthly_event_for_display(event: dict) -> str:
    """把流月事件 dict 转为用户可读文案，正文不暴露开发字段。"""
    label = event.get("label", "事件")
    probability = event.get("probability_level", "需观察")
    plain_summary = event.get("plain_summary", "")
    reason = event.get("reason", "本月相关事务容易被引动，建议结合现实进展观察。")
    advice = event.get("advice", "建议稳妥推进，重要事项留出核实时间。")
    trigger_factors = event.get("trigger_factors", []) or []
    real_world_signals = event.get("real_world_signals", []) or []
    source_titles = event.get("source_titles", []) or event.get("sources", []) or []
    basis = event.get("basis", "")
    lines = [
        f"**{label}｜{probability}**",
    ]
    if plain_summary:
        lines.append(f"一句话：{plain_summary}")
    lines.append(f"现实表现：{reason}")
    if real_world_signals:
        lines.append(f"可能表现：{'、'.join(str(item) for item in real_world_signals[:6])}")
    if trigger_factors:
        lines.append(f"触发因素：{'、'.join(str(item) for item in trigger_factors[:6])}")
    if basis:
        lines.append(f"命理依据：{basis}")
    lines.append(f"行动建议：{advice}")
    if source_titles:
        lines.append(f"参考来源：{'、'.join(str(item) for item in source_titles[:5])}")
    return "\n\n".join(lines)


def _month_top_event_summary(evt_result: dict) -> str:
    """生成月卡片首屏可见的 Top 事件摘要。"""
    top_events = (evt_result or {}).get("top_events", [])[:3]
    if not top_events:
        return (
            '<div style="font-size:13px;color:#8C7A64;margin-top:8px;">'
            "本月重点事件：需结合现实进展观察</div>"
        )

    tag_html = ""
    for event in top_events:
        label = escape(str(event.get("label", "事件")))
        prob = escape(str(event.get("probability_level", "需观察")))
        tag_html += (
            '<span style="display:inline-block;background:#EDE6DC;color:#3D2B1A;'
            'border-radius:12px;padding:3px 10px;font-size:12px;margin:2px 4px 2px 0;">'
            f"{label}｜{prob}</span>"
        )

    first = top_events[0]
    summary = first.get("plain_summary") or first.get("reason") or "本月相关事务容易被引动。"
    return (
        '<div style="border-top:1px solid #EDE6DC;margin-top:10px;padding-top:10px;">'
        '<div style="font-size:12px;color:#8C7A64;margin-bottom:5px;">本月重点事件</div>'
        f'<div>{tag_html}</div>'
        f'<div style="font-size:13px;color:#5C4A32;line-height:1.6;margin-top:4px;">'
        f"{escape(str(summary))}</div>"
        "</div>"
    )


def build_monthly_event_results(
    chart: dict,
    monthly_data: list[dict],
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> list[dict]:
    """年度页面与导出报告共用的全年流月 Top 事件结果。"""
    return build_year_monthly_event_results(chart, monthly_data, yearly_data, luck_data)


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
    if st.session_state.get("cache_version") != CACHE_VERSION:
        st.session_state["cache_version"] = CACHE_VERSION
        for key in [
            "current_yearly_data",
            "current_monthly_data",
            "current_monthly_event_results",
        ]:
            st.session_state.pop(key, None)

    current_year = date.today().year
    target_year = st.number_input("选择分析年份", min_value=1900, max_value=2100, value=current_year, step=1)
    target_year = int(target_year)
    luck_data = st.session_state.get("current_luck_data")
    yearly_data = analyze_yearly_fortune(chart, target_year, luck_data)
    monthly_data = analyze_monthly_fortune(chart, target_year)
    monthly_event_results = build_monthly_event_results(chart, monthly_data, yearly_data, luck_data)
    st.session_state["current_yearly_data"] = yearly_data
    st.session_state["current_monthly_data"] = monthly_data
    st.session_state["current_monthly_event_results"] = monthly_event_results

    # Build enhanced monthly list with more specific content
    enhanced_months = _build_enhanced_monthly_list(chart, target_year, monthly_data)

    # ====== 年度总览 ======
    st.title(f"{target_year}年 年度运程")
    st.caption(
        f"命盘：{profile.get('name', '未命名')} | 日主：{chart.get('day_master', '')} | "
        f"流年：{yearly_data.get('pillar', '')}")
    render_loaded_profile_hint(profile, chart)
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
            st.altair_chart(fig, use_container_width=True)
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
        evt_result = monthly_event_results[month_num - 1] if month_num <= len(monthly_event_results) else {}
        event_summary_html = _month_top_event_summary(evt_result)

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
            + event_summary_html
            + f"</div>",
            unsafe_allow_html=True,
        )

        # Get source info for this month from monthly_data
        month_source_titles = monthly_data[month_num - 1].get("source_titles", []) if monthly_data and month_num <= len(monthly_data) else []
        month_basis = monthly_data[month_num - 1].get("basis", "") if monthly_data and month_num <= len(monthly_data) else ""

        with st.expander(f"📖 {month_name} 详细分析", expanded=False):
            # 大概率事件 Top 3（v1.2-F）
            try:
                evt_result = monthly_event_results[month_num - 1] if month_num <= len(monthly_event_results) else {}
                top_events = evt_result.get("top_events", [])
                if top_events:
                    st.markdown("#### 📌 本月大概率事件")
                    for i, e in enumerate(top_events[:3]):
                        prob = e.get("probability_level", "需观察")
                        prob_icon = {"较高": "🔴", "中等": "🟡", "需观察": "🟢"}.get(prob, "🟢")
                        st.markdown(f"{prob_icon} {format_monthly_event_for_display(e)}")
                        if i < len(top_events[:3]) - 1:
                            st.divider()
                    
                    signal_rows = []
                    for e in top_events[:3]:
                        for signal in e.get("real_world_signals", [])[:3]:
                            signal_rows.append(signal)
                    if signal_rows:
                        st.markdown("**本月容易落地的现实对象**")
                        st.markdown("、".join(dict.fromkeys(signal_rows)))
            except Exception:
                pass

            # 大方向
            st.markdown(f"#### 🎯 本月大方向")
            st.info(direction)

            # 地支关系提醒
            if branch_rels:
                st.markdown("#### 🔗 地支关系")
                for br in branch_rels:
                    st.markdown(f"- {br.get('text', '')}")

            # 行动建议
            st.markdown(f"#### 💡 行动建议")
            for ad in advices:
                if isinstance(ad, dict):
                    st.markdown(f"- {ad.get('text', str(ad))}")
                else:
                    st.markdown(f"- {ad}")

            # 天干五行补充
            st.markdown(f"#### 🌿 五行提示")
            st.caption(gan_advice)

            # 命理依据 / 参考来源
            with st.expander("📚 命理依据 / 参考来源", expanded=False):
                st.markdown(f"- **流月十神**：{ten_god}")
                st.markdown(f"- **五行关系**：{relation}")
                if branch_rels:
                    for br in branch_rels:
                        st.markdown(f"- **地支关系**：{br.get('label', '')} — {br.get('text', '')}")
                if month_basis:
                    st.markdown(f"- **规则依据**：{month_basis}")
                if month_source_titles:
                    st.markdown(f"- **参考来源**：{'、'.join(month_source_titles)}")

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
    st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True)

    # ====== 流月事件差异化检查（调试折叠区）======
    with st.expander("🛠 流月事件差异化检查（开发调试）", expanded=False):
        try:
            # 获取12个月所有事件
            all_results = monthly_event_results
            
            # 统计 event_type 出现频率
            from collections import Counter
            all_event_types = []
            for r in all_results:
                for e in r.get("top_events", []):
                    all_event_types.append(e.get("event_type", ""))
            type_counts = Counter(all_event_types)
            most_common = type_counts.most_common(3) if type_counts else []
            
            # 连续重复检查
            repeat_count = 0
            prev_top = []
            for r in all_results:
                curr_top = [e["event_type"] for e in r.get("top_events", [])[:3]]
                if prev_top and curr_top == prev_top:
                    repeat_count += 1
                prev_top = curr_top
            
            # 每月独有触发因素
            unique_triggers = set()
            for r in all_results:
                for e in r.get("top_events", []):
                    for f in e.get("trigger_factors", []):
                        unique_triggers.add(f)
            
            st.markdown("**差异化检查结果**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("唯一事件组合", f"{len(set([tuple(e['event_type'] for e in r.get('top_events', [])[:3]) for r in all_results]))}/12")
            with col2:
                st.metric("连续重复月数", repeat_count)
            with col3:
                st.metric("事件类型数", len(type_counts))
            
            if most_common:
                st.markdown("**最常见事件**")
                for et, cnt in most_common:
                    st.markdown(f"- {et}: {cnt}/12 个月")
            
            if unique_triggers:
                st.markdown(f"**触发因素列表（{len(unique_triggers)} 种）**")
                st.markdown("、".join(list(unique_triggers)[:15]))
            
            st.markdown("**12个月事件分布**")
            for i, r in enumerate(all_results):
                mn = monthly_data[i].get("month_name", f"月{i+1}")
                top_types = [e.get("event_type", "") for e in r.get("top_events", [])[:3]]
                top_labels = [e.get("label", "") for e in r.get("top_events", [])[:3]]
                triggers = []
                for event in r.get("top_events", [])[:3]:
                    triggers.extend(event.get("trigger_factors", []) or [])
                st.markdown(f"- {mn}: {' | '.join(top_types)}")
                st.caption(f"事件名称：{' | '.join(top_labels)}")
                st.caption(f"独有触发因素：{'、'.join(dict.fromkeys(triggers)) or '暂无'}")
                
        except Exception as exc:
            st.markdown(f"差异化检查暂不可用：{exc}")

    # 底部导航备注
    st.caption("本报告基于传统命理模型生成，仅供个人兴趣和文化研究参考。")
