"""紫微斗数基础排盘 + 十四主星落宫 — v1.2-B。"""

from __future__ import annotations

from datetime import date

from core.ziwei_constants import BRANCHES, PALACE_EXPLANATIONS, PALACE_NAMES
from core.ziwei_star_engine import calculate_ziwei_main_stars, get_year_branch_from_profile, get_year_gan_from_profile

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
            year_branch = get_year_branch_from_profile(profile)
            if year_gan:
                star_data = calculate_ziwei_main_stars(year_gan, abs(lunar_month), abs(lunar_day), life_branch)
        except Exception:
            year_gan = ""
            year_branch = ""
            star_data = {"main_stars_ready": False, "main_stars_by_palace": {}}

        result = {
            "available": True, "profile": profile,
            "lunar_month": lunar_month, "lunar_day": lunar_day,
            "hour_branch": hour_branch,
            "year_gan": year_gan,
            "year_branch": year_branch,
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
        # 集成辅星/煞星/大限（v1.2-F）
        try:
            extra = _integrate_minor_fierce_stars(result, profile)
            result.update(extra)
        except Exception:
            result["minor_stars_ready"] = False
            result["fierce_stars_ready"] = False
            result["daxian"] = {"daxian_ready": False, "error": "辅星/煞星/大限集成异常"}
        return result
    except Exception as exc:
        return {
            "available": False, "profile": profile, "palaces": [],
            "message": f"紫微斗数基础盘暂未成功生成：{exc}",
        }

# ====== 辅星/煞星集成（v1.2-F）======

def _integrate_minor_fierce_stars(chart: dict, profile: dict) -> dict:
    """将辅星和煞星落宫数据集成到命盘结果中。"""
    hour_branch = chart.get("hour_branch", "子")
    lunar_month = abs(chart.get("lunar_month", 1))
    
    # 获取年干、年支
    year_gan = ""
    year_branch = ""
    try:
        from core.ziwei_star_engine import get_year_branch_from_profile, get_year_gan_from_profile
        year_gan = get_year_gan_from_profile(profile) or ""
        year_branch = get_year_branch_from_profile(profile) or ""
    except Exception:
        pass

    # 辅星
    minor_results = {}
    if hour_branch and lunar_month:
        from core.ziwei_minor_star_engine import calculate_all_minor_stars
        minor_results = calculate_all_minor_stars(hour_branch, lunar_month)

    # 煞星
    fierce_results = {}
    if year_gan and year_branch and hour_branch:
        from core.ziwei_fierce_star_engine import calculate_all_fierce_stars
        fierce_results = calculate_all_fierce_stars(year_gan, year_branch, hour_branch)

    # 按宫位名称映射
    palace_name_by_branch = {}
    for p in chart.get("palaces", []):
        palace_name_by_branch[p["branch"]] = p["name"]

    # 辅星落宫映射
    minor_by_palace = {}
    for key, star_data in minor_results.get("stars", {}).items():
        branch = star_data.get("branch", "")
        pname = palace_name_by_branch.get(branch, "")
        if pname:
            sname = star_data.get("star", "")
            if pname not in minor_by_palace:
                minor_by_palace[pname] = []
            minor_by_palace[pname].append(sname)

    # 煞星落宫映射
    fierce_by_palace = {}
    for key, star_data in fierce_results.get("stars", {}).items():
        branch = star_data.get("branch", "")
        pname = palace_name_by_branch.get(branch, "")
        if pname:
            sname = star_data.get("star", "")
            if pname not in fierce_by_palace:
                fierce_by_palace[pname] = []
            fierce_by_palace[pname].append(sname)

    # 写回 palaces
    for p in chart.get("palaces", []):
        pname = p["name"]
        p["minor_stars"] = minor_by_palace.get(pname, [])
        p["fierce_stars"] = fierce_by_palace.get(pname, [])

    result_extra = {
        "minor_stars_ready": minor_results.get("all_ready", False),
        "minor_stars_by_palace": minor_by_palace,
        "minor_stars_placement": minor_results,
        "fierce_stars_ready": fierce_results.get("placement_ready", False),
        "fierce_stars_by_palace": fierce_by_palace,
        "fierce_stars_placement": fierce_results,
    }

    # 大限计算
    try:
        gender = profile.get("gender", "")
        if gender:
            from core.ziwei_daxian_engine import calculate_daxian
            five_element_number = chart.get("five_element_bureau", {}).get("number", 4) if isinstance(chart.get("five_element_bureau"), dict) else 4
            daxian = calculate_daxian(
                gender, year_gan, five_element_number,
                chart.get("life_palace", ""), chart.get("body_palace", ""),
                chart.get("main_stars_by_palace", {})
            )
            # 补充辅星/煞星到大限各阶段
            if daxian.get("daxian_ready"):
                for idx, stage in enumerate(daxian.get("stages", [])):
                    pname = stage.get("palace", "")
                    stage["minor_stars"] = minor_by_palace.get(pname, [])
                    stage["fierce_stars"] = fierce_by_palace.get(pname, [])
            result_extra["daxian"] = daxian
    except Exception:
        result_extra["daxian"] = {"daxian_ready": False, "error": "大限计算异常"}

    return result_extra
