"""合婚匹配专项报告 — v1.3-A"""

from __future__ import annotations

from io import BytesIO


def build_compatibility_markdown(result: dict, name1: str, name2: str) -> str:
    """生成合婚匹配 Markdown 报告。"""
    dims = result.get("dimensions", [])
    cautions = result.get("key_cautions", [])
    sources = result.get("source_titles", [])

    lines = [
        "# 合婚匹配报告",
        "",
        f"**甲方**：{name1}　**乙方**：{name2}",
        "",
        "## 综合评分",
        f"总分：{result['overall_score']}/100　等级：{result['level']}",
        f"评语：{result['summary']}",
        "",
    ]
    if cautions:
        lines.append("## 重点提醒")
        for c in cautions:
            lines.append(f"- ⚠ {c}")
        lines.append("")

    lines.append("## 各维度评分")
    for d in dims:
        pct = int(d["score"] / d["max_score"] * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"**{d['label']}**：{d['score']}/{d['max_score']} {bar}")
        lines.append(f"> {d['text']}")
        if d.get("detail"):
            lines.append(f"  *{d['detail']}*")
        lines.append("")

    lines.append("## 命理依据")
    lines.append(result.get("basis", ""))
    if sources:
        lines.append(f"参考来源：{'、'.join(sources)}")
    lines.append("")
    lines.append("---")
    lines.append("本报告基于传统命理模型生成，仅供个人兴趣和文化研究参考，不应作为重大决策的唯一依据。")
    return "\n".join(lines)


def build_compatibility_pdf(result: dict, name1: str, name2: str) -> bytes:
    """生成合婚匹配 PDF 报告。"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return "PDF 导出暂不可用（缺少 reportlab），请先使用 Markdown 或 TXT。".encode("utf-8")

    try:
        markdown = build_compatibility_markdown(result, name1, name2)
        font_name = None
        for fn, fp in [("DroidSansFallback", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
                       ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                       ("NotoSerifCJK", "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"),
                       ("ArialUnicode", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
                       ("Songti", "/System/Library/Fonts/Supplemental/Songti.ttc"),
                       ("PingFang", "/System/Library/Fonts/PingFang.ttc"),
                       ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc"),
                       ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
                       ("SimHei", "C:/Windows/Fonts/simhei.ttf")]:
            try:
                pdfmetrics.registerFont(TTFont(fn, fp))
                font_name = fn; break
            except Exception:
                continue
        if not font_name:
            return "PDF 字体暂不可用，请使用 Markdown/TXT 导出。".encode("utf-8")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = {"base": ParagraphStyle("B", fontName=font_name, fontSize=10.5, leading=16, spaceAfter=6),
                  "title": ParagraphStyle("T", fontName=font_name, fontSize=18, leading=24, spaceAfter=12),
                  "heading": ParagraphStyle("H", fontName=font_name, fontSize=13, leading=18, spaceBefore=8, spaceAfter=6)}
        story = []
        for line in markdown.splitlines():
            s = line.strip()
            if not s: story.append(Spacer(1, 6))
            elif s.startswith("# "): story.append(Paragraph(s[2:], styles["title"]))
            elif s.startswith("## "): story.append(Paragraph(s[3:], styles["heading"]))
            else: story.append(Paragraph(s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"), styles["base"]))
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return "PDF 生成失败，请使用 Markdown/TXT 导出。".encode("utf-8")


def build_compatibility_text(result: dict, name1: str, name2: str) -> str:
    """生成纯文本报告。"""
    md = build_compatibility_markdown(result, name1, name2)
    return md.replace("# ", "").replace("## ", "").replace("**", "")
