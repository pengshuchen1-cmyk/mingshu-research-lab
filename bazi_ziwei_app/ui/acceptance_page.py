"""v1.0.1 人工验收中心。"""

from __future__ import annotations

from difflib import SequenceMatcher
from itertools import combinations

import pandas as pd
import streamlit as st

from core.bazi_engine import build_bazi_chart
from core.chart_fingerprint import build_chart_fingerprint
from core.monthly_engine import analyze_monthly_fortune
from core.monthly_event_inference_engine import build_year_monthly_event_results
from core.yearly_engine import analyze_yearly_fortune
from core.ziwei_engine import build_ziwei_chart
from core.ziwei_readable_engine import build_ziwei_capability_review, build_ziwei_plain_guide
from core.ziwei_sihua_engine import apply_sihua_to_chart, get_sihua_by_year_gan
from core.ziwei_star_engine import get_year_gan_from_profile
from core.ziwei_validation_engine import validate_ziwei_cases
from report.career_report import generate_career_report
from report.love_report import generate_love_report
from report.wealth_report import generate_wealth_report
from ui.yearly_page import format_monthly_event_for_display


ACCEPTANCE_SAMPLE_PROFILES = [
    {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False},
    {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州", "use_solar_time": False},
    {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都", "use_solar_time": False},
    {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
]


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _report_text(report: dict) -> str:
    parts = [" ".join(report.get("evidence", []))]
    for key, value in report.items():
        if key not in {"sections", "disclaimer"}:
            parts.append(str(value))
    for section in report.get("sections", []):
        parts.append(section.get("title", ""))
        parts.append(section.get("text", ""))
    return "\n".join(parts)


def _yearly_text(yearly_data: dict) -> str:
    keys = ["overall_text", "career_text", "wealth_text", "relationship_text", "health_text", "risk_text", "advice_text"]
    return "\n".join(str(yearly_data.get(key, "")) for key in keys)


def _monthly_text(monthly_data: list[dict], event_results: list[dict]) -> str:
    parts: list[str] = []
    for item, events in zip(monthly_data, event_results):
        parts.extend([
            item.get("theme", ""),
            item.get("event_tendency", ""),
            " ".join(item.get("likely_events", [])),
            item.get("career_text", ""),
            item.get("wealth_text", ""),
            item.get("relationship_text", ""),
            item.get("risk_text", ""),
            item.get("advice_text", ""),
        ])
        for event in events.get("top_events", [])[:3]:
            parts.append(event.get("label", ""))
            parts.append(event.get("reason", ""))
            parts.append("、".join(event.get("trigger_factors", []) or []))
    return "\n".join(parts)


def _build_sample(profile: dict) -> dict:
    chart = build_bazi_chart(profile)
    fingerprint = build_chart_fingerprint(chart)
    yearly_data = analyze_yearly_fortune(chart, 2026)
    monthly_data = analyze_monthly_fortune(chart, 2026)
    event_results = build_year_monthly_event_results(chart, monthly_data, yearly_data, None)
    return {
        "profile": profile,
        "chart": chart,
        "fingerprint": fingerprint,
        "yearly": yearly_data,
        "monthly": monthly_data,
        "events": event_results,
        "career": generate_career_report(chart),
        "wealth": generate_wealth_report(chart),
        "love": generate_love_report(chart, profile),
        "ziwei": build_ziwei_chart(profile),
    }


def _max_similarity(samples: list[dict], key: str) -> tuple[float, str]:
    texts = []
    for sample in samples:
        if key in {"career", "wealth", "love"}:
            texts.append(_report_text(sample[key]))
        elif key == "yearly":
            texts.append(_yearly_text(sample["yearly"]))
        else:
            texts.append(_monthly_text(sample["monthly"], sample["events"]))
    max_score = 0.0
    pair = "暂无"
    for left, right in combinations(range(len(texts)), 2):
        score = _similarity(texts[left], texts[right])
        if score > max_score:
            max_score = score
            pair = f"{samples[left]['profile']['name']} vs {samples[right]['profile']['name']}"
    return max_score, pair


def _pillars_table(chart: dict) -> pd.DataFrame:
    pillars = chart.get("pillars", {})
    return pd.DataFrame([
        {"位置": "年柱", "干支": pillars.get("year", {}).get("pillar", "")},
        {"位置": "月柱", "干支": pillars.get("month", {}).get("pillar", "")},
        {"位置": "日柱", "干支": pillars.get("day", {}).get("pillar", "")},
        {"位置": "时柱", "干支": pillars.get("hour", {}).get("pillar", "")},
    ])


def render_acceptance_page() -> None:
    """渲染主程序内验收样例。"""
    st.title("验收中心")
    st.caption("这里集中展示 5 个固定样例，用于人工检查命盘差异化、年度运程和 12 个月流月事件。")

    samples = [_build_sample(profile) for profile in ACCEPTANCE_SAMPLE_PROFILES]

    st.markdown("### 报告差异化检查")
    rows = []
    for label, key in [("事业报告", "career"), ("财运报告", "wealth"), ("婚恋报告", "love"), ("年度运程", "yearly"), ("流月事件", "monthly")]:
        score, pair = _max_similarity(samples, key)
        rows.append({"检查项": label, "最高相似度": round(score, 3), "最高组合": pair, "结果": "通过" if score <= 0.55 else "需复核"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### 五个验收样例")
    sample_names = [sample["profile"]["name"] for sample in samples]
    selected_name = st.selectbox("选择样例", sample_names)
    sample = next(item for item in samples if item["profile"]["name"] == selected_name)

    profile = sample["profile"]
    chart = sample["chart"]
    fp = sample["fingerprint"]
    strength = chart.get("day_master_strength", {})

    st.markdown("#### 基础信息")
    st.write(f"{profile['name']}｜{profile['gender']}｜{profile['birth_date']} {profile['birth_hour']:02d}:{profile['birth_minute']:02d}｜{profile['birth_place']}")
    st.dataframe(_pillars_table(chart), use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("日主", chart.get("day_master", ""))
    col2.metric("日主强弱", strength.get("strength", ""))
    col3.metric("喜用五行", "、".join(strength.get("favorable_elements", [])) or "需观察")
    col4.metric("忌神五行", "、".join(strength.get("unfavorable_elements", [])) or "需观察")

    st.markdown("#### 命盘总览")
    st.write("、".join(fp.get("chart_summary_tags", [])))
    st.write(f"事业标签：{'、'.join(fp.get('career_pattern_tags', []))}")
    st.write(f"财运标签：{'、'.join(fp.get('wealth_pattern_tags', []))}")
    st.write(f"关系标签：{'、'.join(fp.get('love_pattern_tags', []))}")

    tabs = st.tabs(["事业摘要", "财运摘要", "婚恋摘要", "2026年度", "12个月流月", "紫微命盘名片", "紫微盘例校验", "功能边界"])
    with tabs[0]:
        st.write(sample["career"].get("career_identity", ""))
        st.markdown("**命盘依据**")
        for item in sample["career"].get("evidence", [])[:5]:
            st.markdown(f"- {item}")
    with tabs[1]:
        st.write(sample["wealth"].get("wealth_identity", ""))
        st.markdown("**命盘依据**")
        for item in sample["wealth"].get("evidence", [])[:5]:
            st.markdown(f"- {item}")
    with tabs[2]:
        st.write(sample["love"].get("relationship_pattern", ""))
        st.markdown("**命盘依据**")
        for item in sample["love"].get("evidence", [])[:5]:
            st.markdown(f"- {item}")
    with tabs[3]:
        yearly = sample["yearly"]
        st.write(yearly.get("overall_text", ""))
        st.markdown(f"**事业：** {yearly.get('career_text', '')}")
        st.markdown(f"**财运：** {yearly.get('wealth_text', '')}")
        st.markdown(f"**关系：** {yearly.get('relationship_text', '')}")
        st.markdown(f"**健康：** {yearly.get('health_text', '')}")
    with tabs[4]:
        rows = []
        for item, events in zip(sample["monthly"], sample["events"]):
            rows.append({
                "月份": item.get("month_name", ""),
                "流月": item.get("pillar", ""),
                "主题": item.get("theme", ""),
                "Top 3事件": "｜".join(event.get("label", "") for event in events.get("top_events", [])[:3]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        for item, events in zip(sample["monthly"], sample["events"]):
            with st.expander(f"{item.get('month_name', '')}｜{item.get('pillar', '')}｜{item.get('theme', '')}"):
                for event in events.get("top_events", [])[:3]:
                    st.markdown(format_monthly_event_for_display(event))
                    st.divider()
    with tabs[5]:
        ziwei = sample["ziwei"]
        year_gan = get_year_gan_from_profile(profile)
        sihua_data = apply_sihua_to_chart(ziwei, get_sihua_by_year_gan(year_gan))
        guide = build_ziwei_plain_guide(ziwei, sihua_data.get("sihua_by_palace", {}))
        capability_review = build_ziwei_capability_review(ziwei)

        st.write(f"命宫：{ziwei.get('life_palace', '待确认')}｜身宫：{ziwei.get('body_palace', '待确认')}")
        st.info("紫微斗数当前以已生成的宫位、十四主星和生年四化做说明，不把未确认的飞化、紫微流年流月包装成结论。")

        st.markdown("**星曜组合与主星落宫摘要**")
        for card in guide.get("focus_cards", [])[:5]:
            with st.expander(f"{card.get('title', '')}｜{card.get('plain_title', '')}", expanded=card.get("title") in {"命宫说明", "事业宫说明"}):
                st.markdown(f"**一句话先懂**：{card.get('one_sentence', '')}")
                st.markdown(f"**星曜组合**：{card.get('star_combination_text', '')}")
                star_palace_items = card.get("star_palace_explanations", [])
                if star_palace_items:
                    st.markdown("**主星落宫怎么看**")
                    for item in star_palace_items[:3]:
                        st.markdown(f"- **{item.get('title', '')}**：{item.get('plain_text', '')}")
                        st.caption(f"现实提醒：{item.get('real_world_view', '')}｜建议：{item.get('advice', '')}")
                st.caption(f"边界提醒：{card.get('boundary_note', '')}")

        st.markdown("**紫微模块完成度**")
        rows = [
            {
                "项目": item.get("name", ""),
                "状态": item.get("status", ""),
                "普通理解": item.get("user_text", ""),
                "边界": item.get("boundary", ""),
            }
            for item in capability_review.get("items", [])
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with tabs[6]:
        validation = validate_ziwei_cases()
        summary = validation.get("summary", {})
        st.markdown("**紫微盘例校验**")
        st.caption("这里把算法盘面校验和真实反馈校验分开展示。没有真实反馈的样例只标记为待补充，不会当成已经验证。")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("盘例数", summary.get("total_cases", 0))
        c2.metric("有盘面预期", summary.get("known_chart_cases", 0))
        c3.metric("盘面通过", summary.get("chart_passed_cases", 0))
        c4.metric("待真实反馈", summary.get("pending_feedback_cases", 0))

        validation_rows = []
        for item in validation.get("cases", []):
            validation_rows.append({
                "案例": item.get("name", ""),
                "盘面状态": item.get("chart_status", ""),
                "真实反馈": item.get("feedback_status", ""),
                "通过项": item.get("summary", {}).get("passed_checks", 0),
                "复核项": item.get("summary", {}).get("failed_checks", 0),
            })
        if validation_rows:
            st.dataframe(pd.DataFrame(validation_rows), use_container_width=True, hide_index=True)

        for item in validation.get("cases", []):
            with st.expander(f"{item.get('name', '')}｜{item.get('chart_status', '')}｜{item.get('feedback_status', '')}"):
                profile = item.get("profile", {})
                chart = item.get("chart", {})
                st.write(
                    f"{profile.get('gender', '')}｜{profile.get('birth_date', '')} "
                    f"{int(profile.get('birth_hour', 0)):02d}:{int(profile.get('birth_minute', 0)):02d}"
                )
                st.write(f"命宫：{chart.get('life_palace', '待确认')}｜身宫：{chart.get('body_palace', '待确认')}｜五行局：{chart.get('five_element_bureau', '待确认')}")
                if item.get("chart_checks"):
                    st.markdown("**盘面算法校验**")
                    st.dataframe(pd.DataFrame(item.get("chart_checks", [])), use_container_width=True, hide_index=True)
                if item.get("focus_card_rows"):
                    st.markdown("**重点宫位解释抽样**")
                    st.dataframe(pd.DataFrame(item.get("focus_card_rows", [])), use_container_width=True, hide_index=True)
                if item.get("feedback_prompt"):
                    st.markdown("**请补充真实反馈**")
                    for prompt in item.get("feedback_prompt", []):
                        st.markdown(f"- {prompt}")
                st.caption(item.get("boundary", ""))
        st.info(summary.get("next_action", "请补充真实反馈后再做现实命中复核。"))
    with tabs[7]:
        st.warning("本验收中心用于检查本机版报告质量，不作为医疗、法律、投资、婚姻等重大决策依据。")
        st.write("当前重点验收：年度页面不显示 Python 原始 dict、12 个月流月事件有差异、不同命盘报告不再高度相似。")
