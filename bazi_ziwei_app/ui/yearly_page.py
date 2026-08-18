"""年度运程页面 —— 参考专业命理师流月报告布局。"""

from __future__ import annotations

from datetime import date
from html import escape
import re

import streamlit as st

from core.enhanced_monthly_engine import build_enhanced_month_item
from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.branch_relations import analyze_year_branch_relations
from core.popular_advice_engine import (
    PopularAdviceUnavailableError,
    build_daily_advice,
    build_yearly_popular_advice,
)
from core.presentation_models import (
    build_daily_guidance_view,
    build_yearly_guidance_view,
)
from core.ten_gods import get_ten_god


from core.monthly_event_activation_bridge import build_year_monthly_event_results
from ui.bazi_components import CACHE_VERSION
from utils.analysis_session_cache import get_or_build_year_analysis

_ACTIVE_MONTH_KEY = "ms3_active_month_index"
_TODAY_VIEW_KEY = "ms_today_view"
_REFLECTION_PERIOD_KEY = "ms_reflection_period"


def _daily_score(daily: dict | None) -> int | None:
    """Return a fixed self-reflection starting point, never an engine score."""
    return 88 if daily else None


def build_reflection_cards(daily: dict | None, yearly: dict, period: str) -> list[dict]:
    """Reuse local daily guidance as reflection prompts, never as diagnosis."""
    if period in {"周", "月"}:
        period_copy = "这一周" if period == "周" else "这个月"
        return [
            {"title": "现实进展", "prompt": f"{period_copy}，哪些事情真实发生了变化，哪些还只是想法？"},
            {"title": "精力分配", "prompt": f"{period_copy}，什么最消耗我，什么确实帮助我恢复？"},
            {"title": "下一小步", "prompt": f"基于{period_copy}已经发生的事实，我愿意完成哪一个可验证的小行动？"},
        ]
    if period == "年":
        focus = str(yearly.get("focus") or "整理年度重点")
        theme = str(yearly.get("theme") or "边行动边校准")
        actions = yearly.get("actions") or []
        action = str(actions[0]) if actions else "选择一个长期方向"
        return [
            {"title": "年度主题", "prompt": f"面对“{theme}”，今年我最想守住的现实重点是什么？"},
            {"title": "长期方向", "prompt": f"围绕“{focus}”，哪些现实反馈值得持续记录？"},
            {"title": "年度行动", "prompt": f"怎样把“{action}”拆成可复盘的小步骤？"},
        ]
    daily = daily or {}
    details = daily.get("details") or {}
    focus = str(daily.get("focus") or "整理当下重点")
    reminder = str(daily.get("reminder") or "避免过度消耗")
    relaxation = str(details.get("relaxation") or "给自己留一点安静恢复的时间")
    return [
        {"title": "注意力", "prompt": f"今天，什么事情最值得我把注意力放在“{focus}”上？"},
        {"title": "边界感", "prompt": f"当我发现自己开始“{reminder}”时，可以用什么现实信号提醒自己停一下？"},
        {"title": "恢复力", "prompt": f"今天，怎样把“{relaxation}”变成一个真正能完成的小行动？"},
    ]


def _render_reflection_view(daily: dict | None, yearly: dict) -> None:
    st.markdown("## 心理解读")
    st.caption("日与年复用相应公开建议；周/月仅做现实复盘，不包含周期预测。不是心理诊断，也不是确定预测。")
    periods = ("日", "周", "月", "年")
    current = st.session_state.get(_REFLECTION_PERIOD_KEY, "日")
    columns = st.columns(4)
    for column, period in zip(columns, periods):
        if column.button(
            period,
            key=f"reflection_period_{period}",
            type="primary" if current == period else "secondary",
            use_container_width=True,
        ):
            st.session_state[_REFLECTION_PERIOD_KEY] = period
            st.rerun()
    current = st.session_state.get(_REFLECTION_PERIOD_KEY, "日")
    for index, item in enumerate(build_reflection_cards(daily, yearly, current), start=1):
        st.markdown(
            '<article class="ms-reflection-card">'
            f'<span>{index:02d}</span><h3>{escape(item["title"])}</h3>'
            f'<p>{escape(item["prompt"])}</p>'
            '</article>',
            unsafe_allow_html=True,
        )
    if st.button("返回今日概览", use_container_width=True):
        st.session_state[_TODAY_VIEW_KEY] = "overview"
        st.rerun()


def _render_today_score(daily: dict | None) -> None:
    score = _daily_score(daily)
    if score is None:
        return
    theme = str((daily or {}).get("theme") or "稳定节奏")
    with st.container(key="ms-today-score-card"):
        st.markdown(
            '<div class="ms-today-score-copy">'
            '<span>今日得分</span>'
            f'<strong>{score}</strong><small>/ 100</small>'
            f'<p>{escape(theme)} · 默认自评起点，可按现实感受理解，不是命理评分</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("查看心理解读", type="primary", use_container_width=True):
            st.session_state[_TODAY_VIEW_KEY] = "reflection"
            st.rerun()


def _toggle_active_month(index: int) -> None:
    """Open one month at a time; tapping the active month closes it."""
    current = st.session_state.get(_ACTIVE_MONTH_KEY)
    st.session_state[_ACTIVE_MONTH_KEY] = None if current == index else index

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
    basis = event.get("user_visible_basis") or event.get("basis", "")
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
        lines.append(f"依据简写：{basis}")
    lines.append(f"行动建议：{advice}")
    if source_titles:
        lines.append(f"参考来源：{'、'.join(str(item) for item in source_titles[:5])}")
    return "\n\n".join(lines)


_EVIDENCE_TYPE_COPY = {
    "ten_god": "流月十神主题被引动",
    "ten_god_group": "流月十神主题被引动",
    "favorable_relation": "五行喜忌关系提示需要留意",
    "element": "流月五行关系被引动",
    "element_in": "流月五行关系被引动",
    "element_strength": "流月五行关系被引动",
    "unfavorable_any": "五行喜忌关系提示需要留意",
    "day_master_element": "流月五行关系被引动",
    "group_count_at_least": "原局结构提供相关线索",
    "branch_in": "地支关系提示本月留意变化",
    "gender": "个人命盘条件提供相关线索",
    "month_index": "本月节奏位置触发相关提醒",
}
_NEUTRAL_EVIDENCE_TYPES = {
    "month_index",
}
_INTERNAL_EVIDENCE_MARKERS = (
    "month_index",
    "period_id",
    "case_id",
    "pattern_id",
    "师傅原文",
    "样本编号",
)


def _clean_evidence_copy(value: object) -> str:
    """Accept short user copy while rejecting internal sample identifiers."""
    if not isinstance(value, (str, int, float)):
        return ""
    text = " ".join(str(value).split())
    lowered = text.lower()
    if not text or any(marker in lowered for marker in _INTERNAL_EVIDENCE_MARKERS):
        return ""
    if re.search(r"\b20\d{2}_m\d", lowered):
        return ""
    return text[:120]


def _evidence_type_copy(evidence_type: str) -> str:
    if evidence_type in _EVIDENCE_TYPE_COPY:
        return _EVIDENCE_TYPE_COPY[evidence_type]
    if evidence_type.startswith(("is_", "activate_")):
        return "相关命盘主题被流月引动"
    if evidence_type == "clash_any" or evidence_type.startswith("clash_"):
        return "地支关系提示本月留意变化"
    return ""


def _readable_evidence_items(value: object) -> list[str]:
    """Map whitelisted bridge evidence to safe, neutral display copy."""
    if isinstance(value, dict):
        evidence_type = str(value.get("type") or "")
        fallback = _evidence_type_copy(evidence_type)
        if not fallback:
            return []
        if evidence_type in _NEUTRAL_EVIDENCE_TYPES:
            return [fallback]
        for key in ("label", "text", "reason"):
            copy = _clean_evidence_copy(value.get(key))
            if copy:
                return [copy]
        return [fallback]
    if isinstance(value, (list, tuple, set)):
        items = []
        for entry in value:
            items.extend(_readable_evidence_items(entry))
        return list(dict.fromkeys(items))
    return []


def _readable_trigger_items(value: object) -> list[str]:
    """Normalize explicit user-facing trigger factors separately from evidence."""
    if isinstance(value, (list, tuple, set)):
        items = [_clean_evidence_copy(item) for item in value]
        return [item for item in dict.fromkeys(items) if item]
    item = _clean_evidence_copy(value)
    return [item] if item else []


def build_month_card_view(enhanced_month: dict, event_result: dict) -> dict:
    """Build a user-facing month card without leaking inference internals."""
    month = enhanced_month or {}
    result = event_result or {}
    relation = str(month.get("relation") or "平稳观察")
    status = f"{relation}｜留意变动" if month.get("has_clash") else relation
    result_basis = str(result.get("basis") or "").strip()
    visible_events = []

    for event in (result.get("top_events") or [])[:3]:
        event = event or {}
        signals = [str(item) for item in (event.get("real_world_signals") or []) if str(item).strip()]
        trigger_factors = event.get("trigger_factors")
        triggers = (
            _readable_trigger_items(trigger_factors)
            if trigger_factors
            else _readable_evidence_items(event.get("evidence"))
        )[:3]
        reason = str(event.get("reason") or "").strip()
        visible_events.append(
            {
                "title": str(event.get("label") or "重点事件"),
                "probability": str(event.get("probability_level") or "需观察"),
                "summary": str(
                    event.get("plain_summary")
                    or event.get("one_line")
                    or reason
                    or "本月相关事务需结合现实进展观察。"
                ),
                "reality": reason
                or ("、".join(signals[:4]) if signals else "暂无明确现实信号，留意计划与沟通的实际变化。"),
                "triggers": triggers,
                "basis": str(
                    event.get("user_visible_basis")
                    or event.get("basis")
                    or result_basis
                    or "根据流月十神、五行喜忌与地支关系作趋势参考。"
                ),
                "advice": str(event.get("advice") or "稳妥推进，重要事项留出复核与调整时间。"),
            }
        )

    event_tags = [event["title"] for event in visible_events]
    if not visible_events:
        visible_events = [
            {
                "title": "本月暂无明确重点事件",
                "probability": "需观察",
                "summary": "当前没有突出信号，请结合现实进展观察。",
                "reality": "计划、沟通与资源安排暂无明显变化。",
                "triggers": [],
                "basis": result_basis or "本月暂无足够的重点事件依据。",
                "advice": "保持日常节奏，有新信息时再做调整。",
            }
        ]

    return {
        "month_name": str(month.get("month_name") or "本月"),
        "pillar": str(month.get("pillar") or "待排定"),
        "status": status,
        "direction": str(month.get("direction") or "按现实进展稳步推进，为调整保留余量。"),
        "event_tags": event_tags,
        "events": visible_events,
    }


def _render_month_timeline(month_views: list[dict]) -> None:
    """Render all twelve monthly rhythm nodes with textual state labels."""
    nodes = "".join(
        '<div class="ms3-month-node">'
        f'<span>{escape(str(month.get("month_name") or "本月"))}</span>'
        f'<strong>{escape(str(month.get("status") or "平稳观察"))}</strong>'
        "</div>"
        for month in month_views[:12]
    )
    st.markdown(
        '<section class="ms3-month-rhythm" aria-label="全年十二月节奏">'
        '<div class="ms3-month-rhythm-head"><p>YEAR RHYTHM</p><h3>全年节奏线</h3></div>'
        f'<div class="ms3-month-timeline">{nodes}</div>'
        "</section>",
        unsafe_allow_html=True,
    )


def _render_month_card(month_view: dict, index: int) -> None:
    """Render one compact month card and its progressive event disclosure."""
    tags = month_view.get("event_tags") or []
    tag_html = "".join(
        f'<span class="ms3-month-tag">{escape(str(tag))}</span>' for tag in tags[:3]
    )
    if not tag_html:
        tag_html = '<span class="ms3-month-tag is-empty">暂无明确事件标签</span>'

    st.markdown(
        '<article class="ms3-month-card">'
        '<div class="ms3-month-card-head">'
        f'<p>{escape(str(month_view.get("month_name") or "本月"))}</p>'
        f'<strong>{escape(str(month_view.get("pillar") or "待排定"))}</strong>'
        "</div>"
        f'<div class="ms3-month-status">{escape(str(month_view.get("status") or "平稳观察"))}</div>'
        f'<p class="ms3-month-direction">{escape(str(month_view.get("direction") or ""))}</p>'
        f'<div class="ms3-month-tags">{tag_html}</div>'
        "</article>",
        unsafe_allow_html=True,
    )

    is_open = st.session_state.get(_ACTIVE_MONTH_KEY) == index
    button_label = "收起重点事件" if is_open else "查看重点事件"
    st.button(
        button_label,
        key=f"monthly-events-{index}",
        use_container_width=True,
        on_click=_toggle_active_month,
        args=(index,),
    )
    if not is_open:
        return

    for event in month_view.get("events") or []:
        title = str(event.get("title") or "重点事件")
        triggers = event.get("triggers") or []
        trigger_text = "、".join(str(item) for item in triggers) or "暂无明确触发因素"
        st.markdown(
            '<section class="ms3-month-event">'
            '<div class="ms3-month-event-head">'
            f'<h4>{escape(title)}</h4>'
            f'<span>可能性｜{escape(str(event.get("probability") or "需观察"))}</span>'
            "</div>"
            '<div class="ms3-month-event-details">'
            f'<div><span>一句话</span><p>{escape(str(event.get("summary") or ""))}</p></div>'
            f'<div><span>现实表现</span><p>{escape(str(event.get("reality") or ""))}</p></div>'
            f'<div><span>触发因素</span><p>{escape(trigger_text)}</p></div>'
            f'<div><span>行动建议</span><p>{escape(str(event.get("advice") or ""))}</p></div>'
            "</div></section>",
            unsafe_allow_html=True,
        )
        with st.expander(f"依据简写｜{title}", expanded=False):
            st.markdown(
                f'<p class="ms3-month-basis">{escape(str(event.get("basis") or "暂无更多依据。"))}</p>',
                unsafe_allow_html=True,
            )


def _render_mini_metric(label: str, value: object, value_style: str = "") -> str:
    """渲染年度概要小指标卡。"""
    return (
        '<div class="ms-mini-metric">'
        f'<div class="label">{escape(str(label))}</div>'
        f'<div class="value" style="{value_style}">{escape(str(value or "待观察"))}</div>'
        "</div>"
    )


def _render_tags(items: list, tone: str = "") -> str:
    """渲染统一标签。"""
    class_name = f"ms-tag {tone}".strip()
    return "".join(f'<span class="{class_name}">{escape(str(item))}</span>' for item in (items or []))


def _first_sentence(
    value: object,
    limit: int = 88,
    *,
    fallback: str = "这一年适合边行动边校准，把重要选择留给清晰的现实反馈。",
) -> str:
    """Return a compact, readable sentence for editorial cards."""
    text = " ".join(str(value or "").split())
    if not text:
        return fallback
    sentence_end = min(
        (text.find(marker) for marker in "。！？" if marker in text),
        default=-1,
    )
    if 0 <= sentence_end < limit:
        return text[: sentence_end + 1]
    return text if len(text) <= limit else f"{text[:limit]}…"


def _text_items(value: object, limit: int = 3) -> list[str]:
    """Normalize yearly action and keyword fields without changing engine data."""
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()][:limit]
    if value:
        return [str(value).strip()][:limit]
    return []


def _render_year_overview(profile, chart, yearly_data, target_year) -> None:
    """Render the personal yearly cover and three plain-language metrics."""
    name = escape(str((profile or {}).get("name") or "未命名命盘"))
    day_master = escape(str((chart or {}).get("day_master") or "待确认"))
    pillar = escape(str((yearly_data or {}).get("pillar") or "待排定"))
    ten_god = escape(str((yearly_data or {}).get("ten_god") or "待观察"))
    relation = escape(str((yearly_data or {}).get("relation_to_favorable") or "平稳观察"))
    level = escape(str((yearly_data or {}).get("overall_level") or "边走边看"))
    theme = escape(_first_sentence((yearly_data or {}).get("overall_text")))
    keywords = _text_items(
        (yearly_data or {}).get("annual_keywords", (yearly_data or {}).get("keywords", []))
    )
    keyword_html = "".join(
        f'<span class="ms3-year-keyword">{escape(keyword)}</span>' for keyword in keywords
    )

    st.markdown(
        f"""
        <section class="ms3-year-cover" aria-labelledby="ms3-year-title">
          <div class="ms3-year-cover-main">
            <p class="ms3-year-kicker">个人年度分析</p>
            <div class="ms3-year-heading-row">
              <h2 id="ms3-year-title">{int(target_year)}</h2>
              <p>流年 · {pillar}</p>
            </div>
            <p class="ms3-year-theme">{theme}</p>
            <div class="ms3-year-keywords" aria-label="年度关键词">{keyword_html}</div>
          </div>
          <div class="ms3-year-identity">
            <span>当前命盘</span><strong>{name}</strong>
            <span>日主{day_master}</span>
          </div>
        </section>
        <section class="ms3-year-metrics" aria-label="年度核心指标">
          <article class="ms3-year-metric">
            <p>十神</p><strong>{ten_god}</strong>
            <div><span>白话解释</span> 今年更容易围绕“{ten_god}”主题分配注意力与资源。</div>
          </article>
          <article class="ms3-year-metric">
            <p>喜忌</p><strong>{relation}</strong>
            <div><span>白话解释</span> 这是流年五行与命盘需要之间的配合程度。</div>
          </article>
          <article class="ms3-year-metric">
            <p>年度倾向</p><strong>{level}</strong>
            <div><span>白话解释</span> 这是全年节奏概览，具体选择仍要结合月份与现实进展。</div>
          </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_risk_action_cards(yearly_data) -> None:
    """Render risk, priority and boundary insights as conclusion-led cards."""
    data = yearly_data or {}
    risk = escape(
        _first_sentence(
            data.get("risk_text"),
            fallback="目前没有突出的年度风险信号，仍需结合现实变化持续观察。",
        )
    )
    advice = escape(
        _first_sentence(
            data.get("advice_text"),
            fallback="先处理最明确、可验证的一件事，并为调整保留余量。",
        )
    )
    relation = escape(str(data.get("relation_to_favorable") or "平稳观察"))
    level = escape(str(data.get("overall_level") or "边走边看"))
    suitable = _text_items(data.get("suitable_actions"))
    avoid = _text_items(data.get("actions_to_avoid"))
    primary = escape(suitable[0] if suitable else "先处理最明确、可验证的一件事")

    action_rows = "".join(
        '<div class="ms3-action-step">'
        f'<span>{index:02d}</span><p>{escape(item)}</p>'
        "</div>"
        for index, item in enumerate(suitable or ["保留余量，分阶段推进"], start=1)
    )
    suitable_text = "；".join(escape(item) for item in suitable) or "小步验证、保留余量"
    avoid_text = "；".join(escape(item) for item in avoid) or "信息不足时一次性投入过多"

    st.markdown(
        f"""
        <section class="ms3-insight-grid" aria-label="年度风险与行动">
          <article class="ms3-insight-card">
            <p class="ms3-insight-index">01</p><h3>主要风险</h3>
            <div class="ms3-insight-block"><span>结论</span><p>{risk}</p></div>
            <div class="ms3-insight-block"><span>为什么</span><p>流年与命盘呈现“{relation}”，需要为变化和复核留出空间。</p></div>
            <div class="ms3-insight-block"><span>怎么做</span><p>{advice}</p></div>
          </article>
          <article class="ms3-insight-card">
            <p class="ms3-insight-index">02</p><h3>优先行动</h3>
            <div class="ms3-insight-block"><span>结论</span><p>先做：{primary}</p></div>
            <div class="ms3-insight-block"><span>为什么</span><p>{advice}</p></div>
            <div class="ms3-insight-block"><span>怎么做</span>{action_rows}</div>
          </article>
          <article class="ms3-insight-card">
            <p class="ms3-insight-index">03</p><h3>行动边界</h3>
            <div class="ms3-insight-block"><span>结论</span><p>保持“{level}”的节奏，不把年度倾向当成确定结果。</p></div>
            <div class="ms3-insight-block"><span>为什么</span><p>适合与暂缓同时写清，才能在现实变化中及时校准。</p></div>
            <div class="ms3-insight-block ms3-boundary-copy"><span>怎么做</span>
              <p><strong>适合做</strong>{suitable_text}</p>
              <p><strong>暂缓做</strong>{avoid_text}</p>
            </div>
          </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def build_monthly_event_results(
    chart: dict,
    monthly_data: list[dict],
    yearly_data: dict | None = None,
    luck_data: dict | None = None,
) -> list[dict]:
    """年度页面与导出报告共用的全年流月 Top 事件结果。"""
    return build_year_monthly_event_results(chart, monthly_data, yearly_data, luck_data)


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


def _render_public_guidance_hero(daily: dict | None, yearly: dict) -> None:
    """Render public conclusions before supporting colors and rationale."""
    st.markdown(
        '<section class="ms2-page-hero"><p class="ms2-kicker">PUBLIC DAILY GUIDANCE</p>'
        '<h1>今日指引</h1><p>无需出生资料，先从今天开始整理自己的节奏。</p></section>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        if daily is None:
            st.markdown("### 今日重点")
            st.markdown("**今日内容暂时无法生成，请稍后再试。**")
        else:
            st.markdown(f"### 今日重点｜{escape(str(daily['theme']))}")
            st.markdown(f"**{escape(str(daily['focus']))}**")
            st.caption(escape(str(daily["date"])))
    with right:
        st.markdown("### 今日提醒")
        if daily is None:
            st.markdown("**年度内容仍可阅读，明日指引恢复后再查看今日细节。**")
        else:
            st.markdown(f"**{escape(str(daily['reminder']))}**")
        st.caption("这是所有用户共享的公共内容，不是个人命盘预测。")

    st.markdown(f"### 今年的节奏｜{escape(str(yearly['year']))}")
    st.write(escape(str(yearly["theme"])))


def _render_guidance_details(daily: dict | None, yearly: dict) -> None:
    """Render supporting public guidance after the primary conclusions."""
    st.markdown("### 让今天更好执行")
    if daily is None:
        st.info("今日的颜色、穿搭与放松建议暂不可用；年度建议不受影响。")
    else:
        left, right = st.columns(2)
        with left:
            st.markdown(f"**颜色与穿搭**：{escape('、'.join(daily['details']['colors']))}")
            st.write(escape(str(daily["action"])))
        with right:
            st.markdown("**放松与恢复**")
            st.write(escape(str(daily["details"]["relaxation"])))

    with st.expander("依据与边界"):
        if daily is not None:
            st.write(escape(str(daily["basis"])))
            st.caption(daily["boundary_note"])
        st.write(escape(str(yearly["basis"])))
        st.caption(yearly["boundary_note"])


def render_yearly_page():
    """Render public guidance first, then personal yearly analysis when available."""
    yearly = build_yearly_popular_advice()
    try:
        daily = build_daily_guidance_view(advice=build_daily_advice())
    except PopularAdviceUnavailableError:
        daily = None
        st.warning("今日内容暂时无法生成；年度建议仍可阅读，请稍后再试。")

    yearly_view = build_yearly_guidance_view(advice=yearly)
    if daily is not None and st.session_state.get(_TODAY_VIEW_KEY, "overview") == "reflection":
        _render_reflection_view(daily, yearly_view)
        return
    _render_public_guidance_hero(daily, yearly_view)
    _render_today_score(daily)
    _render_guidance_details(daily, yearly_view)
    st.divider()
    st.markdown("## 个人年度分析")

    chart = st.session_state.get("current_chart")
    if not chart:
        st.info("个人年度分析需要出生资料；你可以先阅读上方大众建议，或前往新建命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    profile = chart.get("profile") or st.session_state.get("current_profile", {})

    current_year = date.today().year
    target_year = st.number_input("选择分析年份", min_value=1900, max_value=2100, value=current_year, step=1)
    target_year = int(target_year)
    luck_data = st.session_state.get("current_luck_data")
    yearly_data, monthly_data, monthly_event_results = get_or_build_year_analysis(
        st.session_state,
        chart,
        target_year,
        luck_data,
        version=CACHE_VERSION,
    )

    # Build enhanced monthly list with more specific content
    enhanced_months = _build_enhanced_monthly_list(chart, target_year, monthly_data)

    # ====== 年度总览 ======
    _render_year_overview(profile, chart, yearly_data, target_year)

    # 专项分析
    st.markdown("### 年度专项分析")
    tab1, tab2, tab3, tab4 = st.tabs(["事业", "财运", "关系", "健康"])
    with tab1:
        st.markdown('<div class="ms-report-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="ms-report-text">{escape(str(yearly_data.get("career_text", "")))}</div>', unsafe_allow_html=True)
        # 月份解析
        cg = yearly_data.get("career_good_months", [])
        cb = yearly_data.get("career_bad_months", [])
        if cg:
            st.markdown("**利好月份**")
            st.markdown(_render_tags(cg, "success"), unsafe_allow_html=True)
        if cb:
            st.markdown("**谨慎月份**")
            st.markdown(_render_tags(cb, "danger"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="ms-report-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="ms-report-text">{escape(str(yearly_data.get("wealth_text", "")))}</div>', unsafe_allow_html=True)
        wg = yearly_data.get("wealth_good_months", [])
        wb = yearly_data.get("wealth_bad_months", [])
        if wg:
            st.markdown("**财机月份**")
            st.markdown(_render_tags(wg, "success"), unsafe_allow_html=True)
        if wb:
            st.markdown("**谨慎月份**")
            st.markdown(_render_tags(wb, "danger"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="ms-report-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="ms-report-text">{escape(str(yearly_data.get("relationship_text", "")))}</div>', unsafe_allow_html=True)
        peach = yearly_data.get("peach_months", [])
        if peach:
            st.markdown("**关系互动月份**")
            st.markdown(_render_tags(peach), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="ms-report-panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="ms-report-text">{escape(str(yearly_data.get("health_text", "")))}</div>', unsafe_allow_html=True)
        hc = yearly_data.get("health_concerns", [])
        if hc:
            st.markdown("**状态提醒**")
            for c in hc:
                st.markdown(f"- {c}")
        st.markdown('</div>', unsafe_allow_html=True)

    # 风险与行动
    _render_risk_action_cards(yearly_data)

    # 高关注月份和机会月份
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        high_attention = yearly_data.get("high_attention_months", [])
        if high_attention:
            st.markdown("### 高关注月份")
            st.write(_tags_text(high_attention))
    with col_m2:
        opportunities = yearly_data.get("opportunity_months", [])
        if opportunities:
            st.markdown("### 机会月份")
            st.write(_tags_text(opportunities))

    st.markdown('<div class="ms-bazi-section"></div>', unsafe_allow_html=True)

    # ====== 12个月流月卡与重点事件 ======
    st.markdown(f"## {target_year}年 十二个月流月分析")
    month_views = []
    for index, enhanced_month in enumerate(enhanced_months[:12]):
        event_result = monthly_event_results[index] if index < len(monthly_event_results) else {}
        month_views.append(build_month_card_view(enhanced_month, event_result))

    _render_month_timeline(month_views)
    with st.container(key="ms3-month-grid"):
        for row_start in range(0, len(month_views), 2):
            month_columns = st.columns(2)
            for index in range(row_start, min(row_start + 2, len(month_views))):
                month_view = month_views[index]
                with month_columns[index - row_start]:
                    _render_month_card(month_view, index)

    st.markdown('<div class="ms-bazi-section"></div>', unsafe_allow_html=True)

    # 底部导航备注
    st.caption("本报告基于传统命理模型生成，仅供个人兴趣和文化研究参考。")
