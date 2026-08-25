"""命盘总体结论报告生成。"""

from __future__ import annotations

from ..analysis.life_overview_engine import analyze_life_overview
from ..fortune.chart_fingerprint import build_chart_fingerprint


def generate_life_overview_report(chart: dict, luck_data: dict | None = None) -> dict:
    """
    生成命盘总体结论报告（适合展示和导出）。

    包含：命盘总体类型、财富/感情/健康/事业总览、优势、隐患、长期建议、参考来源。
    """
    dp = analyze_life_overview(chart, luck_data)
    fp = build_chart_fingerprint(chart)
    scores = dp["scores"]

    sections = {}
    # 财富
    w = dp["wealth_overview"]
    sections["wealth"] = {
        "title": "💰 财富格局",
        "level": w["wealth_level"],
        "type": w["wealth_type"],
        "score": w["wealth_score"],
        "summary": w["wealth_summary"],
        "details": {
            "收入模式": w["income_modes"],
            "财富机会": w["wealth_opportunities"],
            "财富风险": w["wealth_risks"],
            "财务管理建议": [w["money_management_advice"]],
        },
    }

    # 桃花感情
    r = dp["romance_overview"]
    sections["romance"] = {
        "title": "💞 桃花·感情",
        "level": r["romance_level"],
        "type": r["romance_type"],
        "score": r["romance_score"],
        "summary": r["romance_summary"],
        "details": {
            "吸引力特征": r["attraction_points"],
            "关系优势": r["relationship_strengths"],
            "关系风险": r["relationship_risks"],
            "适合伴侣类型": r["suitable_partner_type"],
            "沟通建议": [r["communication_advice"]],
        },
    }

    # 健康稳定度
    h = dp["health_overview"]
    sections["health"] = {
        "title": "🏥 健康·长寿",
        "level": h["health_stability_level"],
        "type": "五行调候参考",
        "score": h["health_score"],
        "summary": h["health_summary"],
        "details": {
            "敏感系统": h["sensitive_elements"],
            "身体倾向": h["body_system_tendencies"],
            "生活习惯风险": h["lifestyle_risks"],
            "长期养护建议": h["long_term_care_advice"],
        },
        "disclaimer": h["medical_disclaimer"],
    }

    # 事业发展
    c = dp["career_overview"]
    sections["career"] = {
        "title": "💼 事业发展",
        "level": c["career_type"].split(" · ")[0] if c["career_type"] else "稳定积累型",
        "type": c["career_type"],
        "score": c["career_score"],
        "summary": c["career_summary"],
        "details": {
            "发展路径": c["development_path"],
            "事业优势": c["career_strengths"],
            "事业风险": c["career_risks"],
            "长期建议": c["long_term_action_advice"],
        },
    }

    return {
        "title": "命盘总体结论",
        "overall_pattern": dp["overall_pattern"],
        "overall_summary": dp["overall_summary"],
        "life_keywords": dp["life_keywords"],
        "scores": scores,
        "sections": sections,
        "key_strengths": dp["key_strengths"],
        "key_risks": dp["key_risks"],
        "long_term_advice": dp["long_term_advice"],
        "evidence": dp["evidence"],
        "source_titles": dp["source_titles"],
    }
