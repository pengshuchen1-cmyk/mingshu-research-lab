"""Mobile-first personal profile and privacy controls."""

from __future__ import annotations

from datetime import date
from html import escape

import streamlit as st

from ui.profile_form import (
    PROFILE_DRAFT_KEY,
    PROFILE_GENDER_INPUT_KEY,
    PROFILE_NAME_INPUT_KEY,
    PROFILE_PASTE_KEY,
    PROFILE_PLACE_INPUT_KEY,
    PROFILE_RELATIONSHIP_INPUT_KEY,
    PROFILE_SUCCESS_RETURN_KEY,
    parse_profile_paste,
    render_profile_form,
)
from ui.primitives import page_header
from utils.runtime_mode import is_public_mode
from utils.session_privacy import clear_private_session
from utils.session_privacy import touch_private_session


PROFILE_PASTE_RESULT_KEY = "profile_paste_result"


def _apply_profile_paste(state) -> None:
    """Parse and clear pasted PII during the button callback phase."""
    raw = str(state.get(PROFILE_PASTE_KEY) or "")
    try:
        recognized = parse_profile_paste(raw)
    except ValueError as exc:
        state[PROFILE_PASTE_RESULT_KEY] = ("error", str(exc))
    else:
        draft = state.setdefault(PROFILE_DRAFT_KEY, {})
        draft.update(recognized)
        widget_keys = {
            "name": PROFILE_NAME_INPUT_KEY,
            "relationship": PROFILE_RELATIONSHIP_INPUT_KEY,
            "gender": PROFILE_GENDER_INPUT_KEY,
            "birth_place": PROFILE_PLACE_INPUT_KEY,
        }
        for field, widget_key in widget_keys.items():
            if field in recognized:
                state[widget_key] = recognized[field]
        state[PROFILE_PASTE_RESULT_KEY] = ("success", tuple(recognized))
    state.pop(PROFILE_PASTE_KEY, None)
    touch_private_session(state)


def _birth_time(profile: dict) -> str:
    hour = profile.get("birth_hour")
    minute = profile.get("birth_minute")
    if hour is None or minute is None:
        return "时辰不详"
    return f"{int(hour):02d}:{int(minute):02d}"


def _profile_draft(profile: dict) -> dict:
    """Seed the canonical profile form without calculating chart facts here."""
    raw_date = profile.get("lunar_birth_date") or profile.get("birth_date")
    try:
        birth_date = date.fromisoformat(str(raw_date))
    except (TypeError, ValueError):
        birth_date = date(1990, 1, 1)
    calendar_type = profile.get("calendar_type")
    return {
        "name": str(profile.get("name") or ""),
        "relationship": str(profile.get("relationship") or "本人"),
        "gender": str(profile.get("gender") or "男"),
        "calendar_label": "农历" if calendar_type == "lunar" else "公历",
        "birth_date": birth_date,
        "lunar_year": birth_date.year,
        "lunar_month": birth_date.month,
        "lunar_day": birth_date.day,
        "birth_hour": profile.get("birth_hour"),
        "birth_minute": profile.get("birth_minute"),
        "birth_place": str(profile.get("birth_place") or ""),
        "is_leap_month": bool(profile.get("is_leap_month")),
        "time_precision": "时辰不详" if profile.get("birth_hour") is None else "精确时间",
        "time_known": profile.get("birth_hour") is not None,
    }


def _navigate(target: str) -> None:
    st.session_state["navigate_to"] = target
    st.rerun()


def render_my_page() -> None:
    """Render personal details or the canonical profile creation flow."""
    profile = st.session_state.get("current_profile")
    chart = st.session_state.get("current_chart")
    if not profile or not chart:
        st.session_state[PROFILE_SUCCESS_RETURN_KEY] = "设置/档案"
        st.markdown(
            '<div class="ms-my-add-bar"><strong>添加档案</strong></div>',
            unsafe_allow_html=True,
        )
        pasted = st.text_area(
            "粘贴并识别（可选）",
            key=PROFILE_PASTE_KEY,
            placeholder="例如：昵称：小青，本人，性别女，1990年2月3日 08:30，出生于北京",
            help="仅识别明确字段；原文不会写入日志，解析后立即从会话状态移除。",
            on_change=touch_private_session,
            args=(st.session_state,),
        )
        st.button(
            "识别并填入",
            use_container_width=True,
            on_click=_apply_profile_paste,
            args=(st.session_state,),
        )
        paste_result = st.session_state.pop(PROFILE_PASTE_RESULT_KEY, None)
        if paste_result:
            kind, payload = paste_result
            if kind == "error":
                st.error(str(payload))
            else:
                recognized_labels = {
                    "name": "昵称", "relationship": "关系", "gender": "性别",
                    "calendar_label": "历法", "birth_date": "出生日期",
                    "birth_hour": "小时", "birth_minute": "分钟",
                    "time_precision": "时间精度", "time_known": "时间状态",
                    "birth_place": "出生地点",
                }
                st.success("已识别并填入：" + "、".join(recognized_labels[key] for key in payload))
        render_profile_form(show_header=False, compact=True)
        if not is_public_mode() and st.button("加载本地档案", use_container_width=True):
            _navigate("命盘档案")
        return

    page_header("我的", "查看当前资料、隐私状态与档案操作。", eyebrow="PROFILE")
    report = st.session_state.get("current_report") or {}
    summary = report.get("summary") if isinstance(report, dict) else str(report)
    if not summary:
        summary = f"当前命盘日主为{chart.get('day_master') or '待确认'}，可从今日、命盘与报告继续查看。"
    privacy_label = "仅本次会话" if is_public_mode() else "当前会话（本机模式）"
    name = str(profile.get("name") or "未命名")
    birth_date = str(profile.get("birth_date") or profile.get("lunar_birth_date") or "未填写")
    calendar_label = "农历" if profile.get("calendar_type") == "lunar" else "公历"
    relationship = str(profile.get("relationship") or "本人")

    st.markdown(
        '<section class="ms-my-summary" aria-labelledby="ms-my-name">'
        '<p class="ms-my-eyebrow">当前资料</p>'
        f'<h2 id="ms-my-name">{escape(name)}</h2>'
        f'<p>{escape(str(summary))}</p>'
        '</section>'
        '<section class="ms-my-facts" aria-label="出生资料摘要">'
        f'<div><span>出生信息</span><strong>{escape(calendar_label)} · {escape(birth_date)} · {escape(_birth_time(profile))}</strong></div>'
        f'<div><span>关系</span><strong>{escape(relationship)}</strong></div>'
        '<div><span>时间标准</span><strong>中国标准时间（北京时间）</strong></div>'
        f'<div><span>隐私状态</span><strong>{escape(privacy_label)}</strong></div>'
        '</section>',
        unsafe_allow_html=True,
    )

    action_a, action_b = st.columns(2)
    if action_a.button("编辑资料", use_container_width=True):
        st.session_state[PROFILE_DRAFT_KEY] = _profile_draft(profile)
        st.session_state[PROFILE_SUCCESS_RETURN_KEY] = "设置/档案"
        _navigate("新建命盘")
    if action_b.button("新建命盘", type="primary", use_container_width=True):
        st.session_state.pop(PROFILE_DRAFT_KEY, None)
        st.session_state[PROFILE_SUCCESS_RETURN_KEY] = "设置/档案"
        _navigate("新建命盘")

    if not is_public_mode() and st.button("打开本地命盘档案", use_container_width=True):
        _navigate("命盘档案")

    st.caption(
        "公网模式只清除当前会话；本地模式清除当前载入资料，不会删除本机档案。"
        if not is_public_mode()
        else "清除后，本次会话中的出生资料、命盘、报告与问答上下文都会移除。"
    )
    if st.button("清除当前资料", use_container_width=True):
        clear_private_session(st.session_state)
        st.session_state["navigate_to"] = "设置/档案"
        st.success("当前会话资料已清除。")
        st.rerun()
