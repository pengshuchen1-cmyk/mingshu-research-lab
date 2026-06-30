"""
紫微命盘名片引擎 — v1.2-B0 (修复版)

基于 ziwei_fingerprint 生成差异化命盘名片。
明确区分「通用宫位说明」和「本命盘解读」。
不伪造未实现算法。
"""

from __future__ import annotations

import json

from core.ziwei_fingerprint import build_ziwei_fingerprint
from core.ziwei_constants import DETAILED_PALACE_EXPLANATIONS, PALACE_EXPLANATIONS


def _load_source_titles(source_ids):
    with open("rules/source_registry.json", "r", encoding="utf-8") as f:
        reg = json.load(f)
    return [reg[s]["title"] for s in source_ids if s in reg]


def analyze_ziwei_life_card(chart: dict) -> dict:
    """生成紫微命盘名片（基于fingerprint差异化）。"""
    fp = build_ziwei_fingerprint(chart)
    
    if not fp.get("available"):
        return {
            "title": "紫微命盘名片", "ziwei_profile_type": "暂不可用",
            "profile_keywords": [], "ming_gong_summary": "", "shen_gong_summary": "",
            "ming_shen_relation": "",
            "key_palace_summaries": {}, "personalized_evidence": [],
            "generic_palace_notes": [], "module_boundary": "紫微基础盘暂不可用。",
            "source_ids": [], "source_titles": [],
        }
    
    life_branch = fp["ming_gong_branch"]
    body_branch = fp["shen_gong_branch"]
    same_palace = fp["is_ming_shen_same_palace"]
    ms_relation = "命身同宫" if same_palace else f"命宫{life_branch}·身宫{body_branch}（分离）"
    
    profile_type = f"命宫{life_branch} · 身宫{body_branch}"
    if same_palace:
        profile_type += "【命身同宫】"
    
    # Personalized summaries
    ming_text = (
        f"命宫落在{life_branch}支。"
        + (PALACE_EXPLANATIONS.get("命宫", "") + "需要注意，命宫的地支位置会影响整体命盘布局。"
           if not DETAILED_PALACE_EXPLANATIONS.get("命宫", {}) else "")
    )
    shen_text = (
        f"身宫落在{body_branch}支。"
        + ("命身同宫，后天用力方向与先天性格高度一致。"
           if same_palace else
           f"命身分离，说明后天人生用力方向更容易集中在身宫所在的宫位主题上。"
           f"身宫所在的宫位是：{[p.get('name','') for p in chart.get('palaces',[]) if p.get('is_body_palace')]}")
    )
    if not same_palace:
        body_palace_name = ""
        for p in chart.get("palaces", []):
            if p.get("is_body_palace"):
                body_palace_name = p.get("name", "")
                break
        if body_palace_name and body_palace_name in PALACE_EXPLANATIONS:
            shen_text += f"身宫在{body_palace_name}，代表{body_palace_name}领域在人生中后期会更受重视。"
    
    # Key palace focus (personalized) + generic notes
    key_summaries = {}
    generic_notes = []
    focus_palaces = ["官禄宫", "财帛宫", "夫妻宫", "福德宫", "疾厄宫", "迁移宫"]
    palace_expl = DETAILED_PALACE_EXPLANATIONS if DETAILED_PALACE_EXPLANATIONS else {}
    
    for name in focus_palaces:
        fp_text = fp.get("key_palace_focus", {}).get(name, "")
        generic_expl = PALACE_EXPLANATIONS.get(name, "")
        
        if fp_text:
            key_summaries[name] = fp_text
        else:
            key_summaries[name] = f"{name}代表{generic_expl}。"
        
        generic_notes.append(f"【通用】{name}：{generic_expl}")
    
    # Evidence and keywords
    evidence = fp.get("evidence", [])
    keywords = fp.get("ziwei_profile_tags", [])
    
    # Generic palace notes (separated)
    source_ids = ["ziwei_doushu_quanshu", "traditional_ziwei_palace_system"]
    source_titles = _load_source_titles(source_ids)
    
    return {
        "title": "紫微命盘名片",
        "ziwei_profile_type": profile_type,
        "profile_keywords": keywords,
        "ming_gong_summary": ming_text,
        "shen_gong_summary": shen_text,
        "ming_shen_relation": ms_relation,
        "key_palace_summaries": key_summaries,
        "personalized_evidence": evidence,
        "generic_palace_notes": generic_notes,
        "star_info": chart.get("main_stars_by_palace", {}),
        "main_stars_ready": chart.get("main_stars_ready", False),
        "module_boundary": fp.get("module_boundary", "当前版本为紫微基础宫位分析版。"),
        "source_ids": source_ids,
        "source_titles": source_titles,
    }
