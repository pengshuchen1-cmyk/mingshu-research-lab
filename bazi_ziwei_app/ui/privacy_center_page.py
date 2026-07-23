"""公网版本的隐私说明与立即清除入口。"""

from __future__ import annotations

from utils.session_privacy import clear_private_session


def render_privacy_center_page() -> None:
    import streamlit as st

    st.title("隐私与清除")
    st.markdown("### 当前隐私状态")
    st.info("个人资料仅用于本次会话计算；服务器档案保存、跨用户搜索与云同步均已关闭。")
    st.info("出生资料和排盘计算保留在本次会话；AI 问答会把去身份化命盘事实、问题和近期对话发送给已配置的云端 AI 服务。不会发送姓名、精确出生日期、出生地点或 API Key。")
    left, middle, right = st.columns(3)
    left.metric("资料范围", "仅本次会话")
    middle.metric("服务器保存", "关闭")
    right.metric("自动清除", "30 分钟")
    st.markdown("### 你可以控制自己的资料")
    st.write("刷新、会话超时或主动清除后，需要重新输入出生资料。称呼可以不填，建议不要填写真实姓名。")
    if st.button("立即清除我的资料", type="primary", use_container_width=True):
        clear_private_session(st.session_state)
        st.session_state["navigate_to"] = "首页"
        st.success("本次会话中的出生资料、命盘和报告已清除。")
        st.rerun()
