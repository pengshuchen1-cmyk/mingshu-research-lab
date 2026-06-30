"""专项报告页面。"""

from __future__ import annotations

from report.career_report import generate_career_report
from report.export_report import build_special_pdf_report, build_special_text_report
from report.love_report import generate_love_report
from report.special_report_common import build_special_markdown
from report.wealth_report import generate_wealth_report
from ui.bazi_components import render_loaded_profile_hint


def _safe_filename(name: str, report_type: str, suffix: str) -> str:
    """生成安全文件名。"""
    clean_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip() or "未命名"
    return f"命数研究室_{clean_name}_{report_type}.{suffix}"


def render_special_reports_page() -> None:
    """
    渲染事业、财运、婚恋专项报告。
    """
    import streamlit as st

    st.title("专项报告")
    chart = st.session_state.get("current_chart")
    profile = st.session_state.get("current_profile", {})
    if not chart:
        st.info("请先在新建命盘页面生成命盘，或从命盘档案中加载一个命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    report_type = st.radio("选择报告类型", ["事业专项", "财运专项", "婚恋专项"], horizontal=True)
    render_loaded_profile_hint(profile, chart)
    if report_type == "事业专项":
        report = generate_career_report(chart)
    elif report_type == "财运专项":
        report = generate_wealth_report(chart)
    else:
        report = generate_love_report(chart, profile)

    markdown = build_special_markdown(report)
    text_report = build_special_text_report(report)
    pdf_report = build_special_pdf_report(report)
    name = profile.get("name", "未命名")

    st.caption(report.get("disclaimer", ""))
    for item in report.get("sections", []):
        with st.expander(item.get("title", ""), expanded=True):
            st.write(item.get("text", ""))

    col1, col2, col3 = st.columns(3)
    col1.download_button("下载 Markdown", markdown, _safe_filename(name, report_type, "md"), "text/markdown")
    col2.download_button("下载 TXT", text_report, _safe_filename(name, report_type, "txt"), "text/plain")
    col3.download_button("下载 PDF", pdf_report, _safe_filename(name, report_type, "pdf"), "application/pdf")
