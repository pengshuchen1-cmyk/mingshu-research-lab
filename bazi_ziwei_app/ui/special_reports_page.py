"""专项报告页面。"""

from __future__ import annotations

from html import escape

from report.career_report import generate_career_report
from report.export_report import build_special_pdf_report, build_special_text_report
from report.love_report import generate_love_report
from report.special_report_common import build_special_markdown
from report.wealth_report import generate_wealth_report
from ui.bazi_components import render_loaded_profile_hint
from utils.runtime_mode import is_public_mode


def _safe_filename(name: str, report_type: str, suffix: str) -> str:
    """生成安全文件名。"""
    if is_public_mode():
        return f"命数研究室_个人报告.{suffix}"
    clean_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip() or "未命名"
    return f"命数研究室_{clean_name}_{report_type}.{suffix}"


def _section_text_html(text: str) -> str:
    """把专项报告正文转成名片里易读的 HTML。"""
    lines = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("<br>")
            continue
        if line.startswith("- "):
            line = "• " + line[2:]
        lines.append(escape(line))
    return "<br>".join(lines) or "本节暂无详细内容。"


def _render_special_report_card(card: dict, index: int, total: int) -> None:
    """渲染单张专项报告名片。"""
    import streamlit as st

    title = escape(card.get("title", "专项报告"))
    body = _section_text_html(card.get("text", ""))
    st.markdown(
        f"""
        <div class="mingshu-report-card">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;">
            <div>
              <div class="mingshu-report-eyebrow">专项报告名片</div>
              <div class="mingshu-report-title">{title}</div>
            </div>
            <div style="font-size:13px;color:var(--ms-muted-2);white-space:nowrap;">第 {index + 1} / {total} 张</div>
          </div>
          <div class="mingshu-report-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_special_report_card_carousel(report: dict, report_type: str) -> None:
    """专项报告名片轮播。"""
    import streamlit as st

    sections = report.get("sections", []) or []
    if not sections:
        st.info("当前专项报告暂无可预览内容。")
        return
    key = f"special_report_card_index_{report_type}"
    st.session_state[key] = int(st.session_state.get(key, 0)) % len(sections)
    index = st.session_state[key]
    _render_special_report_card(sections[index], index, len(sections))

    col_prev, col_mid, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← 上一张", key=f"special_prev_{report_type}", use_container_width=True):
            st.session_state[key] = (index - 1) % len(sections)
            st.rerun()
    with col_mid:
        st.markdown(
            f'<div style="text-align:center;color:var(--ms-muted-2);font-size:13px;padding-top:8px;">'
            f'当前：{escape(sections[index].get("title", ""))}</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("下一张 →", key=f"special_next_{report_type}", use_container_width=True):
            st.session_state[key] = (index + 1) % len(sections)
            st.rerun()


def render_special_reports_page() -> None:
    """
    渲染事业、财运、婚恋专项报告。
    """
    import streamlit as st

    chart = st.session_state.get("current_chart")
    profile = st.session_state.get("current_profile", {})
    if not chart:
        st.info("请先在新建命盘页面生成命盘，或从命盘档案中加载一个命盘。")
        return
    if chart.get("error"):
        st.error(chart["error"])
        return

    st.markdown(
        """
        <section class="v106c-page-hero">
          <div class="v106c-page-eyebrow">SPECIAL REPORT · v1.0.6</div>
          <div class="v106c-page-title">专项报告</div>
          <div class="v106c-page-subtitle">
            把事业、财运、婚恋拆成独立主题阅读。页面只展示关键信息，完整内容可按需导出。
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown(
        '<div class="mingshu-panel ms-report-panel">'
        '<div class="mingshu-report-eyebrow">SPECIAL REPORT</div>'
        f'<div class="mingshu-report-title">{escape(report_type)}</div>'
        '<div class="mingshu-muted">这里保留核心判断、现实解释和行动建议，先用名片阅读重点，再按需下载完整报告。</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(report.get("disclaimer", ""))
    _render_special_report_card_carousel(report, report_type)

    col1, col2, col3 = st.columns(3)
    col1.download_button("下载 Markdown", markdown, _safe_filename(name, report_type, "md"), "text/markdown")
    col2.download_button("下载 TXT", text_report, _safe_filename(name, report_type, "txt"), "text/plain")
    col3.download_button("下载 PDF", pdf_report, _safe_filename(name, report_type, "pdf"), "application/pdf")
