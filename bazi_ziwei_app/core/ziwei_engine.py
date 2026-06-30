"""紫微斗数基础排盘 + 十四主星落宫 — v1.2-B。"""

from __future__ import annotations

from datetime import date

from core.ziwei_constants import BRANCHES, PALACE_EXPLANATIONS, PALACE_NAMES
from core.ziwei_star_engine import calculate_ziwei_main_stars, get_year_gan_from_profile

HOUR_TO_BRANCH = {
    23: "子", 0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅",
    5: "卯", 6: "卯", 7: "辰", 8: "辰", 9: "巳", 10: "巳",
    11: "午", 12: "午", 13: "未", 14: "未", 15: "申", 16: "申",
    17: "酉", 18: "酉", 19: "戌", 20: "戌", 21: "亥", 22: "亥",
}


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    """解析出生日期。"""
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def _lunar_month_day(profile: dict) -> tuple[int, int]:
    """获取农历月日。"""
    year, month, day = _parse_birth_date(profile.get("birth_date"))
    try:
        from lunar_python import Solar
        try:
            solar = Solar(year, month, day, int(profile.get("birth_hour", 0)), int(profile.get("birth_minute", 0)), 0)
        except TypeError:
            solar = Solar.fromYmdHms(year, month, day, int(profile.get("birth_hour", 0)), int(profile.get("birth_minute", 0)), 0)
        lunar = solar.getLunar()
        return int(lunar.getMonth()), int(lunar.getDay())
    except Exception:
        return month, day


def _branch_index(branch: str) -> int:
    return BRANCHES.index(branch) if branch in BRANCHES else 0


def _calculate_life_body_palace(lunar_month: int, hour_branch: str) -> tuple[str, str]:
    hour_index = _branch_index(hour_branch)
    life_index = (2 + lunar_month - 1 - hour_index) % 12
    body_index = (2 + lunar_month - 1 + hour_index) % 12
    return BRANCHES[life_index], BRANCHES[body_index]


def _build_palaces(life_branch: str, body_branch: str) -> list[dict]:
    start = _branch_index(life_branch)
    palaces = []
    for offset, name in enumerate(PALACE_NAMES):
        branch = BRANCHES[(start + offset) % 12]
        palaces.append({
            "name": name, "branch": branch,
            "is_life_palace": branch == life_branch,
            "is_body_palace": branch == body_branch,
            "main_stars": [],
            "transforms": [],
            "explanation": PALACE_EXPLANATIONS.get(name, ""),
        })
    return palaces


def build_ziwei_chart(profile: dict) -> dict:
    """生成紫微斗数盘（含十四主星落宫）。"""
    try:
        lunar_month, lunar_day = _lunar_month_day(profile)
        hour_branch = HOUR_TO_BRANCH.get(int(profile.get("birth_hour", 0)), "子")
        life_branch, body_branch = _calculate_life_body_palace(abs(lunar_month), hour_branch)
        palaces = _build_palaces(life_branch, body_branch)

        # 十四主星排布
        star_data = {"main_stars_ready": False, "main_stars_by_palace": {}}
        try:
            year_gan = get_year_gan_from_profile(profile)
            if year_gan:
                star_data = calculate_ziwei_main_stars(year_gan, abs(lunar_month), abs(lunar_day), life_branch)
        except Exception:
            star_data = {"main_stars_ready": False, "main_stars_by_palace": {}}

        result = {
            "available": True, "profile": profile,
            "lunar_month": lunar_month, "lunar_day": lunar_day,
            "hour_branch": hour_branch,
            "life_palace": life_branch, "body_palace": body_branch,
            "palaces": palaces,
        }

        if star_data.get("main_stars_ready"):
            msbp = star_data.get("main_stars_by_palace", {})
            for p in palaces:
                pname = p.get("name", "")
                if pname in msbp and msbp[pname]:
                    p["main_stars"] = msbp[pname]
            result["main_stars_ready"] = True
            result["main_stars_by_palace"] = msbp
            result["five_element_bureau"] = star_data.get("five_element_bureau", "")
            result["algorithm"] = star_data.get("algorithm", "")
            result["algorithm_evidence"] = star_data.get("algorithm_evidence", [])
            result["star_note"] = "十四主星排布已实现（v1.2-B），基于传统起星诀计算。"
            result["message"] = "已生成紫微斗数宫位盘，包含十四主星落宫。"
        else:
            result["main_stars_ready"] = False
            result["main_stars_by_palace"] = {}
            result["star_note"] = "十四主星排布未能计算。"
            result["message"] = "已生成紫微斗数基础宫位盘。十四主星排布暂未完成。"
        return result
    except Exception as exc:
        return {
            "available": False, "profile": profile, "palaces": [],
            "message": f"紫微斗数基础盘暂未成功生成：{exc}",
        }
