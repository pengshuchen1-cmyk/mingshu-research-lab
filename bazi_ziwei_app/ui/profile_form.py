"""新建命盘页面。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from core.birth_input_preview import (
    CHINESE_DAYS,
    CHINESE_MONTHS,
    TRADITIONAL_TIMES,
    BirthFormInput,
    build_birth_preview,
    traditional_time,
)
from report.bazi_report import generate_basic_bazi_report
from utils.runtime_mode import is_public_mode
from utils.session_privacy import touch_private_session
from ui.primitives import page_header


PROFILE_DRAFT_KEY = "profile_draft"
PROFILE_SOLAR_TIME_KEY = "profile_use_solar_time"
PROFILE_PREVIEW_KEY = "profile_birth_preview"
PROFILE_PREVIEW_INPUT_KEY = "profile_birth_preview_input"
PUBLIC_PRIVACY_NOTICE = "出生资料会传至本站服务器内存用于排盘，不写入公网命盘数据库。进入 AI 问答后，去身份化命盘事实、问题和近期对话会发送给已配置的云端 AI 服务；原始生日、姓名和地点不会发送给该服务，30 分钟无操作后清除本次会话。"


def _clear_birth_preview(state) -> None:
    state.pop(PROFILE_PREVIEW_KEY, None)
    state.pop(PROFILE_PREVIEW_INPUT_KEY, None)


def _mutable_copy(value: Any) -> Any:
    """Copy deeply immutable preview data into regular session-state containers."""
    if isinstance(value, Mapping):
        return {key: _mutable_copy(item) for key, item in value.items()}
    if isinstance(value, (tuple, frozenset)):
        return [_mutable_copy(item) for item in value]
    return value


def _render_profile_step_indicator(st, *, preview_ready: bool) -> None:
    """显示一页式表单当前所处的填写/确认阶段。"""
    first_class = "complete" if preview_ready else "active"
    second_class = "active" if preview_ready else ""
    st.markdown(
        f"""
        <div class="ms5-stepper" role="list" aria-label="建立命盘进度">
          <div class="ms5-step {first_class}" role="listitem" aria-current="{'false' if preview_ready else 'step'}">
            <span class="ms5-step-number">1</span>
            <span class="ms5-step-copy"><strong>填写出生资料</strong><small>选择日期、时间与基本资料</small></span>
          </div>
          <div class="ms5-step {second_class}" role="listitem" aria-current="{'step' if preview_ready else 'false'}">
            <span class="ms5-step-number">2</span>
            <span class="ms5-step-copy"><strong>核对排盘结果</strong><small>确认预览后生成个人命盘</small></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_birth_longitude(value: str | float | int | None) -> float | None:
    """Parse an east-longitude value without letting malformed form data crash a page."""
    if value is None or str(value).strip() == "":
        return None
    try:
        longitude = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("出生地经度需要填写数字，例如 116.4。") from exc
    if not 0 <= longitude <= 180:
        raise ValueError("出生地经度需在东经 0 到 180 度之间。")
    return longitude


def _build_profile_payload(
    *,
    name: str,
    gender: str,
    calendar_label: str,
    birth_date: date,
    birth_hour: int | None,
    birth_minute: int | None,
    birth_place: str,
    use_solar_time: bool,
    birth_longitude: str | float | int | None,
    is_leap_month: bool = False,
    time_known: bool = True,
) -> dict:
    """构造新建命盘资料；农历日期由排盘核心统一换算。"""
    calendar_type = "lunar" if calendar_label == "农历" else "solar"
    display_name = name.strip() or ("访客" if is_public_mode() else "")
    payload = {
        "name": display_name,
        "gender": gender,
        "calendar_type": calendar_type,
        "birth_date": birth_date.isoformat(),
        "birth_hour": birth_hour if time_known else None,
        "birth_minute": birth_minute if time_known else None,
        "birth_place": birth_place.strip(),
        "use_solar_time": False,
        "use_true_solar_time": False,
        "birth_longitude": None,
        "time_mode": "china_standard",
        "is_leap_month": bool(is_leap_month and calendar_type == "lunar"),
    }
    if calendar_type == "lunar":
        payload["lunar_birth_date"] = birth_date.isoformat()
    return payload


def _render_unified_profile_form(draft: dict) -> None:
    """在一个表单中收集资料，经预览确认后生成命盘。"""
    import streamlit as st

    with st.container(key="ms5-profile-card", border=True):
        st.caption("排盘统一采用中国标准时间（北京时间）。")
        st.session_state[PROFILE_DRAFT_KEY] = draft
        _render_profile_step_indicator(
            st,
            preview_ready=bool(st.session_state.get(PROFILE_PREVIEW_KEY)),
        )

        st.markdown("## 出生日期")
        st.caption("无需输入姓名，只需选择农历或公历的出生日期及时间；性别仍用于排盘规则。")
        calendar_label = st.radio(
            "出生日期类型",
            ["公历", "农历"],
            index=0 if draft.get("calendar_label", "公历") == "公历" else 1,
            key="profile_calendar_label",
            horizontal=True,
        )

        with st.form("unified_profile_form"):
            st.markdown("## 基本资料")
            identity_columns = st.columns(2)
            with identity_columns[0]:
                name_label = "称呼（可选，建议昵称）" if is_public_mode() else "姓名"
                name = st.text_input(name_label, value=draft.get("name", ""))
            with identity_columns[1]:
                gender = st.selectbox(
                    "性别",
                    ["男", "女"],
                    index=0 if draft.get("gender", "男") == "男" else 1,
                )

            solar_date = None
            lunar_year = None
            lunar_month = None
            lunar_day = None
            is_leap_month = False
            if calendar_label == "公历":
                stored_date = draft.get("birth_date", date(1990, 1, 1))
                if not isinstance(stored_date, date):
                    stored_date = date.fromisoformat(str(stored_date))
                solar_date = st.date_input(
                    "公历出生日期",
                    value=stored_date,
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                )
            else:
                lunar_year = st.selectbox(
                    "农历年份",
                    list(range(1900, date.today().year + 1)),
                    index=max(
                        0,
                        min(
                            date.today().year - 1900,
                            int(draft.get("lunar_year", 1990)) - 1900,
                        ),
                    ),
                )
                lunar_month = st.selectbox(
                    "农历月份",
                    list(range(1, 13)),
                    index=max(0, min(11, int(draft.get("lunar_month", 1)) - 1)),
                    format_func=lambda value: f"{CHINESE_MONTHS[value - 1]}月",
                )
                lunar_day = st.selectbox(
                    "农历日期",
                    list(range(1, 31)),
                    index=max(0, min(29, int(draft.get("lunar_day", 1)) - 1)),
                    format_func=lambda value: CHINESE_DAYS[value - 1],
                )
                is_leap_month = st.checkbox(
                    "是否闰月",
                    value=bool(draft.get("is_leap_month", False)),
                )

            st.markdown("## 出生时间与地点")
            time_precision = st.radio(
                "出生时间精度",
                ["精确时间", "传统时辰", "时辰不详"],
                index={
                    "精确时间": 0,
                    "传统时辰": 1,
                    "时辰不详": 2,
                }.get(draft.get("time_precision", "精确时间"), 0),
                horizontal=True,
            )
            birth_hour = None
            birth_minute = None
            time_label = time_precision
            if time_precision == "精确时间":
                time_columns = st.columns(2)
                with time_columns[0]:
                    stored_hour = draft.get("birth_hour", 10)
                    birth_hour = st.selectbox(
                        "出生小时",
                        list(range(24)),
                        index=10 if stored_hour is None else int(stored_hour),
                    )
                with time_columns[1]:
                    birth_minute = st.selectbox(
                        "出生分钟",
                        list(range(60)),
                        index=int(draft.get("birth_minute", 0) or 0),
                    )
            elif time_precision == "传统时辰":
                traditional_label = st.selectbox(
                    "传统时辰",
                    list(TRADITIONAL_TIMES),
                    index=list(TRADITIONAL_TIMES).index(
                        draft.get("traditional_time", "巳时")
                    )
                    if draft.get("traditional_time", "巳时") in TRADITIONAL_TIMES
                    else list(TRADITIONAL_TIMES).index("巳时"),
                )
                birth_hour, birth_minute, time_label = traditional_time(
                    traditional_label
                )
            else:
                st.caption("时辰不详：时柱及与出生时间相关的结论将受到限制。")
            birth_place = st.text_input(
                "出生地点",
                value=draft.get("birth_place", ""),
                placeholder="可为空，如 北京、上海、广州",
            )

            privacy_consent = True
            if is_public_mode():
                st.caption(PUBLIC_PRIVACY_NOTICE)
                privacy_consent = st.checkbox("我已阅读并同意本次会话隐私说明")
            else:
                st.caption("出生资料只用于本地排盘；公共每日建议不读取这些资料。")

            if calendar_label == "公历":
                assert solar_date is not None
                input_year, input_month, input_day = (
                    solar_date.year,
                    solar_date.month,
                    solar_date.day,
                )
            else:
                assert lunar_year is not None
                assert lunar_month is not None
                assert lunar_day is not None
                input_year, input_month, input_day = (
                    lunar_year,
                    lunar_month,
                    lunar_day,
                )

            birth_input = BirthFormInput(
                name=name,
                gender=gender,
                calendar="lunar" if calendar_label == "农历" else "solar",
                year=input_year,
                month=input_month,
                day=input_day,
                hour=birth_hour,
                minute=birth_minute,
                is_leap_month=is_leap_month,
                birth_place=birth_place,
                time_label=time_label,
            )
            current_fingerprint = birth_input.fingerprint()
            saved_fingerprint = st.session_state.get(PROFILE_PREVIEW_INPUT_KEY)
            if saved_fingerprint and saved_fingerprint != current_fingerprint:
                _clear_birth_preview(st.session_state)
                st.info("出生资料已变更，请重新校验并预览。")

            saved_preview = st.session_state.get(PROFILE_PREVIEW_KEY)
            preview_submitted = st.form_submit_button(
                "校验并预览", type="primary", use_container_width=True
            )
            confirm_submitted = False
            if saved_preview:
                st.markdown(f"原始输入：{saved_preview['input_text']}")
                st.markdown(
                    f"标准时间：中国标准时间 {saved_preview['solar_datetime']}"
                )
                st.markdown(
                    f"四柱预览：{' / '.join(saved_preview['pillars'])}"
                )
                st.markdown(f"计算依据：{saved_preview['calculation_basis']}")
                confirm_submitted = st.form_submit_button(
                    "确认生成命盘", type="primary", use_container_width=True
                )

        if preview_submitted:
            if is_public_mode() and not privacy_consent:
                st.error("请先阅读并同意本次会话隐私说明。")
                return
            touch_private_session(st.session_state)
            draft.update(
                {
                    "name": name,
                    "gender": gender,
                    "calendar_label": calendar_label,
                    "birth_date": solar_date
                    or draft.get("birth_date")
                    or date(1990, 1, 1),
                    "lunar_year": lunar_year,
                    "lunar_month": lunar_month,
                    "lunar_day": lunar_day,
                    "birth_hour": birth_hour,
                    "birth_minute": birth_minute,
                    "birth_place": birth_place,
                    "use_solar_time": False,
                    "birth_longitude": None,
                    "is_leap_month": is_leap_month,
                    "time_precision": time_precision,
                    "traditional_time": time_label
                    if time_precision == "传统时辰"
                    else None,
                    "time_known": time_precision != "时辰不详",
                }
            )
            try:
                preview = build_birth_preview(birth_input)
            except ValueError as exc:
                _clear_birth_preview(st.session_state)
                st.error(str(exc))
                return
            converted_date = date.fromisoformat(preview.solar_datetime[:10])
            if converted_date > date.today():
                _clear_birth_preview(st.session_state)
                st.error("出生日期不能晚于今天。")
                return
            st.session_state[PROFILE_PREVIEW_INPUT_KEY] = preview.input_fingerprint
            st.session_state[PROFILE_PREVIEW_KEY] = {
                "profile": _mutable_copy(preview.profile),
                "chart_fingerprint": preview.chart_fingerprint,
                "input_text": preview.input_text,
                "solar_datetime": preview.solar_datetime,
                "pillars": list(preview.pillars),
                "calculation_basis": preview.calculation_basis,
            }
            st.rerun()
            return

        if not confirm_submitted or not saved_preview:
            return
        if current_fingerprint != st.session_state.get(PROFILE_PREVIEW_INPUT_KEY):
            _clear_birth_preview(st.session_state)
            st.error("出生资料已变更，请重新校验并预览。")
            return
        try:
            rebuilt = build_birth_preview(birth_input)
        except ValueError as exc:
            _clear_birth_preview(st.session_state)
            st.error(str(exc))
            return
        if rebuilt.chart_fingerprint != saved_preview["chart_fingerprint"]:
            _clear_birth_preview(st.session_state)
            st.error("命盘结果已变化，请重新校验并预览后再确认。")
            return

        profile = _mutable_copy(rebuilt.profile)
        chart = _mutable_copy(rebuilt.chart)
        with st.spinner("正在生成命盘..."):
            report = generate_basic_bazi_report(chart)
        st.session_state["current_profile"] = profile
        st.session_state["current_chart"] = chart
        st.session_state["current_report"] = report
        touch_private_session(st.session_state)
        st.session_state.pop(PROFILE_DRAFT_KEY, None)
        st.session_state.pop(PROFILE_SOLAR_TIME_KEY, None)
        _clear_birth_preview(st.session_state)
        st.session_state["navigate_to"] = "个人命盘"
        st.rerun()


def render_profile_form() -> None:
    """渲染带有校验预览的一页式新建命盘表单。"""
    import streamlit as st

    page_header(
        "新建命盘",
        "一次填写完整资料，校验预览无误后生成个人命盘。",
        eyebrow="CREATE CHART",
    )
    draft = st.session_state.setdefault(PROFILE_DRAFT_KEY, {})
    _render_unified_profile_form(draft)
