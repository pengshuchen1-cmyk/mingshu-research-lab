"""数据备份页面。"""

from __future__ import annotations

from utils.backup import backup_database, export_profiles_to_json, import_profiles_from_json


def render_backup_page() -> None:
    """
    渲染数据备份页面。
    """
    import streamlit as st

    st.title("数据备份")
    st.markdown(
        f'<div style="background:#FAF7F4;border-radius:10px;padding:20px 24px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);">',
        unsafe_allow_html=True,
    )
    st.warning("导出文件包含出生信息和命盘报告，请自行妥善保存，避免泄露个人隐私。")

    payload = export_profiles_to_json()
    st.download_button("导出所有命盘 JSON", payload, "命数研究室_命盘备份.json", "application/json")

    if st.button("备份 SQLite 数据库"):
        result = backup_database()
        if result.get("ok"):
            st.success(f"数据库已备份：{result.get('path')}")
        else:
            st.error(result.get("message", "数据库备份失败。"))

    st.markdown("### 从 JSON 导入命盘")
    uploaded = st.file_uploader("选择 JSON 备份文件", type=["json"])
    confirm = st.checkbox("我确认导入会新增命盘记录")
    if uploaded and st.button("开始导入", disabled=not confirm):
        text = uploaded.read().decode("utf-8")
        result = import_profiles_from_json(text)
        if result.get("error"):
            st.error(result["error"])
        else:
            st.success(f"已导入 {result.get('imported', 0)} 条命盘。")
        st.markdown("</div>", unsafe_allow_html=True)
