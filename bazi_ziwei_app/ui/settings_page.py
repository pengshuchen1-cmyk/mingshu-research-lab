"""设置页面。"""

from __future__ import annotations


def render_settings_page() -> None:
    """
    渲染设置页面。
    """
    import streamlit as st

    st.markdown(
        '<div style="background:linear-gradient(135deg,#3D2B1A 0%,#5C4A32 100%);'
        'border-radius:16px;padding:24px 32px;margin-bottom:24px;'
        'box-shadow:0 4px 12px rgba(61,43,26,0.15);">'
        '<h1 style="color:#FCF8F0;font-size:28px;letter-spacing:3px;'
        'font-weight:700;margin:0 0 4px 0;">设置</h1>'
        '<p style="color:#D4C5B0;font-size:13px;margin:0;">'
        '应用偏好和默认行为配置</p></div>',
        unsafe_allow_html=True)
    st.markdown(
                    f'<div style="{card_style()}padding:20px 24px;margin-bottom:16px;">'
                    '<div style="font-weight:600;color:#3D2B1A;font-size:16px;margin-bottom:14px;">'
                    '⚙ 应用偏好</div>',
                    unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("设置保存在当前本机会话中，关闭浏览器后重置。")
