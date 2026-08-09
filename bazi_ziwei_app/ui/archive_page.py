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
from utils.validators import validate_profile
from ui.primitives import card, empty_state_header, page_header, section_header


def _parse_date(value: object) -> date:
    """解析日期控件默认值。"""
    try:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return date.today()


def _format_birth_time(hour: object, minute: object) -> str:
    if hour is None or minute is None:
        return "时辰不详"
    return f"{int(hour):02d}:{int(minute):02d}"


def _time_input_default(value: object, default: int = 0) -> int:
    return default if value is None or value == "" else int(value)


def _build_rebuild_profile(
    *,
    name: str,
    gender: str,
    calendar_label: str,
    birth_date: date,
    birth_hour: int,
    birth_minute: int,
    birth_place: str,
    is_leap_month: bool,
    time_known: bool,
    note: str,
) -> dict:
    """Build a rebuild payload without losing lunar/leap-month semantics."""
    calendar_type = "lunar" if calendar_label == "农历" else "solar"
    profile = {
        "name": name,
        "gender": gender,
        "calendar_type": calendar_type,
        "birth_date": birth_date.isoformat(),
        "birth_hour": int(birth_hour) if time_known else None,
        "birth_minute": int(birth_minute) if time_known else None,
        "birth_place": birth_place,
        "is_leap_month": bool(is_leap_month and calendar_type == "lunar"),
        "time_mode": "china_standard",
        "time_known": bool(time_known),
        "use_solar_time": False,
        "use_true_solar_time": False,
        "note": note,
    }
    if calendar_type == "lunar":
        profile["lunar_birth_date"] = birth_date.isoformat()
    return profile


def _render_archive_empty_state() -> None:
    """引导首次使用者创建本机保存的命盘。"""
    import streamlit as st

    empty_state_header(
        "还没有保存的命盘",
        "数据仅保存在本机。建立命盘后，你可以在这里加载、编辑或删除自己的资料。",
    )
    if st.button("开始个人分析", type="primary", use_container_width=True):
        st.session_state["navigate_to"] = "新建命盘"
        st.rerun()


def render_archive_page() -> None:
    """
    渲染命盘档案页面。
    """
    import streamlit as st

    page_header(
        "我的命盘",
        "搜索、加载与维护保存在本机的命盘资料。",
        eyebrow="ARCHIVE",
    )
    init_db()
    with card("archive-search"):
        section_header("搜索命盘")
        col1, col2 = st.columns([2, 1])
        keyword = col1.text_input("关键词", placeholder="可输入姓名、出生日期、地点或备注")
        gender = col2.selectbox("性别筛选", ["全部", "男", "女"])

    profiles = search_profiles(keyword=keyword, gender=gender)
    if not profiles:
        with card("archive-empty", tone="muted", size="lg"):
            _render_archive_empty_state()
        return

    section_header("已保存命盘")
    st.dataframe(pd.DataFrame(profiles), width='stretch', hide_index=True)
    options = {f"{item['id']}｜{item['name']}｜{item['birth_date']}": item["id"] for item in profiles}
    selected = st.selectbox("选择命盘", list(options.keys()))
    profile_id = options[selected]
    loaded = load_profile_chart_report(profile_id)

    if loaded:
        section_header("命盘基础信息")
        st.write(
            f"姓名：{loaded.get('name', '')}｜性别：{loaded.get('gender', '')}｜"
            f"出生：{loaded.get('birth_date', '')} "
            f"{_format_birth_time(loaded.get('birth_hour'), loaded.get('birth_minute'))}"
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
                    "calendar_type",
                    "birth_date",
                    "lunar_birth_date",
                    "birth_hour",
                    "birth_minute",
                    "birth_place",
                    "is_leap_month",
                    "time_mode",
                    "time_known",
                    "use_solar_time",
                    "note",
                ]
            }
            st.session_state["current_chart"] = loaded.get("chart", {})
            st.session_state["current_report"] = loaded.get("report", {})
            st.session_state.pop("current_luck_data", None)
            st.session_state.pop("current_yearly_data", None)
            st.session_state.pop("current_monthly_data", None)
            st.session_state.pop("current_monthly_event_results", None)
            st.session_state["navigate_to"] = "八字排盘"
            st.success("已加载该命盘，正在打开「八字排盘」。")
            st.rerun()

        if col_report.button("重新生成"):
            new_report = generate_basic_bazi_report(loaded.get("chart", {}))
            update_report(profile_id, new_report)
            st.session_state["current_report"] = new_report
            st.success("报告已重新生成。")

        section_header("编辑资料")
        with st.form(f"edit_profile_{profile_id}"):
            new_name = st.text_input("姓名", value=loaded.get("name", ""))
            new_birth_place = st.text_input("出生地点", value=loaded.get("birth_place", "") or "")
            new_note = st.text_area("备注", value=loaded.get("note", "") or "", height=90)
            submitted = st.form_submit_button("保存基础信息")
        if submitted:
            update_profile_basic(profile_id, name=new_name, birth_place=new_birth_place, note=new_note)
            st.success("基础信息已保存。")
            st.rerun()

        section_header("重新排盘", "重新排盘会覆盖当前命盘结果，适合出生时间、性别或地点录入错误时使用。")
        with st.form(f"rebuild_profile_{profile_id}"):
            rebuild_name = st.text_input("姓名", value=loaded.get("name", ""), key=f"rebuild_name_{profile_id}")
            gender_options = ["男", "女"]
            gender_value = loaded.get("gender", "男")
            gender_index = gender_options.index(gender_value) if gender_value in gender_options else 0
            rebuild_gender = st.selectbox("性别", gender_options, index=gender_index, key=f"rebuild_gender_{profile_id}")
            calendar_options = ["公历", "农历"]
            calendar_index = 1 if loaded.get("calendar_type") == "lunar" else 0
            rebuild_calendar_label = st.radio(
                "出生日期类型",
                calendar_options,
                index=calendar_index,
                horizontal=True,
                key=f"rebuild_calendar_{profile_id}",
            )
            rebuild_is_leap_month = False
            if rebuild_calendar_label == "农历":
                rebuild_is_leap_month = st.checkbox(
                    "是否闰月",
                    value=bool(loaded.get("is_leap_month")),
                    key=f"rebuild_leap_{profile_id}",
                )
            source_date = (
                loaded.get("lunar_birth_date")
                if rebuild_calendar_label == "农历"
                else loaded.get("birth_date")
            )
            rebuild_birth_date = st.date_input(
                "出生日期",
                value=_parse_date(source_date),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key=f"rebuild_birth_date_{profile_id}",
            )
            rebuild_time_known = not st.checkbox(
                "出生时辰不详",
                value=not bool(loaded.get("time_known", loaded.get("birth_hour") is not None)),
                key=f"rebuild_time_unknown_{profile_id}",
            )
            col_hour, col_minute = st.columns(2)
            rebuild_hour = col_hour.number_input(
                "出生小时",
                min_value=0,
                max_value=23,
                value=_time_input_default(loaded.get("birth_hour")),
                step=1,
                key=f"rebuild_hour_{profile_id}",
            )
            rebuild_minute = col_minute.number_input(
                "出生分钟",
                min_value=0,
                max_value=59,
                value=_time_input_default(loaded.get("birth_minute")),
                step=1,
                key=f"rebuild_minute_{profile_id}",
            )
            rebuild_birth_place = st.text_input(
                "出生地点",
                value=loaded.get("birth_place", "") or "",
                key=f"rebuild_place_{profile_id}",
            )
            st.caption("排盘统一采用中国标准时间（北京时间）。")
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
            new_profile = _build_rebuild_profile(
                name=rebuild_name,
                gender=rebuild_gender,
                calendar_label=rebuild_calendar_label,
                birth_date=rebuild_birth_date,
                birth_hour=int(rebuild_hour),
                birth_minute=int(rebuild_minute),
                birth_place=rebuild_birth_place,
                is_leap_month=rebuild_is_leap_month,
                time_known=rebuild_time_known,
                note=rebuild_note,
            )
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
                st.session_state.pop("current_monthly_event_results", None)
                st.success("已重新排盘，并加载为当前命盘。")
                st.rerun()

        section_header("删除命盘", "删除后无法恢复，请确认当前命盘已经不再需要。")
        confirm_delete = st.checkbox("确认删除：我了解这会删除该命盘及相关报告", key=f"confirm_delete_{profile_id}")
        if st.button("删除命盘", disabled=not confirm_delete):
            delete_profile(profile_id)
            st.success("命盘已删除。")
            st.rerun()
