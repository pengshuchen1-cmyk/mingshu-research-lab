"""
三方四正基础结构 — v1.2-B2。

每个宫位的三方四正：
- 对宫：同宫位 + 6
- 三合：+4, +8 (或 -4, +4)
三合宫 = 命宫 +4, 命宫 +8 (顺时针)
"""

from __future__ import annotations

PALACE_INDEX: dict[str, int] = {
    "命宫": 0, "兄弟宫": 1, "夫妻宫": 2, "子女宫": 3,
    "财帛宫": 4, "疾厄宫": 5, "迁移宫": 6, "交友宫": 7,
    "官禄宫": 8, "田宅宫": 9, "福德宫": 10, "父母宫": 11,
}

INDEX_TO_PALACE: dict[int, str] = {v: k for k, v in PALACE_INDEX.items()}


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

    summary = (
        f"{target_palace}的对宫是{dui_gong_name}。"
        f"三合宫为{sanfang_names[0]}和{sanfang_names[1]}。"
        + (f"当前已开启十四主星，可进一步分析星曜分布。" if main_stars_ready
           else "当前为基础结构准备，后续将结合辅星、四化、大限流年增强。")
    )

    return {
        "target_palace": target_palace,
        "sanfang": sanfang_names,
        "sizheng": dui_gong_name,
        "related_palaces": related_palaces,
        "main_stars": stars_info,
        "summary": summary,
        "module_boundary": "当前为基础结构准备，后续将结合辅星、四化、大限流年增强。",
    }
