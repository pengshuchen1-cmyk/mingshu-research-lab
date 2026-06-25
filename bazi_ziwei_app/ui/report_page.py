"""报告导出页面。"""

from __future__ import annotations

from datetime import date

from core.luck_engine import get_luck_cycles
from core.monthly_engine import analyze_monthly_fortune
from core.yearly_engine import analyze_yearly_fortune
from report.export_report import build_markdown_report, build_pdf_report, build_text_report


def _safe_filename(name: str, suffix: str) -> str:
    """生成安全文件名。"""
    clean_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip() or "未命名"
    return f"命数研究室_{clean_name}_八字报告.{suffix}"


def render_report_page() -> None:
    """
    渲染报告导出页面。
    """
    import streamlit as st

    st.title("报告导出")
    chart = st.session_state.get("current_chart")
    report = st.session_state.get("current_report")
    if not chart or not report:
        st.info("请先在新建命盘页面生成命盘，或从命盘档案中选择一个命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    profile = chart.get("profile") or st.session_state.get("current_profile", {})
    luck_data = st.session_state.get("current_luck_data")
    if not luck_data:
        luck_data = get_luck_cycles(profile, chart)
        st.session_state["current_luck_data"] = luck_data

    yearly_data = st.session_state.get("current_yearly_data")
    monthly_data = st.session_state.get("current_monthly_data")
    if not yearly_data:
        yearly_data = analyze_yearly_fortune(chart, date.today().year, luck_data)
        st.session_state["current_yearly_data"] = yearly_data
    if not monthly_data:
        monthly_data = analyze_monthly_fortune(chart, int(yearly_data.get("year", date.today().year)))
        st.session_state["current_monthly_data"] = monthly_data

    markdown = build_markdown_report(profile, chart, report, luck_data, yearly_data, monthly_data)
    text_report = build_text_report(profile, chart, report, luck_data, yearly_data, monthly_data)
    pdf_report = build_pdf_report(profile, chart, report, luck_data, yearly_data, monthly_data)
    name = profile.get("name", "未命名")

    st.markdown("### 当前命盘")
    st.write(f"姓名：{name}｜日主：{chart.get('day_master', '')}")
    st.caption("报告内容包含八字排盘、五行十神、日主强弱、喜用五行细化、基础分析、大运流年、年度运程、流月分析和免责声明。")
    if not pdf_report.startswith(b"%PDF"):
        st.info("当前环境 PDF 导出暂不可用，请先使用 Markdown 或 TXT 导出。也可以先运行：python -m pip install -r requirements.txt")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "下载 Markdown 报告",
            data=markdown,
            file_name=_safe_filename(name, "md"),
            mime="text/markdown",
        )
    with col2:
        st.download_button(
            "下载 TXT 报告",
            data=text_report,
            file_name=_safe_filename(name, "txt"),
            mime="text/plain",
        )
    with col3:
        st.download_button(
            "下载 PDF 报告",
            data=pdf_report,
            file_name=_safe_filename(name, "pdf"),
            mime="application/pdf",
        )

    st.markdown("### 报告预览")
    st.markdown(markdown)

    with st.expander("查看原始 Markdown 文本"):
        st.text_area("原始 Markdown", markdown, height=360)
