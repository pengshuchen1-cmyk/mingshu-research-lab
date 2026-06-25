"""新建命盘页面。"""

from __future__ import annotations

from datetime import date

from core.bazi_engine import build_bazi_chart
from report.bazi_report import generate_basic_bazi_report
from utils.database import save_profile
from utils.validators import validate_profile


def render_profile_form() -> None:
    """
    渲染新建命盘表单。
    """
    import streamlit as st

    st.title("新建命盘")
    st.markdown(
        f'<div style="background:#FAF7F4;border-radius:10px;padding:20px 24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);'
        f'margin-bottom:16px;">',
        unsafe_allow_html=True,
    )
    with st.form("profile_form"):
        name = st.text_input("姓名")
        gender = st.selectbox("性别", ["男", "女"])
        birth_date = st.date_input("出生日期", value=date(1990, 1, 1))
        birth_hour = st.selectbox("出生小时", list(range(24)), index=10)
        birth_minute = st.selectbox("出生分钟", list(range(60)), index=0)
        birth_place = st.text_input("出生地点", placeholder="可为空")
        use_solar_time = st.checkbox("是否使用真太阳时")
        if use_solar_time:
            st.caption("真太阳时将在后续版本支持，v0.1 暂按标准时间计算。")
        submitted = st.form_submit_button("生成命盘")

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        profile = {
            "name": name.strip(),
            "gender": gender,
            "birth_date": birth_date.isoformat(),
            "birth_hour": birth_hour,
            "birth_minute": birth_minute,
            "birth_place": birth_place.strip(),
            "use_solar_time": use_solar_time,
        }
        ok, message = validate_profile(profile)
        if not ok:
            st.error(message)
            return
        with st.spinner("正在生成命盘..."):
            chart = build_bazi_chart(profile)
            report = generate_basic_bazi_report(chart)
        st.session_state["current_profile"] = profile
        st.session_state["current_chart"] = chart
        st.session_state["current_report"] = report
        if chart.get("error"):
            st.error(chart["error"])
        else:
            st.success("命盘已生成，可切换到八字排盘或五行十神页面查看。")

    chart = st.session_state.get("current_chart")
    report = st.session_state.get("current_report")
    if chart and report and not chart.get("error"):
        st.markdown("### 当前命盘")
        st.write(report.get("summary", ""))
        if st.button("保存命盘"):
            profile_id = save_profile(chart.get("profile", {}), chart, report)
            st.success(f"命盘已保存，档案编号：{profile_id}")
