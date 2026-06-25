"""设置页面。"""

from __future__ import annotations


def render_settings_page() -> None:
    """
    渲染设置页面。
    """
    import streamlit as st

    st.title("设置")
    settings = st.session_state.setdefault(
        "app_settings",
        {
            "report_length": "标准版",
            "show_technical_details": False,
            "show_disclaimer": True,
            "default_export_format": "Markdown",
            "enable_quality_check": True,
        },
    )
    settings["report_length"] = st.selectbox("报告长度", ["简洁版", "标准版", "详细版"], index=["简洁版", "标准版", "详细版"].index(settings["report_length"]))
    settings["show_technical_details"] = st.checkbox("显示技术细节", value=settings["show_technical_details"])
    settings["show_disclaimer"] = st.checkbox("默认显示免责声明", value=settings["show_disclaimer"])
    settings["default_export_format"] = st.selectbox("默认导出格式", ["Markdown", "TXT", "PDF"], index=["Markdown", "TXT", "PDF"].index(settings["default_export_format"]))
    settings["enable_quality_check"] = st.checkbox("启用报告质量检查提示", value=settings["enable_quality_check"])
    st.success("设置已保存在当前本机会话中。")
