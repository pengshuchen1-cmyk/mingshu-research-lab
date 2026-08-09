"""公网版本的隐私说明与立即清除入口。"""

from __future__ import annotations

from utils.session_privacy import clear_private_session
from ui.primitives import callout, card, metric_card, page_header, section_header


def render_privacy_center_page() -> None:
    import streamlit as st

    page_header(
        "隐私与清除",
        "清楚了解资料如何使用，并随时结束本次会话中的数据保留。",
        eyebrow="PRIVACY",
    )
    with card("privacy-status", size="lg"):
        section_header("当前隐私状态")
        callout(
            "仅限本次会话",
            "个人资料仅用于本次会话计算；服务器档案保存、跨用户搜索与云同步均已关闭。",
            variant="muted",
        )
        callout(
            "AI 问答的数据边界",
            "出生资料和排盘计算保留在本次会话；AI 问答会把去身份化命盘事实、问题和近期对话发送给已配置的云端 AI 服务。不会发送姓名、精确出生日期、出生地点或 API Key。",
            variant="default",
        )
        left, middle, right = st.columns(3)
        with left:
            metric_card("资料范围", "仅本次会话")
        with middle:
            metric_card("服务器保存", "关闭")
        with right:
            metric_card("自动清除", "30 分钟")

    with card("privacy-control", size="lg", tone="muted"):
        section_header(
            "你可以控制自己的资料",
            "刷新、会话超时或主动清除后，需要重新输入出生资料。称呼可以不填，建议不要填写真实姓名。",
        )
        if st.button("立即清除我的资料", type="primary", use_container_width=True):
            clear_private_session(st.session_state)
            st.session_state["navigate_to"] = "首页"
            st.success("本次会话中的出生资料、命盘和报告已清除。")
            st.rerun()
