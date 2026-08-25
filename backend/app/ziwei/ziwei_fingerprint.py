"""紫微命盘差异化特征指纹 — v1.2-B0/B1。"""

from __future__ import annotations

SELF_PALACE = "命宫"
BODY_PALACE = "身宫"

PALACE_LIFE_AREAS = {
    "命宫": "自我定位、性格气质、人生主轴",
    "兄弟宫": "手足情谊、同辈关系、团队协作",
    "夫妻宫": "亲密关系、伴侣模式、合作品质",
    "子女宫": "子女缘分、创造力、晚辈延伸",
    "财帛宫": "财富方式、收入结构、金钱观念",
    "疾厄宫": "身心状态、压力反应、体质倾向",
    "迁移宫": "外出发展、环境适应、异地缘分",
    "交友宫": "朋友质量、团队支持、人际圈层",
    "官禄宫": "事业方向、工作模式、成就路径",
    "田宅宫": "居住环境、不动产、家庭资产",
    "福德宫": "精神世界、内心满足、福分厚薄",
    "父母宫": "长辈关系、家庭背景、上级缘分",
}

PALACE_BRANCH_MEANINGS = {
    "子": "桃花位，情感丰富，社交活跃",
    "丑": "稳定位，务实进取，耐力较强",
    "寅": "开创位，魄力较足，适合开拓",
    "卯": "桃花位，沟通协调，人缘较好",
    "辰": "库位，积累意识强，适合经营",
    "巳": "火位，行动力强，容易变动",
    "午": "旺位，表现欲强，目标感明显",
    "未": "库位，包容性强，需要释放",
    "申": "变动位，适应力强，灵活应变",
    "酉": "桃花位，审美力强，注重细节",
    "戌": "库位，原则性强，需要平衡",
    "亥": "水位，思考力强，内在丰富",
}


def _find_palace(chart: dict, name: str) -> dict:
    if name == "身宫":
        for p in chart.get("palaces", []):
            if p.get("is_body_palace"):
                return p
        return {}
    for p in chart.get("palaces", []):
        if p.get("name") == name:
            return p
    return {}


def build_ziwei_fingerprint(ziwei_chart: dict, profile: dict | None = None) -> dict:
    """提取紫微命盘核心差异化特征。"""
    if not ziwei_chart.get("available"):
        return {"available": False, "main_stars_ready": False}

    life_branch = ziwei_chart.get("life_palace", "")
    body_branch = ziwei_chart.get("body_palace", "")
    same_palace = life_branch == body_branch

    # Palace order
    palace_order = [p.get("name", "") for p in ziwei_chart.get("palaces", [])]
    palace_branches = {p.get("name", ""): p.get("branch", "") for p in ziwei_chart.get("palaces", [])}

    # Key palace focus — personalized
    key_focus = {}
    for name in ["命宫", "身宫", "财帛宫", "官禄宫", "夫妻宫", "疾厄宫", "福德宫", "迁移宫"]:
        p = _find_palace(ziwei_chart, "身宫" if name == "身宫" else name)
        branch = p.get("branch", "")
        area = PALACE_LIFE_AREAS.get(name, "待补充")
        branch_note = PALACE_BRANCH_MEANINGS.get(branch, "")
        key_focus[name] = f"{name}落{branch}支，代表{area}。{branch_note}"

    # Profile tags
    tags = [f"命宫{life_branch}", f"身宫{body_branch}"]
    if same_palace:
        tags.append("命身同宫")
    tags.append(f"生月{ziwei_chart.get('lunar_month', '?')}")
    tags.append(f"时支{ziwei_chart.get('hour_branch', '?')}")

    # Body palace life area
    body_area = PALACE_LIFE_AREAS.get(
        [p.get("name", "") for p in ziwei_chart.get("palaces", []) if p.get("is_body_palace")][0]
        if any(p.get("is_body_palace") for p in ziwei_chart.get("palaces", [])) else "", ""
    )

    # Evidence
    evidence = [
        f"命宫地支：{life_branch}",
        f"身宫地支：{body_branch}",
        f"命身{'同宫' if same_palace else '分离（身宫在' + body_branch + '）'}",
        f"农历{ziwei_chart.get('lunar_month', '?')}月{ziwei_chart.get('lunar_day', '?')}日",
    ]
    main_stars_ready = ziwei_chart.get("main_stars_ready", False)

    return {
        "available": True,
        "main_stars_ready": main_stars_ready,
        "lunar_month": ziwei_chart.get("lunar_month", 0),
        "lunar_day": ziwei_chart.get("lunar_day", 0),
        "birth_hour_branch": ziwei_chart.get("hour_branch", ""),
        "ming_gong": life_branch,
        "shen_gong": body_branch,
        "ming_gong_branch": life_branch,
        "shen_gong_branch": body_branch,
        "is_ming_shen_same_palace": same_palace,
        "shen_gong_life_area": body_area,
        "palace_order": palace_order,
        "palace_branches": palace_branches,
        "key_palace_focus": key_focus,
        "ziwei_profile_tags": tags,
        "evidence": evidence,
        "module_boundary": (
            "当前版本为紫微基础宫位分析版。"
            + ("十四主星落宫已完成。" if main_stars_ready else "十四主星落宫将在后续版本完善，当前版本不伪造主星落宫。")
        ),
    }
