"""十日干十二月调候表与白话解释。

本模块先建立 v1 版本调候表：以日干和月令为主，输出寒暖燥湿层面的
"需要什么气"。它不直接改变日主强弱评分，只作为用神解释层和命局依据。
"""

from __future__ import annotations

from .bazi_constants import BRANCH_MAIN_ELEMENTS

MONTH_BRANCH_INFO = {
    "寅": {"month_name": "寅月", "season": "初春", "climate": "余寒未尽、木气刚起", "season_need": ["丙", "癸"]},
    "卯": {"month_name": "卯月", "season": "仲春", "climate": "木气明显、需要阳光与水分配合", "season_need": ["丙", "癸"]},
    "辰": {"month_name": "辰月", "season": "暮春", "climate": "湿土承接、木气转缓", "season_need": ["甲", "癸"]},
    "巳": {"month_name": "巳月", "season": "初夏", "climate": "火气渐旺、燥热开始明显", "season_need": ["壬", "癸"]},
    "午": {"month_name": "午月", "season": "仲夏", "climate": "火气最旺、燥热最重", "season_need": ["壬", "庚"]},
    "未": {"month_name": "未月", "season": "暮夏", "climate": "燥土夹火、需要润燥疏通", "season_need": ["癸", "甲"]},
    "申": {"month_name": "申月", "season": "初秋", "climate": "金气渐起、气候转肃", "season_need": ["丁", "甲"]},
    "酉": {"month_name": "酉月", "season": "仲秋", "climate": "金气清肃、木火容易受压", "season_need": ["丁", "丙"]},
    "戌": {"month_name": "戌月", "season": "暮秋", "climate": "燥土收束、火库余燥", "season_need": ["甲", "壬"]},
    "亥": {"month_name": "亥月", "season": "初冬", "climate": "水气渐旺、寒意开始", "season_need": ["丙", "甲"]},
    "子": {"month_name": "子月", "season": "仲冬", "climate": "水寒最重、万物收藏", "season_need": ["丙", "戊"]},
    "丑": {"month_name": "丑月", "season": "暮冬", "climate": "寒湿之土、冷湿并见", "season_need": ["丙", "甲"]},
}

DAY_STEM_NEEDS = {
    "甲": {"image": "大树", "core": ["丙", "癸"], "plain": "甲木像大树，既要阳光，也要水分；太寒要火暖，太燥要水润。"},
    "乙": {"image": "花草藤蔓", "core": ["丙", "癸"], "plain": "乙木像花草，重在环境温润；太寒要见火，太燥要见水。"},
    "丙": {"image": "太阳之火", "core": ["壬", "甲"], "plain": "丙火像太阳，太旺要水调，太弱要木来续气。"},
    "丁": {"image": "灯烛之火", "core": ["甲", "庚"], "plain": "丁火像灯烛，先要木来成薪，也需要金来成器、让火有用处。"},
    "戊": {"image": "高山厚土", "core": ["甲", "癸"], "plain": "戊土像山地，土厚要木来疏，燥土要水来润。"},
    "己": {"image": "田园湿土", "core": ["丙", "癸"], "plain": "己土像田园，寒湿时要阳光，燥时要水分，重在能承载万物。"},
    "庚": {"image": "粗金矿铁", "core": ["丁", "甲"], "plain": "庚金像矿铁，常要火来锻炼，也要木来引发用途。"},
    "辛": {"image": "珠玉细金", "core": ["壬", "甲"], "plain": "辛金像珠玉，喜清润不喜浊重，常需水来洗练、木来成财用。"},
    "壬": {"image": "江河大水", "core": ["戊", "丙"], "plain": "壬水像江河，太泛要土来堤防，太寒要火来温暖。"},
    "癸": {"image": "雨露泉水", "core": ["丙", "辛"], "plain": "癸水像雨露，太寒要火照，太浊要金来生清。"},
}

HOT_BRANCHES = {"巳", "午", "未"}
COLD_BRANCHES = {"亥", "子", "丑"}
DRY_BRANCHES = {"巳", "午", "未", "戌"}
WET_BRANCHES = {"亥", "子", "丑", "辰"}


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _entry(day_stem: str, month_branch: str) -> dict:
    day = DAY_STEM_NEEDS.get(day_stem, {})
    month = MONTH_BRANCH_INFO.get(month_branch, {})
    day_core = list(day.get("core", []))
    season_need = list(month.get("season_need", []))

    primary = _dedupe(season_need[:1] + day_core[:1])
    supporting = _dedupe(season_need[1:] + day_core[1:])

    if month_branch in HOT_BRANCHES and "壬" not in primary + supporting:
        supporting.append("壬")
    if month_branch in COLD_BRANCHES and "丙" not in primary + supporting:
        primary.append("丙")
    if month_branch in DRY_BRANCHES and "癸" not in primary + supporting:
        supporting.append("癸")
    if month_branch in WET_BRANCHES and "戊" not in primary + supporting and day_stem in {"壬", "癸", "己"}:
        supporting.append("戊")

    primary = _dedupe(primary)[:3]
    supporting = _dedupe([x for x in supporting if x not in primary])[:3]
    climate = month.get("climate", "月令气候暂不清晰")
    month_name = month.get("month_name", f"{month_branch}月" if month_branch else "未知月令")
    return {
        "day_master": day_stem,
        "month_branch": month_branch,
        "month_name": month_name,
        "season": month.get("season", "季节不明"),
        "climate": climate,
        "day_image": day.get("image", "日主"),
        "primary_useful_stems": primary,
        "supporting_stems": supporting,
        "plain_text": (
            f"{day_stem}日主生在{month_name}（{month.get('season', '季节不明')}），环境像{climate}。"
            f"{day.get('plain', '调候需要结合日主和月令观察')}"
            f"本盘调候先看{'、'.join(primary) or '月令'}，再看{'、'.join(supporting) or '原局配合'}，"
            "意思是先把命局的寒暖燥湿调顺，再谈事业、财运和关系的发挥。"
        ),
        "basis": "参考《穷通宝鉴》十日干十二月调候思路，并结合月令寒暖燥湿作白话化解释。",
    }


def get_seasonal_adjustment_table() -> dict[str, dict[str, dict]]:
    """返回十日干十二月调候表，共 10 x 12 项。"""
    return {
        stem: {branch: _entry(stem, branch) for branch in MONTH_BRANCH_INFO}
        for stem in DAY_STEM_NEEDS
    }


def analyze_seasonal_adjustment(chart: dict) -> dict:
    """根据 chart 输出调候用神解释。"""
    day_stem = chart.get("day_master", "")
    month_branch = chart.get("pillars", {}).get("month", {}).get("zhi", "")
    table = get_seasonal_adjustment_table()
    result = table.get(day_stem, {}).get(month_branch)
    if not result:
        return {
            "day_master": day_stem,
            "month_branch": month_branch,
            "month_name": f"{month_branch}月" if month_branch else "未知月令",
            "primary_useful_stems": [],
            "supporting_stems": [],
            "plain_text": "调候表暂未匹配到此日主与月令，建议先按五行强弱和大运流年观察。",
            "basis": "调候解释暂未匹配。",
        }

    # 观察原局是否已经出现调候所需天干，让用户能看懂“有药/缺药”。
    stems = [p.get("gan", "") for p in chart.get("pillars", {}).values()]
    hidden = []
    try:
        from .bazi_constants import BRANCH_HIDDEN_STEMS
        for p in chart.get("pillars", {}).values():
            hidden.extend(BRANCH_HIDDEN_STEMS.get(p.get("zhi", ""), []))
    except Exception:  # noqa: BLE001 - optional enrichment fallback
        hidden = []
    needed = result["primary_useful_stems"] + result["supporting_stems"]
    visible = [s for s in needed if s in stems]
    hidden_seen = [s for s in needed if s in hidden and s not in visible]
    missing = [s for s in needed if s not in visible and s not in hidden_seen]
    out = dict(result)
    out.update({
        "visible_stems": visible,
        "hidden_stems_seen": hidden_seen,
        "missing_stems": missing,
        "month_element": BRANCH_MAIN_ELEMENTS.get(month_branch, ""),
        "evidence": [
            f"日主为{day_stem}，月令为{result['month_name']}。",
            f"月令气候：{result['climate']}。",
            f"调候优先看：{'、'.join(result['primary_useful_stems']) or '暂无'}。",
            f"辅助观察：{'、'.join(result['supporting_stems']) or '暂无'}。",
        ],
    })
    if visible:
        out["evidence"].append(f"天干已见{'、'.join(visible)}，调候之气较容易被看见。")
    if hidden_seen:
        out["evidence"].append(f"地支藏干中见{'、'.join(hidden_seen)}，代表有潜在条件，但需要大运流年引动。")
    if missing:
        out["evidence"].append(f"原局暂少{'、'.join(missing)}，遇到相关大运流年时更像补足环境。")
    return out
