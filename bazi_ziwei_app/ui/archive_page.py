"""命盘档案页面。"""

from __future__ import annotations

from datetime import date

import pandas as pd

from core.bazi_engine import build_bazi_chart
from report.bazi_report import generate_basic_bazi_report
from utils.database import (
    delete_profile,
    init_db,
    load_profile_chart_report,
    search_profiles,
    update_chart_and_report,
    update_profile_basic,
    update_profile_birth_info,
    update_report,
)
from ui.styles import card_style
from utils.validators import validate_profile


def _parse_date(value: object) -> date:
    """解析日期控件默认值。"""
    try:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return date.today()


def render_archive_page() -> None:
    """
    渲染命盘档案页面。
    """
    import streamlit as st

    st.title("命盘档案")
    init_db()
    st.markdown("### 搜索命盘")
    col1, col2 = st.columns([2, 1])
    keyword = col1.text_input("关键词", placeholder="可输入姓名、出生日期、地点或备注")
    gender = col2.selectbox("性别筛选", ["全部", "男", "女"])

    profiles = search_profiles(keyword=keyword, gender=gender)
    if not profiles:
        st.markdown(
                    '<div style="background:#FAF7F4;border:1px dashed #EDE6DC;'
                    'border-radius:12px;padding:36px 24px;text-align:center;'
                    'margin:20px 0;">'
                    '<div style="font-size:36px;margin-bottom:12px;">📂</div>'
                    '<div style="font-size:16px;font-weight:600;color:#3D2B1A;margin-bottom:6px;">'
                    '暂无符合条件的命盘</div>'
                    '<div style="font-size:13px;color:#8C7A64;line-height:1.6;">'
                    '请先修改搜索条件，或在「新建命盘」页面创建并保存命盘。</div></div>',
                    unsafe_allow_html=True)
        return

    st.markdown("### 已保存命盘")
    st.dataframe(pd.DataFrame(profiles), width='stretch', hide_index=True)
    options = {f"{item['id']}｜{item['name']}｜{item['birth_date']}": item["id"] for item in profiles}
    selected = st.selectbox("选择命盘", list(options.keys()))
    profile_id = options[selected]
    loaded = load_profile_chart_report(profile_id)

    if loaded:
        st.markdown("### 命盘基础信息")
        st.write(
            f"姓名：{loaded.get('name', '')}｜性别：{loaded.get('gender', '')}｜"
            f"出生：{loaded.get('birth_date', '')} {loaded.get('birth_hour', 0):02d}:{loaded.get('birth_minute', 0):02d}"
        )
        st.write(f"出生地点：{loaded.get('birth_place', '') or '未填写'}")
        if loaded.get("note"):
            st.write(f"备注：{loaded.get('note', '')}")
        report = loaded.get("report", {})
        if report:
            st.write(report.get("summary", ""))

        col_load, col_report = st.columns(2)
        if col_load.button("加载到当前命盘"):
            st.session_state["current_profile"] = {
                key: loaded.get(key)
                for key in [
                    "name",
                    "gender",
                    "birth_date",
                    "birth_hour",
                    "birth_minute",
                    "birth_place",
                    "use_solar_time",
                    "note",
                ]
            }
            st.session_state["current_chart"] = loaded.get("chart", {})
            st.session_state["current_report"] = loaded.get("report", {})
            st.success("已加载该命盘，可前往八字排盘、五行十神、大运流年或报告导出页面查看。")

        if col_report.button("重新生成报告"):
            new_report = generate_basic_bazi_report(loaded.get("chart", {}))
            update_report(profile_id, new_report)
            st.session_state["current_report"] = new_report
            st.success("报告已重新生成。")

        st.markdown("### 编辑基础信息")
        with st.form(f"edit_profile_{profile_id}"):
            new_name = st.text_input("姓名", value=loaded.get("name", ""))
            new_birth_place = st.text_input("出生地点", value=loaded.get("birth_place", "") or "")
            new_note = st.text_area("备注", value=loaded.get("note", "") or "", height=90)
            submitted = st.form_submit_button("保存基础信息")
        if submitted:
            update_profile_basic(profile_id, name=new_name, birth_place=new_birth_place, note=new_note)
            st.success("基础信息已保存。")
            st.rerun()

        st.markdown("### 重新排盘")
        st.caption("重新排盘会覆盖当前命盘结果，适合出生时间、性别或地点录入错误时使用。")
        with st.form(f"rebuild_profile_{profile_id}"):
            rebuild_name = st.text_input("姓名", value=loaded.get("name", ""), key=f"rebuild_name_{profile_id}")
            gender_options = ["男", "女"]
            gender_value = loaded.get("gender", "男")
            gender_index = gender_options.index(gender_value) if gender_value in gender_options else 0
            rebuild_gender = st.selectbox("性别", gender_options, index=gender_index, key=f"rebuild_gender_{profile_id}")
            rebuild_birth_date = st.date_input(
                "出生日期",
                value=_parse_date(loaded.get("birth_date")),
                key=f"rebuild_birth_date_{profile_id}",
            )
            col_hour, col_minute = st.columns(2)
            rebuild_hour = col_hour.number_input(
                "出生小时",
                min_value=0,
                max_value=23,
                value=int(loaded.get("birth_hour", 0)),
                step=1,
                key=f"rebuild_hour_{profile_id}",
            )
            rebuild_minute = col_minute.number_input(
                "出生分钟",
                min_value=0,
                max_value=59,
                value=int(loaded.get("birth_minute", 0)),
                step=1,
                key=f"rebuild_minute_{profile_id}",
            )
            rebuild_birth_place = st.text_input(
                "出生地点",
                value=loaded.get("birth_place", "") or "",
                key=f"rebuild_place_{profile_id}",
            )
            rebuild_use_solar_time = st.checkbox(
                "使用真太阳时校正（当前版本仅保存选项，后续继续完善）",
                value=bool(loaded.get("use_solar_time")),
                key=f"rebuild_solar_{profile_id}",
            )
            rebuild_note = st.text_area(
                "备注",
                value=loaded.get("note", "") or "",
                height=90,
                key=f"rebuild_note_{profile_id}",
            )
            confirm_rebuild = st.checkbox(
                "我确认重新排盘会覆盖当前命盘结果，继续执行",
                key=f"confirm_rebuild_{profile_id}",
            )
            rebuild_submitted = st.form_submit_button("重新排盘")
        if rebuild_submitted:
            new_profile = {
                "name": rebuild_name,
                "gender": rebuild_gender,
                "birth_date": rebuild_birth_date.isoformat(),
                "birth_hour": int(rebuild_hour),
                "birth_minute": int(rebuild_minute),
                "birth_place": rebuild_birth_place,
                "use_solar_time": rebuild_use_solar_time,
                "note": rebuild_note,
            }
            ok, message = validate_profile(new_profile)
            if not confirm_rebuild:
                st.error("请先确认：重新排盘会覆盖当前命盘结果。")
            elif not ok:
                st.error(message)
            else:
                new_chart = build_bazi_chart(new_profile)
                new_report = generate_basic_bazi_report(new_chart)
                update_profile_birth_info(profile_id, new_profile)
                update_chart_and_report(profile_id, new_chart, new_report)
                st.session_state["current_profile"] = new_profile
                st.session_state["current_chart"] = new_chart
                st.session_state["current_report"] = new_report
                st.session_state.pop("current_luck_data", None)
                st.session_state.pop("current_yearly_data", None)
                st.session_state.pop("current_monthly_data", None)
                st.success("已重新排盘，并加载为当前命盘。")
                st.rerun()

        st.markdown(
                    f'<div style="{card_style()}border:1px solid #B85C4A40;margin-top:20px;padding:16px 20px;">'
                    '<div style="font-weight:600;color:#B85C4A;font-size:15px;margin-bottom:8px;">'
                    '⚠ 删除命盘</div>'
                    '<div style="font-size:13px;color:#5C4A32;margin-bottom:12px;line-height:1.5;">'
                    '删除操作不可撤销，命盘信息和报告将从本地数据库中永久移除。</div>',
                    unsafe_allow_html=True)
        confirm_delete = st.checkbox("我确认要永久删除该命盘", key=f"confirm_delete_{profile_id}")
        if st.button("删除命盘", disabled=not confirm_delete, type="primary"):
            delete_profile(profile_id)
            st.success("命盘已删除。")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
