"""大运流年页面 —— 参考命理报告风格，增强排版。"""

from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from ui.charts import render_dayun_chart
from core.luck_engine import get_luck_cycles

from ui.charts import STAGE_COLORS

CURRENT_YEAR = datetime.now().year


def _mini_metric_html(label: str, value: object, suffix: str = "") -> str:
    """统一小指标卡。"""
    return (
        '<div class="ms-mini-metric">'
        f'<div class="label">{escape(str(label))}</div>'
        f'<div class="value">{escape(str(value or "待观察"))}{escape(str(suffix))}</div>'
        "</div>"
    )


def _tag_html(label: object, tone: str = "") -> str:
    """统一标签。"""
    class_name = f"ms-tag {tone}".strip()
    return f'<span class="{class_name}">{escape(str(label or "平稳观察"))}</span>'


def _current_luck_item(dayun_list):
    """根据当前年份判断当前大运。"""
    for item in dayun_list:
        if int(item.get("start_year", 0)) <= CURRENT_YEAR <= int(item.get("end_year", 0)):
            return item
    return None


def render_luck_page():
    """渲染大运流年页面。"""
    chart = st.session_state.get("current_chart")
    if not chart:
        st.info('请先在「新建命盘」页面生成命盘。')
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    result = get_luck_cycles(chart.get("profile", {}), chart)
    st.session_state["current_luck_data"] = result
    if not result.get("available"):
        st.info(result.get("message", "当前版本暂未成功获取大运数据，请确认 lunar_python 接口兼容性。后续版本将继续完善。"))
        return

    profile = chart.get("profile", {})
    day_master = chart.get("day_master", "")

    st.markdown(
        f"""
        <section class="v106c-page-hero">
          <div class="v106c-page-eyebrow">LUCK CYCLES · v1.0.6</div>
          <div class="v106c-page-title">大运流年分析</div>
          <div class="v106c-page-subtitle">
            当前命盘：{escape(str(profile.get('name', '未命名')))}｜日主：{escape(str(day_master))}
            ｜当前年份：{CURRENT_YEAR}年。这里重点看十年阶段、当前大运与未来流年的节奏变化。
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ====== 起运信息 ======
    st.markdown("### 起运信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(_mini_metric_html("起运年龄", result.get("start_age", ""), "岁"), unsafe_allow_html=True)
    with col2:
        st.markdown(_mini_metric_html("起运年份", result.get("start_year", ""), "年"), unsafe_allow_html=True)
    with col3:
        st.markdown(_mini_metric_html("起运月份", result.get("start_month", ""), "月"), unsafe_allow_html=True)
    start_text = result.get("start_text", "")
    if start_text:
        st.markdown(f'<div class="ms-report-panel">{escape(str(start_text))}</div>', unsafe_allow_html=True)

    # ====== 当前大运高亮卡片 ======
    dayun_list = result.get("dayun_list", [])
    current_luck = _current_luck_item(dayun_list)

    st.markdown("### 当前大运")
    if current_luck:
        stage_level = current_luck.get("stage_level", "")
        st.markdown(
            '<div class="ms-luck-stage-card current">'
            '<div class="ms-luck-stage-head">'
            f'<div><span class="ms-luck-stage-pillar">{escape(str(current_luck.get("pillar", "")))}</span>'
            f'{_tag_html(current_luck.get("ten_god", ""), "info")}</div>'
            f'<div class="ms-bazi-muted">{escape(str(current_luck.get("start_year", "")))} - {escape(str(current_luck.get("end_year", "")))}年'
            f'｜{escape(str(current_luck.get("start_age", "")))} - {escape(str(current_luck.get("end_age", "")))}岁</div>'
            f'<div>{_tag_html(stage_level)}</div>'
            f"</div>"
            f'<div class="ms-report-text">{escape(str(current_luck.get("stage_text", "")))}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("当前年份暂未匹配到大运阶段，可结合完整大运表继续观察。")

    # ====== 完整大运表 ======
    st.markdown("### 完整大运表")
    dayun_rows = []
    stage_map = {"偏助力": "🟢", "小有助力": "🔵", "平稳观察": "🟡", "略有压力": "🟠", "压力较明显": "🔴"}
    for item in dayun_list:
        stage_level = item.get("stage_level", "")
        icon = stage_map.get(stage_level, "⚪")
        dayun_rows.append({
            "大运": item.get("pillar", ""),
            "年龄": f'{item.get("start_age", "")} - {item.get("end_age", "")}',
            "十神": item.get("ten_god", ""),
            "阶段": f'{icon} {stage_level}',
        })

    df = pd.DataFrame(dayun_rows)

    # Color-code the current luck row
    def _highlight_current(row):
        if current_luck and row["大运"] == current_luck.get("pillar", ""):
            return ["background-color: #B8860B15"] * len(row)
        return [""] * len(row)

    styled_df = df.style.apply(_highlight_current, axis=1)
    st.dataframe(styled_df, width='stretch', hide_index=True)

    # ====== 大运阶段详解 ======
    st.markdown("### 大运各阶段详解")
    for item in dayun_list:
        stage_level = item.get("stage_level", "")
        is_current = (current_luck and item.get("pillar") == current_luck.get("pillar"))
        label = " [当前大运]" if is_current else ""

        title = (
            f'{item.get("start_age", "")} - {item.get("end_age", "")}岁 | '
            f'{item.get("pillar", "")} | {item.get("ten_god", "")}{label}'
        )
        with st.expander(title, expanded=is_current):
            # Stage level badge
            st.markdown(
                f'<div class="ms-report-panel">{_tag_html(stage_level)}'
                f'<div class="ms-report-text" style="margin-top:10px;">'
                f'{escape(str(item.get("stage_summary", item.get("stage_text", ""))))}</div></div>',
                unsafe_allow_html=True,
            )
            # 根据年龄调整章节标签
            end_age = int(item.get("end_age", 99))
            if end_age <= 15:
                st.markdown("**📚 学习成长：**")
                st.write(item.get("career_focus", "以学习和基础能力培养为主。"))
                st.markdown("**🎨 兴趣爱好：**")
                st.write(item.get("wealth_focus", "可以尝试多种兴趣活动，发现自己的特长。"))
                st.markdown("**👨‍👩‍👧‍👦 家庭关系：**")
                st.write(item.get("relationship_focus", "家庭和学校是主要环境，父母的引导和支持很重要。"))
                st.markdown("**⚠ 需关注：**")
                st.write(item.get("risk_focus", "注意身心健康和良好的生活习惯培养。"))
                st.markdown("**💡 成长建议：**")
                st.write(item.get("action_advice", "多接触不同领域的内容，打好知识和身体基础。"))
            elif end_age <= 22:
                st.markdown("**📖 学业发展：**")
                st.write(item.get("career_focus", "学业是这一阶段的核心任务，适合为未来方向做积累。"))
                st.markdown("**🔧 技能培养：**")
                st.write(item.get("wealth_focus", "除了课业，可以开始培养实用技能和兴趣特长。"))
                st.markdown("**🤝 人际关系：**")
                st.write(item.get("relationship_focus", "同学、老师、朋友是主要社交圈，适合建立健康的社交习惯。"))
                st.markdown("**⚠ 需关注：**")
                st.write(item.get("risk_focus", ""))
                st.markdown("**💡 发展建议：**")
                st.write(item.get("action_advice", ""))
            elif end_age <= 28:
                st.markdown("**💼 事业起步：**")
                st.write(item.get("career_focus", ""))
                st.markdown("**💰 财务积累：**")
                st.write(item.get("wealth_focus", ""))
                st.markdown("**💞 感情发展：**")
                st.write(item.get("relationship_focus", ""))
                st.markdown("**⚠ 需关注：**")
                st.write(item.get("risk_focus", ""))
                st.markdown("**💡 行动建议：**")
                st.write(item.get("action_advice", ""))
            else:
                st.markdown("**💼 事业重点：**")
                st.write(item.get("career_focus", ""))
                st.markdown("**💰 财运重点：**")
                st.write(item.get("wealth_focus", ""))
                st.markdown("**💞 关系提醒：**")
                st.write(item.get("relationship_focus", ""))
                st.markdown("**⚠ 风险与状态：**")
                st.write(item.get("risk_focus", ""))
                st.markdown("**💡 行动建议：**")
                st.write(item.get("action_advice", ""))

    st.markdown('<div class="ms-bazi-section"></div>', unsafe_allow_html=True)

    # ====== 未来十年流年 ======
    st.markdown("### 未来十年流年速览")
    yearly_rows = [
        {
            "年份": item.get("year", ""),
            "流年": item.get("pillar", ""),
            "十神": item.get("ten_god", ""),
            "喜忌": item.get("relation_to_favorable", ""),
        }
        for item in result.get("yearly_list", [])
    ]
    st.dataframe(pd.DataFrame(yearly_rows), width='stretch', hide_index=True)

    # 底部备注
    st.caption("本报告基于传统命理模型生成，仅供个人兴趣和文化研究参考。")
