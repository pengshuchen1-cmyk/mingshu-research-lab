"""
紫微命盘名片报告生成 — v1.2-A
"""

from __future__ import annotations

from core.ziwei_life_card_engine import analyze_ziwei_life_card


def generate_ziwei_life_card_report(chart: dict) -> dict:
    """生成紫微命盘名片报告（适合展示和导出）。"""
    card = analyze_ziwei_life_card(chart)
    sections = []
    
    # 命宫分析
    sections.append({
        "title": "命宫分析",
        "text": card.get("ming_gong_summary", ""),
    })
    # 身宫分析
    sections.append({
        "title": "身宫分析",
        "text": card.get("shen_gong_summary", ""),
    })
    # 重点宫位摘要
    for name, summary in card.get("key_palace_summaries", {}).items():
        sections.append({
            "title": f"{name}摘要",
            "text": summary,
        })
    # 优势与风险
    strengths = card.get("strengths", [])
    risks = card.get("risks", [])
    if strengths:
        sections.append({"title": "命盘优势", "text": "\n".join(f"- {s}" for s in strengths)})
    if risks:
        sections.append({"title": "需关注的方向", "text": "\n".join(f"- {r}" for r in risks)})
    # 模块边界
    sections.append({
        "title": "模块完成度说明",
        "text": card.get("module_boundary", ""),
    })
    
    return {
        "title": "紫微命盘名片",
        "sections": sections,
        "advice": "\n".join(card.get("life_advice", [])),
        "source_titles": card.get("source_titles", []),
    }
