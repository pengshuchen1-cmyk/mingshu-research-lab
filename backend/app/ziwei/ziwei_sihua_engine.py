"""
生年四化引擎 — v1.2-C

基于出生年天干的传统四化映射表（本版本采用《紫微斗数全书》标准四化表）。
只映射十四主星范围内的四化星，辅星四化标记为待完善。
"""

from __future__ import annotations

SIHUA_MAP: dict[str, dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌*", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼*", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲*"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲*", "化忌": "文昌*"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅*", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

MAIN_STARS = {"紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
              "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}


def get_sihua_by_year_gan(year_gan: str) -> dict:
    """
    根据年干返回生年四化映射。
    返回结构含 mapping、interpretation、marked_stars 等。
    """
    mapping = SIHUA_MAP.get(year_gan, {})
    if not mapping:
        return {
            "sihua_ready": False,
            "year_gan": year_gan or "",
            "mapping": {},
            "main_star_transforms": {},
            "minor_transforms": [],
            "interpretation": {},
            "source_ids": ["ziwei_doushu_quanshu", "traditional_ziwei_sihua_system"],
        }

    # Separate main star transforms from minor star transforms
    main_transforms = {}
    minor_transforms = []
    for transform_type, star_name in mapping.items():
        if star_name.endswith("*"):
            clean_name = star_name.rstrip("*")
            minor_transforms.append({"transform": transform_type, "star": clean_name, "note": "辅星四化，当前版本暂未落宫"})
        elif star_name in MAIN_STARS:
            main_transforms[transform_type] = star_name
        else:
            minor_transforms.append({"transform": transform_type, "star": star_name, "note": "星曜不在十四主星范围内"})

    interpretations = {}
    interp_data = {
        "化禄": ("代表该星曜所在宫位容易展现财气、机遇和流动性。为人处世或事业发展中更容易借该星特质获利。",
                 ["ziwei_doushu_quanshu"]),
        "化权": ("代表该星曜所在宫位容易展现掌控力、决策力和执行力。在对应的生活领域中个人主导性会增强。",
                 ["ziwei_doushu_quanshu"]),
        "化科": ("代表该星曜所在宫位容易展现名望、才华和外在形象。个人在该领域的能力容易被外界看见和认可。",
                 ["ziwei_doushu_quanshu"]),
        "化忌": ("代表该星曜所在宫位容易展现课题、消耗和需要面对的问题。该领域需要更多耐心、调整和关注。",
                 ["traditional_ziwei_sihua_system"]),
    }
    for tt, (text, srcs) in interp_data.items():
        if tt in mapping:
            interpretations[tt] = {
                "meaning": text,
                "star": mapping[tt].rstrip("*"),
                "is_minor": tt in [m["transform"] for m in minor_transforms],
            }

    sihua_ready = len(main_transforms) > 0 or len(minor_transforms) > 0

    return {
        "sihua_ready": sihua_ready,
        "year_gan": year_gan,
        "mapping": mapping,
        "main_star_transforms": main_transforms,
        "minor_transforms": minor_transforms,
        "interpretation": interpretations,
        "basis": f"基于紫微斗数全书四化表，年干{year_gan}时四化分布如上。",
        "source_ids": ["ziwei_doushu_quanshu", "traditional_ziwei_sihua_system"],
    }


def apply_sihua_to_chart(ziwei_chart: dict, sihua_data: dict) -> dict:
    """
    将四化信息映射到紫微命盘的十二宫中。
    只对十四主星范围内的星曜做宫位映射。
    """
    if not sihua_data.get("sihua_ready"):
        return sihua_data

    main_transforms = sihua_data.get("main_star_transforms", {})
    msbp = ziwei_chart.get("main_stars_by_palace", {})
    if not msbp:
        return sihua_data

    sihua_by_palace: dict[str, list[str]] = {}
    for palace_name, stars in msbp.items():
        for star in stars:
            for transform_type, transform_star in main_transforms.items():
                if star == transform_star:
                    if palace_name not in sihua_by_palace:
                        sihua_by_palace[palace_name] = []
                    sihua_by_palace[palace_name].append(transform_type)

    sihua_data["sihua_by_palace"] = sihua_by_palace
    return sihua_data
