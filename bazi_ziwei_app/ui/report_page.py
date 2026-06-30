"""报告导出页面。"""

from __future__ import annotations

from datetime import date
from html import escape

from core.luck_engine import get_luck_cycles
from core.monthly_engine import analyze_monthly_fortune
from core.yearly_engine import analyze_yearly_fortune
from report.export_report import build_markdown_report, build_pdf_report, build_text_report


def _safe_filename(name: str, suffix: str) -> str:
    """生成安全文件名。"""
    clean_name = "".join(ch for ch in name if ch not in r'\/:*?"<>|').strip() or "未命名"
    return f"命数研究室_{clean_name}_八字报告.{suffix}"


def _build_report_preview_cards(markdown: str) -> list[dict]:
    """把完整 Markdown 报告拆成适合逐张阅读的名片。"""
    cards: list[dict] = []
    current_title = ""
    current_lines: list[str] = []
    for raw_line in (markdown or "").splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if current_title:
                content = "\n".join(current_lines).strip()
                cards.append({"title": current_title, "content": content or "本节暂无详细内容。"})
            current_title = line.replace("## ", "", 1).strip()
            current_lines = []
            continue
        if current_title:
            current_lines.append(raw_line)
    if current_title:
        content = "\n".join(current_lines).strip()
        cards.append({"title": current_title, "content": content or "本节暂无详细内容。"})
    return cards


def _preview_content_html(content: str) -> str:
    """把 Markdown 内容转成名片内的安全预览文本。"""
    lines = []
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("<br>")
            continue
        if line.startswith("- "):
            line = "• " + line[2:]
        elif line.startswith("* "):
            line = "  · " + line[2:]
        lines.append(escape(line))
    return "<br>".join(lines)


def _render_report_card(card: dict, index: int, total: int) -> None:
    """渲染单张报告名片。"""
    import streamlit as st

    title = escape(card.get("title", "报告内容"))
    content_html = _preview_content_html(card.get("content", ""))
    st.markdown(
        f"""
        <div style="background:#FAF7F4;border:1px solid #D4C5B0;border-radius:14px;
            padding:20px 22px;margin:12px 0 10px 0;box-shadow:0 3px 10px rgba(61,43,26,0.08);">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;">
            <div>
              <div style="font-size:12px;color:#8C7A64;margin-bottom:3px;">报告名片</div>
              <div style="font-size:22px;font-weight:800;color:#3D2B1A;">{title}</div>
            </div>
            <div style="font-size:13px;color:#8C7A64;white-space:nowrap;">第 {index + 1} / {total} 张</div>
          </div>
          <div style="background:#FFFDF8;border-radius:10px;border:1px solid #EDE6DC;
              padding:14px 16px;max-height:520px;overflow-y:auto;
              font-size:14px;color:#3D2B1A;line-height:1.85;">
            {content_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_report_card_carousel(markdown: str) -> None:
    """渲染报告名片轮播。"""
    import streamlit as st

    cards = _build_report_preview_cards(markdown)
    if not cards:
        st.info("报告预览暂不可用。")
        return

    key = "report_card_index"
    st.session_state[key] = int(st.session_state.get(key, 0)) % len(cards)
    index = st.session_state[key]
    _render_report_card(cards[index], index, len(cards))

    col_prev, col_mid, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← 上一张", use_container_width=True):
            st.session_state[key] = (index - 1) % len(cards)
            st.rerun()
    with col_mid:
        st.markdown(
            f'<div style="text-align:center;color:#8C7A64;font-size:13px;padding-top:8px;">'
            f'当前：{escape(cards[index].get("title", ""))}</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("下一张 →", use_container_width=True):
            st.session_state[key] = (index + 1) % len(cards)
            st.rerun()


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

    st.markdown("### 报告名片预览")
    st.caption("每一张名片对应完整报告中的一个章节。下方按钮只切换预览名片，下载文件仍包含完整报告。")
    _render_report_card_carousel(markdown)

    with st.expander("查看原始 Markdown 文本"):
        st.text_area("原始 Markdown", markdown, height=360)
