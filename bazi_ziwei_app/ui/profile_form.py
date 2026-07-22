"""新建命盘页面。"""

from __future__ import annotations

from datetime import date

from core.bazi_engine import build_bazi_chart
from report.bazi_report import generate_basic_bazi_report
from utils.runtime_mode import is_public_mode
from utils.session_privacy import touch_private_session
from utils.validators import validate_profile


PROFILE_DRAFT_KEY = "profile_draft"
PROFILE_SOLAR_TIME_KEY = "profile_use_solar_time"


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
    birth_hour: int,
    birth_minute: int,
    birth_place: str,
    use_solar_time: bool,
    birth_longitude: str | float | int | None,
) -> dict:
    """构造新建命盘资料；农历日期由排盘核心统一换算。"""
    calendar_type = "lunar" if calendar_label == "农历" else "solar"
    display_name = name.strip() or ("访客" if is_public_mode() else "")
    payload = {
        "name": display_name,
        "gender": gender,
        "calendar_type": calendar_type,
        "birth_date": birth_date.isoformat(),
        "birth_hour": birth_hour,
        "birth_minute": birth_minute,
        "birth_place": birth_place.strip(),
        "use_solar_time": use_solar_time,
        "use_true_solar_time": use_solar_time,
        "birth_longitude": parse_birth_longitude(birth_longitude) if use_solar_time else None,
    }
    if calendar_type == "lunar":
        payload["lunar_birth_date"] = birth_date.isoformat()
    return payload


def _render_unified_profile_form(draft: dict) -> None:
    """在一个表单中收集、验证并生成命盘。"""
    import streamlit as st

    if PROFILE_SOLAR_TIME_KEY not in st.session_state:
        st.session_state[PROFILE_SOLAR_TIME_KEY] = bool(draft.get("use_solar_time", False))

    with st.container(key="ms5-profile-card", border=True):
        st.caption("可选设置：真太阳时会按出生地经度校正时间。")
        use_solar_time = st.checkbox(
            "使用真太阳时校正",
            key=PROFILE_SOLAR_TIME_KEY,
        )
        draft["use_solar_time"] = bool(use_solar_time)
        if not use_solar_time:
            draft["birth_longitude"] = None
        st.session_state[PROFILE_DRAFT_KEY] = draft

        with st.form("unified_profile_form"):
            st.markdown("### 基本资料")
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

            st.markdown("### 出生日期")
            calendar_label = st.radio(
                "出生日期类型",
                ["公历", "农历"],
                index=0 if draft.get("calendar_label", "公历") == "公历" else 1,
                horizontal=True,
            )
            birth_date = st.date_input(
                "出生日期",
                value=draft.get("birth_date", date(1990, 1, 1)),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
            )
            st.caption("选择农历时，日期会先自动换算为真实公历日期，再进入八字排盘。")

            st.markdown("### 出生时间与地点")
            time_columns = st.columns(2)
            with time_columns[0]:
                birth_hour = st.selectbox(
                    "出生小时",
                    list(range(24)),
                    index=int(draft.get("birth_hour", 10)),
                )
            with time_columns[1]:
                birth_minute = st.selectbox(
                    "出生分钟",
                    list(range(60)),
                    index=int(draft.get("birth_minute", 0)),
                )
            birth_place = st.text_input(
                "出生地点",
                value=draft.get("birth_place", ""),
                placeholder="可为空，如 北京、上海、广州",
            )

            st.markdown("### 高级设置")
            birth_longitude = None
            if use_solar_time:
                st.caption(
                    "真太阳时可能影响时柱；若不确定经度，建议关闭并使用标准北京时间。"
                )
                birth_longitude = st.text_input(
                    "出生地经度（东经）",
                    placeholder="例如：116.4（北京）、121.4（上海）",
                    value=draft.get("birth_longitude") or "",
                )

            privacy_consent = True
            if is_public_mode():
                st.caption(
                    "出生资料只用于本次会话排盘，不写入服务器档案；30 分钟无操作后自动清除。"
                )
                privacy_consent = st.checkbox("我已阅读并同意本次会话隐私说明")
            else:
                st.caption("出生资料只用于本地排盘；公共每日建议不读取这些资料。")
            submitted = st.form_submit_button("生成命盘", type="primary", use_container_width=True)

    if not submitted:
        return
    if is_public_mode() and not privacy_consent:
        st.error("请先阅读并同意本次会话隐私说明。")
        return

    draft.update(
        {
            "name": name,
            "gender": gender,
            "calendar_label": calendar_label,
            "birth_date": birth_date,
            "birth_hour": birth_hour,
            "birth_minute": birth_minute,
            "birth_place": birth_place,
            "use_solar_time": use_solar_time,
            "birth_longitude": birth_longitude,
        }
    )
    st.session_state[PROFILE_DRAFT_KEY] = draft

    try:
        parsed_longitude = parse_birth_longitude(birth_longitude) if use_solar_time else None
        if use_solar_time and parsed_longitude is None:
            raise ValueError("启用真太阳时校正后，请填写出生地经度。")
        profile = _build_profile_payload(
            name=name,
            gender=gender,
            calendar_label=calendar_label,
            birth_date=birth_date,
            birth_hour=birth_hour,
            birth_minute=birth_minute,
            birth_place=birth_place,
            use_solar_time=use_solar_time,
            birth_longitude=parsed_longitude,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    ok, message = validate_profile(profile)
    if not ok:
        st.error(message)
        return
    with st.spinner("正在生成命盘..."):
        chart = build_bazi_chart(profile)
        report = generate_basic_bazi_report(chart) if not chart.get("error") else None
    if chart.get("error"):
        st.error(chart["error"])
        return
    st.session_state["current_profile"] = profile
    st.session_state["current_chart"] = chart
    st.session_state["current_report"] = report
    touch_private_session(st.session_state)
    st.session_state.pop(PROFILE_DRAFT_KEY, None)
    st.session_state.pop(PROFILE_SOLAR_TIME_KEY, None)
    st.session_state["navigate_to"] = "个人命盘"
    st.rerun()


def render_profile_form() -> None:
    """渲染一页式新建命盘表单。"""
    import streamlit as st

    st.title("新建命盘")
    st.caption("一次填写完整资料，确认无误后直接生成个人命盘。")
    draft = st.session_state.setdefault(PROFILE_DRAFT_KEY, {})
    _render_unified_profile_form(draft)
