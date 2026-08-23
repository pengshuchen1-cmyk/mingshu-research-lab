"""
三方四正基础结构 — v1.2-B2。

每个宫位的三方四正：
- 对宫：同宫位 + 6
- 三合：+4, +8 (或 -4, +4)
三合宫 = 命宫 +4, 命宫 +8 (顺时针)
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PALACE_INDEX: dict[str, int] = {
    "命宫": 0, "兄弟宫": 1, "夫妻宫": 2, "子女宫": 3,
    "财帛宫": 4, "疾厄宫": 5, "迁移宫": 6, "交友宫": 7,
    "官禄宫": 8, "田宅宫": 9, "福德宫": 10, "父母宫": 11,
}

INDEX_TO_PALACE: dict[int, str] = {v: k for k, v in PALACE_INDEX.items()}
PALACE_RULE_PATH = Path(__file__).resolve().parent / "rules" / "ziwei_palace_rules.json"
TRIANGLE_SOURCE_IDS = [
    "ziwei_doushu_quanshu",
    "ziwei_doushu_quanji",
    "ziwei_doushu_daquan",
    "traditional_ziwei_palace_system",
]


@lru_cache(maxsize=1)
def _load_palace_rules() -> dict[str, dict]:
    with PALACE_RULE_PATH.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    return {item.get("title", ""): item for item in payload.get("rules", [])}


def _palace_brief(palace_name: str) -> dict:
    rule = _load_palace_rules().get(palace_name, {})
    return {
        "palace": palace_name,
        "life_area": rule.get("life_area", "人生某一领域"),
        "positive_tendencies": rule.get("positive_tendencies", []),
        "risk_tendencies": rule.get("risk_tendencies", []),
        "advice": rule.get("advice", "建议结合命宫、三合宫和对宫综合观察。"),
        "basis": rule.get("basis", "基于传统紫微斗数十二宫体系。"),
        "source_ids": rule.get("source_ids", []),
    }


def _card(role: str, palace_name: str, stars: list[str], sihua: list[str] | None = None) -> dict:
    brief = _palace_brief(palace_name)
    star_text = "、".join(stars) if stars else "本宫未见十四主星，可借三方四正补充观察"
    sihua_text = "、".join(sihua or []) if sihua else "未见生年四化落入"
    return {
        "role": role,
        "palace": palace_name,
        "life_area": brief["life_area"],
        "main_stars": stars,
        "sihua": sihua or [],
        "plain_text": f"{palace_name}主看{brief['life_area']}。{role}在三方四正里用于观察这一主题的不同侧面。",
        "star_text": f"星曜信号：{star_text}；四化信号：{sihua_text}。",
        "opportunity": "、".join(brief["positive_tendencies"][:2]) or "可观察资源与行动空间",
        "risk": "、".join(brief["risk_tendencies"][:2]) or "需要留意节奏与边界",
        "advice": brief["advice"],
        "basis": brief["basis"],
        "source_ids": brief["source_ids"],
    }


def get_sanfang_sizheng(target_palace: str, ziwei_chart: dict) -> dict:
    """获取某宫的三方四正宫位及主星。"""
    target_idx = PALACE_INDEX.get(target_palace)
    if target_idx is None:
        return {"target_palace": target_palace, "error": "未知宫位"}

    # 对宫：+6
    dui_idx = (target_idx + 6) % 12
    # 三合宫：(target - 4) % 12, (target + 4) % 12
    sanhe1 = (target_idx + 4) % 12
    sanhe2 = (target_idx - 4) % 12

    sanfang_names = [INDEX_TO_PALACE.get(sanhe1, ""), INDEX_TO_PALACE.get(sanhe2, "")]
    dui_gong_name = INDEX_TO_PALACE.get(dui_idx, "")

    palaces = ziwei_chart.get("palaces", [])
    main_stars_ready = ziwei_chart.get("main_stars_ready", False)

    def _get_stars(palace_name: str) -> list[str]:
        for p in palaces:
            if p.get("name") == palace_name:
                if main_stars_ready and "main_stars" in p:
                    return p["main_stars"]
                return []
        return []

    related_palaces = {
        "三合宫1": sanfang_names[0],
        "三合宫2": sanfang_names[1],
        "对宫": dui_gong_name,
    }

    stars_info = {}
    for name in [target_palace] + sanfang_names + [dui_gong_name]:
        if name:
            stars_info[name] = _get_stars(name) if main_stars_ready else []

    sihua_by_palace = ziwei_chart.get("sihua_by_palace", {}) or {}
    relation_cards = [
        _card("本宫", target_palace, stars_info.get(target_palace, []), sihua_by_palace.get(target_palace, [])),
        _card("三合支援", sanfang_names[0], stars_info.get(sanfang_names[0], []), sihua_by_palace.get(sanfang_names[0], [])),
        _card("三合支援", sanfang_names[1], stars_info.get(sanfang_names[1], []), sihua_by_palace.get(sanfang_names[1], [])),
        _card("对宫照应", dui_gong_name, stars_info.get(dui_gong_name, []), sihua_by_palace.get(dui_gong_name, [])),
    ]
    source_ids = sorted(set(TRIANGLE_SOURCE_IDS + [sid for card in relation_cards for sid in card.get("source_ids", [])]))
    opportunity_parts = [card["opportunity"] for card in relation_cards if card.get("opportunity")]
    risk_parts = [card["risk"] for card in relation_cards if card.get("risk")]
    advice_parts = [card["advice"] for card in relation_cards if card.get("advice")]

    summary = (
        f"{target_palace}的对宫是{dui_gong_name}。"
        f"三合宫为{sanfang_names[0]}和{sanfang_names[1]}。"
        + ("当前已开启十四主星，可进一步分析星曜分布。" if main_stars_ready
           else "当前为基础结构准备，后续将结合辅星、四化、大限流年增强。")
    )
    plain_explanation = (
        f"三方四正不是只看{target_palace}一个点，而是把本宫、两个三合宫和对宫合起来看。"
        f"本宫看主题本身，三合宫看资源与联动，对宫看外部环境、关系拉扯和现实反馈。"
        f"因此{target_palace}要同时参考{target_palace}、{sanfang_names[0]}、{sanfang_names[1]}、{dui_gong_name}。"
    )

    return {
        "target_palace": target_palace,
        "sanfang": sanfang_names,
        "sizheng": dui_gong_name,
        "related_palaces": related_palaces,
        "main_stars": stars_info,
        "summary": summary,
        "plain_explanation": plain_explanation,
        "relation_cards": relation_cards,
        "opportunity": "；".join(dict.fromkeys(opportunity_parts[:4])),
        "risk": "；".join(dict.fromkeys(risk_parts[:4])),
        "advice": "；".join(dict.fromkeys(advice_parts[:3])),
        "source_ids": source_ids,
        "basis": "参考《紫微斗数全书》《紫微斗数全集》《紫微斗数大全》以及传统十二宫体系：三方四正用于把本宫、三合宫、对宫作为同一主题的联动结构观察。",
        "module_boundary": "当前为基础结构准备，后续将结合辅星、四化、大限流年增强。",
    }
