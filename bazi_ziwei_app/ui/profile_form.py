"""新建命盘页面。"""

from __future__ import annotations

import calendar
import re
from collections.abc import Mapping
from datetime import date
from functools import partial
from html import escape
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
from lunar_python import LunarYear
from utils.runtime_mode import is_public_mode
from utils.session_privacy import maintain_private_session, touch_private_session
from ui.birth_wheel_picker import (
    BIRTH_WHEEL_COMPONENT_KEY,
    render_birth_wheel,
    validate_wheel_selection,
    wheel_column,
)
from ui.primitives import page_header


PROFILE_DRAFT_KEY = "profile_draft"
PROFILE_SOLAR_TIME_KEY = "profile_use_solar_time"
PROFILE_PREVIEW_KEY = "profile_birth_preview"
PROFILE_PREVIEW_INPUT_KEY = "profile_birth_preview_input"
PROFILE_SUCCESS_RETURN_KEY = "profile_success_return_to"
PROFILE_PASTE_KEY = "profile_paste_source"
PROFILE_NAME_INPUT_KEY = "profile_name_input"
PROFILE_RELATIONSHIP_INPUT_KEY = "profile_relationship_input"
PROFILE_GENDER_INPUT_KEY = "profile_gender_input"
PROFILE_PLACE_INPUT_KEY = "profile_place_input"
PROFILE_PICKER_OPEN_KEY = "profile_picker_open"
PROFILE_PICKER_SNAPSHOT_KEY = "profile_picker_snapshot"
PROFILE_PICKER_CALENDAR_KEY = "profile_picker_calendar"
PROFILE_PICKER_YEAR_KEY = "profile_picker_year"
PROFILE_PICKER_MONTH_KEY = "profile_picker_month"
PROFILE_PICKER_DAY_KEY = "profile_picker_day"
PROFILE_PICKER_HOUR_KEY = "profile_picker_hour"
PROFILE_PICKER_MINUTE_KEY = "profile_picker_minute"
PROFILE_PICKER_PRECISION_KEY = "profile_picker_precision"
PROFILE_PICKER_TRADITIONAL_KEY = "profile_picker_traditional"
PROFILE_PICKER_LEAP_KEY = "profile_picker_leap"
PROFILE_PICKER_KEYS = (
    PROFILE_PICKER_CALENDAR_KEY,
    PROFILE_PICKER_YEAR_KEY,
    PROFILE_PICKER_MONTH_KEY,
    PROFILE_PICKER_DAY_KEY,
    PROFILE_PICKER_HOUR_KEY,
    PROFILE_PICKER_MINUTE_KEY,
    PROFILE_PICKER_PRECISION_KEY,
    PROFILE_PICKER_TRADITIONAL_KEY,
    PROFILE_PICKER_LEAP_KEY,
)
PUBLIC_PRIVACY_NOTICE = "出生资料会传至本站服务器内存用于排盘，不写入公网命盘数据库。进入 AI 问答后，去身份化命盘事实、问题和近期对话会发送给已配置的云端 AI 服务；原始生日、姓名和地点不会发送给该服务，30 分钟无操作后清除本次会话。"


def valid_solar_days(year: int, month: int, *, today: date | None = None) -> list[int]:
    """Return selectable Gregorian days, bounded so a birth date is not future."""
    current = today or date.today()
    if not 1900 <= year <= current.year or not 1 <= month <= 12:
        return []
    if year == current.year and month > current.month:
        return []
    last_day = calendar.monthrange(year, month)[1]
    if year == current.year and month == current.month:
        last_day = min(last_day, current.day)
    return list(range(1, last_day + 1))


def lunar_month_days(year: int, month: int, *, is_leap_month: bool = False) -> list[int]:
    """Return lunar calendar month days from the calendar conversion library."""
    target = -month if is_leap_month else month
    lunar_month = next(
        (item for item in LunarYear.fromYear(year).getMonthsInYear() if item.getMonth() == target),
        None,
    )
    return list(range(1, lunar_month.getDayCount() + 1)) if lunar_month else []


def parse_profile_paste(value: str, *, today: date | None = None) -> dict[str, Any]:
    """Parse only explicit profile fields; the original text is never retained or logged."""
    text = value.strip()
    if not text:
        raise ValueError("请先粘贴明确的资料。")
    parsed: dict[str, Any] = {}
    relationships = [item for item in ("本人", "伴侣", "家人", "朋友") if item in text]
    if len(relationships) > 1:
        raise ValueError("粘贴内容中出现多个关系，请只保留一个。")
    if relationships:
        parsed["relationship"] = relationships[0]
    gender_match = re.search(r"性别[：:\s]*(男|女)|(?<![男女])(男|女)(?:性|士)", text)
    if gender_match:
        parsed["gender"] = gender_match.group(1) or gender_match.group(2)
    datetime_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日(?:\s+(\d{1,2}):(\d{2}))?"
    datetime_matches = list(re.finditer(datetime_pattern, text))
    if len(datetime_matches) > 1:
        raise ValueError("粘贴内容中出现多个日期，请只保留一个。")
    datetime_match = datetime_matches[0] if datetime_matches else None
    if datetime_match:
        year, month, day = (int(datetime_match.group(i)) for i in range(1, 4))
        try:
            parsed_date = date(year, month, day)
        except ValueError as exc:
            raise ValueError("粘贴内容中的公历日期无效，请检查年月日。") from exc
        if parsed_date > (today or date.today()) or year < 1900:
            raise ValueError("粘贴内容中的出生日期超出可用范围。")
        parsed.update(calendar_label="公历", birth_date=parsed_date)
        if datetime_match.group(4) is not None:
            hour, minute = int(datetime_match.group(4)), int(datetime_match.group(5))
            if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                raise ValueError("粘贴内容中的时间无效，请使用 00:00–23:59。")
            parsed.update(
                birth_hour=hour,
                birth_minute=minute,
                time_precision="精确时间",
                time_known=True,
            )
    place_match = re.search(r"出生于\s*([^，,。;；\n]+)", text)
    if place_match:
        parsed["birth_place"] = place_match.group(1).strip()
    name_match = re.search(r"(?:昵称|称呼)[：:]\s*([^，,。;；\n]+)", text)
    if name_match:
        parsed["name"] = name_match.group(1).strip()
    if not parsed:
        raise ValueError("未识别到明确字段；请包含昵称、关系、性别、日期时间或“出生于…”地点。")
    return parsed


def _selected(options: list[Any], value: Any, fallback: Any) -> int:
    return options.index(value) if value in options else options.index(fallback)


def _picker_seed(draft: Mapping[str, Any]) -> dict[str, Any]:
    stored_date = draft.get("birth_date", date(1990, 1, 1))
    try:
        stored_date = stored_date if isinstance(stored_date, date) else date.fromisoformat(str(stored_date))
    except (TypeError, ValueError):
        stored_date = date(1990, 1, 1)
    is_lunar = draft.get("calendar_label") == "农历"
    return {
        PROFILE_PICKER_CALENDAR_KEY: "农历" if is_lunar else "公历",
        PROFILE_PICKER_YEAR_KEY: int(draft.get("lunar_year") or stored_date.year),
        PROFILE_PICKER_MONTH_KEY: int(draft.get("lunar_month") or stored_date.month),
        PROFILE_PICKER_DAY_KEY: int(draft.get("lunar_day") or stored_date.day),
        PROFILE_PICKER_HOUR_KEY: draft.get("birth_hour", 12),
        PROFILE_PICKER_MINUTE_KEY: draft.get("birth_minute", 0),
        PROFILE_PICKER_PRECISION_KEY: draft.get("time_precision", "精确时间"),
        PROFILE_PICKER_TRADITIONAL_KEY: draft.get("traditional_time") or "巳时",
        PROFILE_PICKER_LEAP_KEY: bool(draft.get("is_leap_month", False)),
    }


def open_birth_picker(state, draft: Mapping[str, Any]) -> None:
    seed = _picker_seed(draft)
    # The component is not mounted while the sheet is closed, so its previous
    # selection can be safely discarded before seeding a new picker session.
    state.pop(BIRTH_WHEEL_COMPONENT_KEY, None)
    state[PROFILE_PICKER_SNAPSHOT_KEY] = dict(seed)
    state.update(seed)
    state[PROFILE_PICKER_OPEN_KEY] = True
    touch_private_session(state)


def cancel_birth_picker(state) -> None:
    snapshot = state.get(PROFILE_PICKER_SNAPSHOT_KEY) or {}
    for key in PROFILE_PICKER_KEYS:
        if key in snapshot:
            state[key] = snapshot[key]
        else:
            state.pop(key, None)
    state[PROFILE_PICKER_OPEN_KEY] = False
    state.pop(PROFILE_PICKER_SNAPSHOT_KEY, None)


def complete_birth_picker(state, draft: dict) -> None:
    calendar_label = state[PROFILE_PICKER_CALENDAR_KEY]
    year = int(state[PROFILE_PICKER_YEAR_KEY])
    month = int(state[PROFILE_PICKER_MONTH_KEY])
    day = int(state[PROFILE_PICKER_DAY_KEY])
    if calendar_label == "公历" and day not in valid_solar_days(year, month):
        raise ValueError("所选公历日期无效，请重新选择。")
    is_leap_month = bool(state[PROFILE_PICKER_LEAP_KEY] and calendar_label == "农历")
    if calendar_label == "农历" and day not in lunar_month_days(year, month, is_leap_month=is_leap_month):
        raise ValueError("所选农历日期或闰月无效，请重新选择。")
    precision = state[PROFILE_PICKER_PRECISION_KEY]
    if precision == "传统时辰":
        hour, minute, time_label = traditional_time(state[PROFILE_PICKER_TRADITIONAL_KEY])
    elif precision == "时辰不详":
        hour, minute, time_label = None, None, precision
    else:
        hour = int(state[PROFILE_PICKER_HOUR_KEY])
        minute = int(state[PROFILE_PICKER_MINUTE_KEY])
        time_label = precision
    draft.update(
        {
            "calendar_label": calendar_label,
            "birth_date": date(year, month, day) if calendar_label == "公历" else draft.get("birth_date", date(1990, 1, 1)),
            "lunar_year": year if calendar_label == "农历" else None,
            "lunar_month": month if calendar_label == "农历" else None,
            "lunar_day": day if calendar_label == "农历" else None,
            "birth_hour": hour,
            "birth_minute": minute,
            "is_leap_month": is_leap_month,
            "time_precision": precision,
            "traditional_time": time_label if precision == "传统时辰" else None,
            "time_known": precision != "时辰不详",
        }
    )
    state[PROFILE_PICKER_OPEN_KEY] = False
    state.pop(PROFILE_PICKER_SNAPSHOT_KEY, None)
    touch_private_session(state)


def sync_birth_wheel_selection(
    state,
    raw_selection: Any,
    columns: list[Mapping[str, Any]],
    *,
    precision: str,
) -> bool:
    """Copy a fully whitelisted component selection into canonical picker state."""
    selection = validate_wheel_selection(raw_selection, columns)
    if selection is None:
        return False
    updates = {
        PROFILE_PICKER_YEAR_KEY: selection["year"],
        PROFILE_PICKER_MONTH_KEY: selection["month"],
        PROFILE_PICKER_DAY_KEY: selection["day"],
    }
    if precision == "传统时辰":
        updates[PROFILE_PICKER_TRADITIONAL_KEY] = selection["hour"]
    elif precision == "精确时间":
        updates[PROFILE_PICKER_HOUR_KEY] = selection["hour"]
        updates[PROFILE_PICKER_MINUTE_KEY] = selection["minute"]
    changed = any(state.get(key) != value for key, value in updates.items())
    if changed:
        state.update(updates)
        touch_private_session(state)
    return changed


def sync_birth_wheel_component_state(
    state,
    columns: list[Mapping[str, Any]],
    *,
    precision: str,
) -> bool:
    """Synchronize v2 state in its pre-rerun callback, avoiding a stale frame."""
    if is_public_mode() and maintain_private_session(state):
        return False
    component_state = state.get(BIRTH_WHEEL_COMPONENT_KEY)
    raw_selection = component_state.get("selection") if isinstance(component_state, Mapping) else None
    return sync_birth_wheel_selection(
        state,
        raw_selection,
        columns,
        precision=precision,
    )


def _render_birth_picker(st, draft: dict) -> bool:
    """Render an operable date/time sheet; return whether it remains open."""
    if not st.session_state.get(PROFILE_PICKER_OPEN_KEY):
        return False

    with st.container(key="ms5-birth-picker", border=True):
        st.markdown('<div class="ms5-picker-backdrop" aria-hidden="true"></div>', unsafe_allow_html=True)
        # The simplified picker always accepts an explicit clock time. Legacy
        # unknown/traditional values remain intact unless the user completes
        # this sheet; opening then cancelling restores the original snapshot.
        time_precision = "精确时间"
        st.session_state[PROFILE_PICKER_PRECISION_KEY] = time_precision
        if not isinstance(st.session_state.get(PROFILE_PICKER_HOUR_KEY), int):
            st.session_state[PROFILE_PICKER_HOUR_KEY] = 12
        if not isinstance(st.session_state.get(PROFILE_PICKER_MINUTE_KEY), int):
            st.session_state[PROFILE_PICKER_MINUTE_KEY] = 0

        with st.container(key="ms5-picker-toolbar"):
            header = st.columns(3)
            with header[0]:
                st.button(
                    "取消",
                    key="profile_picker_cancel",
                    on_click=cancel_birth_picker,
                    args=(st.session_state,),
                )
            with header[1]:
                calendar_label = st.radio(
                    "历法",
                    ["公历", "农历"],
                    key=PROFILE_PICKER_CALENDAR_KEY,
                    horizontal=True,
                    label_visibility="collapsed",
                    on_change=touch_private_session,
                    args=(st.session_state,),
                )
            with header[2]:
                done_clicked = st.button("完成", key="profile_picker_done", type="primary")
        if done_clicked:
            try:
                complete_birth_picker(st.session_state, draft)
            except ValueError as exc:
                st.error(str(exc))
            else:
                _clear_birth_preview(st.session_state)
                st.rerun()
                return False

        st.markdown(
            '<p class="ms5-picker-hint">出生时间不详时，可使用默认 12:00；这会影响时柱与时间相关结论。</p>',
            unsafe_allow_html=True,
        )
        current = date.today()
        years = list(range(1900, current.year + 1))
        if st.session_state.get(PROFILE_PICKER_YEAR_KEY) not in years:
            st.session_state[PROFILE_PICKER_YEAR_KEY] = 1990
        year = st.session_state[PROFILE_PICKER_YEAR_KEY]
        months = list(range(1, 13 if calendar_label == "农历" or year < current.year else current.month + 1))
        if st.session_state.get(PROFILE_PICKER_MONTH_KEY) not in months:
            st.session_state[PROFILE_PICKER_MONTH_KEY] = months[-1]
        month = st.session_state[PROFILE_PICKER_MONTH_KEY]
        leap_month = LunarYear.fromYear(year).getLeapMonth() if calendar_label == "农历" else 0
        if calendar_label != "农历" or month != leap_month:
            st.session_state[PROFILE_PICKER_LEAP_KEY] = False
        is_leap_month = bool(st.session_state.get(PROFILE_PICKER_LEAP_KEY))
        days = lunar_month_days(year, month, is_leap_month=is_leap_month) if calendar_label == "农历" else valid_solar_days(year, month)
        if st.session_state.get(PROFILE_PICKER_DAY_KEY) not in days:
            st.session_state[PROFILE_PICKER_DAY_KEY] = days[-1]
        hour_values, minute_values = list(range(24)), list(range(60))
        selected_hour = st.session_state.get(PROFILE_PICKER_HOUR_KEY, 12)
        selected_minute = st.session_state.get(PROFILE_PICKER_MINUTE_KEY, 0)
        wheel_columns = [
            wheel_column("year", "年", years, year, lambda value: f"{value}年"),
            wheel_column(
                "month",
                "月",
                months,
                month,
                (lambda value: f"{CHINESE_MONTHS[value - 1]}月")
                if calendar_label == "农历"
                else (lambda value: f"{value}月"),
            ),
            wheel_column(
                "day",
                "日",
                days,
                st.session_state[PROFILE_PICKER_DAY_KEY],
                (lambda value: CHINESE_DAYS[value - 1])
                if calendar_label == "农历"
                else (lambda value: f"{value}日"),
            ),
            wheel_column(
                "hour",
                "时",
                hour_values,
                selected_hour,
                lambda value: f"{value:02d}时",
            ),
            wheel_column(
                "minute",
                "分",
                minute_values,
                selected_minute,
                lambda value: "不详" if value is None else f"{value:02d}分",
            ),
        ]
        wheel_selection = render_birth_wheel(
            wheel_columns,
            on_change=partial(
                sync_birth_wheel_component_state,
                st.session_state,
                wheel_columns,
                precision=time_precision,
            ),
        )
        if wheel_selection is not None:
            sync_birth_wheel_selection(
                st.session_state,
                wheel_selection,
                wheel_columns,
                precision=time_precision,
            )
        if calendar_label == "农历" and month == leap_month:
            st.checkbox("闰月", key=PROFILE_PICKER_LEAP_KEY, on_change=touch_private_session, args=(st.session_state,))
    return True


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


def _render_birth_preview_summary(st, preview: Mapping[str, Any]) -> None:
    """Render a compact escaped receipt without changing confirmation semantics."""
    pillars = " / ".join(str(item) for item in preview.get("pillars", []))
    rows = (
        ("输入资料", preview.get("input_text", "")),
        ("标准时间", f'中国标准时间 {preview.get("solar_datetime", "")}'),
        ("四柱", pillars),
        ("计算依据", preview.get("calculation_basis", "")),
    )
    rows_html = "".join(
        '<div class="ms5-preview-row">'
        f'<span>{escape(label)}</span><strong>{escape(str(value))}</strong>'
        "</div>"
        for label, value in rows
    )
    st.markdown(
        '<section class="ms5-preview-summary" aria-label="排盘预览摘要">'
        '<h3>请核对排盘预览</h3>'
        f"{rows_html}</section>",
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


def _committed_birth_values(draft: Mapping[str, Any]) -> tuple[str, int, int, int, int | None, int | None, bool, str, str]:
    seed = _picker_seed(draft)
    calendar_label = str(seed[PROFILE_PICKER_CALENDAR_KEY])
    year = int(seed[PROFILE_PICKER_YEAR_KEY])
    month = int(seed[PROFILE_PICKER_MONTH_KEY])
    day = int(seed[PROFILE_PICKER_DAY_KEY])
    precision = str(seed[PROFILE_PICKER_PRECISION_KEY])
    if precision == "传统时辰":
        hour, minute, time_label = traditional_time(str(seed[PROFILE_PICKER_TRADITIONAL_KEY]))
    elif precision == "时辰不详":
        hour, minute, time_label = None, None, precision
    else:
        hour = 12 if seed[PROFILE_PICKER_HOUR_KEY] is None else int(seed[PROFILE_PICKER_HOUR_KEY])
        minute = int(seed[PROFILE_PICKER_MINUTE_KEY] or 0)
        time_label = precision
    return calendar_label, year, month, day, hour, minute, bool(seed[PROFILE_PICKER_LEAP_KEY] and calendar_label == "农历"), precision, time_label


def _birth_summary(draft: Mapping[str, Any]) -> str:
    calendar_label, year, month, day, hour, minute, is_leap, precision, _ = _committed_birth_values(draft)
    date_text = f"{year}年{month}月{day}日"
    if calendar_label == "农历":
        date_text = f"{year}年{CHINESE_MONTHS[month - 1]}月{CHINESE_DAYS[day - 1]}"
    time_text = "时辰不详" if precision == "时辰不详" else f"{int(hour):02d}:{int(minute):02d}"
    leap_text = " · 闰月" if is_leap else ""
    return f"出生时间　{calendar_label} · {date_text}{leap_text} · {time_text}　›"


def _render_unified_profile_form(draft: dict, *, compact: bool = False) -> None:
    """在一个表单中收集资料，经预览确认后生成命盘。"""
    import streamlit as st

    with st.container(key="ms5-profile-card", border=True):
        if not compact:
            st.caption("排盘统一采用中国标准时间（北京时间）。")
        st.session_state[PROFILE_DRAFT_KEY] = draft
        if not compact:
            _render_profile_step_indicator(
                st,
                preview_ready=bool(st.session_state.get(PROFILE_PREVIEW_KEY)),
            )

        name_label = "昵称（可选）" if compact or is_public_mode() else "姓名"
        name = st.text_input(
            name_label,
            value=draft.get("name", ""),
            key=PROFILE_NAME_INPUT_KEY,
            on_change=touch_private_session,
            args=(st.session_state,),
        )
        relationship = st.selectbox(
            "关系",
            ["本人", "伴侣", "家人", "朋友"],
            index=["本人", "伴侣", "家人", "朋友"].index(draft.get("relationship", "本人")) if draft.get("relationship", "本人") in {"本人", "伴侣", "家人", "朋友"} else 0,
            key=PROFILE_RELATIONSHIP_INPUT_KEY,
            on_change=touch_private_session,
            args=(st.session_state,),
        )
        gender = st.radio(
            "性别",
            ["男", "女"],
            index=0 if draft.get("gender", "男") == "男" else 1,
            horizontal=True,
            key=PROFILE_GENDER_INPUT_KEY,
            on_change=touch_private_session,
            args=(st.session_state,),
        )
        if st.button(_birth_summary(draft), key="profile_birth_summary", use_container_width=True):
            open_birth_picker(st.session_state, draft)
        birth_place = st.text_input(
            "出生地点",
            value=draft.get("birth_place", ""),
            placeholder="可为空，如 北京、上海、广州",
            key=PROFILE_PLACE_INPUT_KEY,
            on_change=touch_private_session,
            args=(st.session_state,),
        )
        if compact:
            st.caption("排盘统一采用中国标准时间（北京时间）。")

        privacy_consent = True
        if is_public_mode():
            st.caption(PUBLIC_PRIVACY_NOTICE)
            privacy_consent = st.checkbox("我已阅读并同意本次会话隐私说明")
        else:
            st.caption("出生资料只用于本地排盘；公共每日建议不读取这些资料。")

        _render_birth_picker(st, draft)
        (
            calendar_label,
            input_year,
            input_month,
            input_day,
            birth_hour,
            birth_minute,
            is_leap_month,
            time_precision,
            time_label,
        ) = _committed_birth_values(draft)

        with st.form("unified_profile_form"):
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
            preview_submitted = False
            confirm_submitted = False
            if saved_preview:
                _render_birth_preview_summary(st, saved_preview)
                confirm_submitted = st.form_submit_button(
                    "确认生成命盘", type="primary", use_container_width=True
                )
            else:
                preview_submitted = st.form_submit_button(
                    "校验并预览", type="primary", use_container_width=True
                )

        if preview_submitted:
            if is_public_mode() and not privacy_consent:
                st.error("请先阅读并同意本次会话隐私说明。")
                return
            touch_private_session(st.session_state)
            draft.update(
                {
                    "name": name,
                    "relationship": relationship,
                    "gender": gender,
                    "calendar_label": calendar_label,
                    "birth_date": draft.get("birth_date", date(1990, 1, 1)),
                    "lunar_year": draft.get("lunar_year"),
                    "lunar_month": draft.get("lunar_month"),
                    "lunar_day": draft.get("lunar_day"),
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
        profile["relationship"] = relationship
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
        return_target = st.session_state.pop(PROFILE_SUCCESS_RETURN_KEY, "个人命盘")
        st.session_state["navigate_to"] = (
            return_target if return_target in {"个人命盘", "设置/档案"} else "个人命盘"
        )
        st.rerun()


def render_profile_form(*, show_header: bool = True, compact: bool = False) -> None:
    """渲染带有校验预览的一页式新建命盘表单。"""
    import streamlit as st

    if show_header:
        page_header(
            "新建命盘",
            "一次填写完整资料，校验预览无误后生成个人命盘。",
            eyebrow="CREATE CHART",
        )
    draft = st.session_state.setdefault(PROFILE_DRAFT_KEY, {})
    _render_unified_profile_form(draft, compact=compact)
