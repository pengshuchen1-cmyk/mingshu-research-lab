"""紫微主星落宫解释引擎。

只解释已经由紫微盘计算出的主星落宫，不新增飞化或流年算法。
"""

from __future__ import annotations

from .rule_engine import load_rules, match_rules
from .ziwei_constants import DETAILED_PALACE_EXPLANATIONS, DETAILED_STAR_EXPLANATIONS


def load_star_palace_rules() -> dict:
    """加载主星落宫规则。"""
    return load_rules("ziwei_star_palace_rules.json")


def _join(items: list[str]) -> str:
    return "、".join(items) if items else "暂无明显标记"


def _fallback_explanation(star: str, palace: str) -> dict:
    star_detail = DETAILED_STAR_EXPLANATIONS.get(star, {})
    palace_detail = DETAILED_PALACE_EXPLANATIONS.get(palace, {})
    palace_area = palace_detail.get("life_area", palace)
    star_keywords = star_detail.get("core_keywords", [])[:3]
    star_tendency = star_detail.get("personality_tendency", "")
    field_map = {
        "命宫": "personality_tendency",
        "官禄宫": "career_tendency",
        "财帛宫": "wealth_tendency",
        "夫妻宫": "relationship_tendency",
    }
    tendency = star_detail.get(field_map.get(palace, "personality_tendency"), star_tendency)
    text = f"{star}落在{palace}，可以把{star}的{_join(star_keywords)}特质放到{palace_area}里观察。"
    real_world = f"现实里更适合看{palace}对应领域中，是否表现出{tendency}。"
    return {
        "id": f"fallback_{star}_{palace}",
        "title": f"{star}入{palace}",
        "condition": {"star": star, "palace": palace},
        "text": text,
        "real_world_view": real_world,
        "strengths": palace_detail.get("positive_tendencies", [])[:2] or star_keywords[:2],
        "risks": palace_detail.get("risk_tendencies", [])[:2] or [star_detail.get("risk_tendency", "需要结合全盘观察")],
        "advice": star_detail.get("advice", "建议结合宫位、四化和八字一起参考。"),
        "boundary": "这是主星落宫的基础参考，未命中专项规则时不做过度延伸。",
        "source_ids": ["ziwei_doushu_quanshu", "traditional_ziwei_palace_system"],
    }


def explain_star_in_palace(star: str, palace: str, sihua: list[str] | None = None) -> dict:
    """解释一颗主星落入某个宫位的含义。"""
    sihua = sihua or []
    rules = load_star_palace_rules()
    matches = match_rules({"star": star, "palace": palace}, rules)
    rule = dict(matches[0]) if matches else _fallback_explanation(star, palace)
    matched_rule = bool(matches)

    sihua_text = (
        f"四化提示：本宫同时见{_join(sihua)}，可把相关领域作为阶段重点观察。"
        if sihua else "四化提示：本宫未见明显四化，先看长期模式。"
    )
    strengths = rule.get("strengths", [])
    risks = rule.get("risks", [])
    plain_text = (
        f"{rule.get('text', '')}"
        f"生活里怎么看：{rule.get('real_world_view', '')}"
        f"优势：{_join(strengths[:3])}。"
        f"风险：{_join(risks[:3])}。"
        f"建议：{rule.get('advice', '')}"
    )

    return {
        "star": star,
        "palace": palace,
        "title": rule.get("title", f"{star}入{palace}"),
        "matched_rule": matched_rule,
        "plain_text": plain_text,
        "real_world_view": rule.get("real_world_view", ""),
        "strengths": strengths,
        "risks": risks,
        "advice": rule.get("advice", ""),
        "boundary": rule.get("boundary", "此项仅供趋势参考。"),
        "sihua": sihua,
        "sihua_text": sihua_text,
        "source_ids": rule.get("source_ids", []),
    }


def build_star_palace_explanations(
    chart: dict,
    sihua_by_palace: dict | None = None,
    palace_names: list[str] | None = None,
) -> dict[str, list[dict]]:
    """按宫位生成主星落宫解释。"""
    sihua_by_palace = sihua_by_palace or {}
    palace_names = palace_names or ["命宫", "身宫", "官禄宫", "财帛宫", "夫妻宫"]
    main_stars_by_palace = chart.get("main_stars_by_palace", {})

    # 身宫对应实际宫位，外部仍可用“身宫”查。
    body_palace_name = ""
    for palace in chart.get("palaces", []):
        if palace.get("is_body_palace"):
            body_palace_name = palace.get("name", "")
            break

    result: dict[str, list[dict]] = {}
    for palace_name in palace_names:
        actual_name = body_palace_name if palace_name == "身宫" and body_palace_name else palace_name
        stars = main_stars_by_palace.get(actual_name, [])
        result[palace_name] = [
            explain_star_in_palace(star, actual_name, sihua_by_palace.get(actual_name, []))
            for star in stars
        ]
    return result
