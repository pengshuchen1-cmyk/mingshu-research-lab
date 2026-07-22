"""大众年日建议引擎。

本模块只生成不依赖个人命盘的首页建议，定位为传统文化节律提醒。
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.sixty_jiazi import get_jiazi_by_year


SHANGHAI_TIMEZONE = "Asia/Shanghai"


class PopularAdviceUnavailableError(RuntimeError):
    """Raised when verified calendar data cannot be produced."""


ELEMENT_ADVICE = {
    "木": {
        "colors": ["青绿", "浅蓝"],
        "wearing": "可选择绿色、木质感或简洁自然材质，提醒自己保持生发与规划感。",
        "relax": "适合散步、伸展、整理计划，把心里的想法写成可执行清单。",
        "actions": ["学习规划", "沟通协作", "启动小计划"],
        "avoid": ["临时改方向", "情绪化承诺"],
        "year_focus": "重视成长、学习、长期规划和人际生发。",
        "wellbeing": "多接触自然光和绿色环境，让身体从紧绷里慢慢松开。",
    },
    "火": {
        "colors": ["红色", "暖橙"],
        "wearing": "可用一点红色、橙色或暖色配饰提气，但不必过度张扬。",
        "relax": "适合晒太阳、轻运动、深呼吸，把旺盛念头转成有节奏的行动。",
        "actions": ["表达展示", "推进事项", "整理目标"],
        "avoid": ["急躁争辩", "过度透支"],
        "year_focus": "重视表达、行动、曝光、热度管理和节奏控制。",
        "wellbeing": "注意睡眠、心火和情绪热度，忙的时候也给自己留缓冲。",
    },
    "土": {
        "colors": ["米黄", "大地色"],
        "wearing": "可选择米黄、咖色、陶土色或稳定质感的物件，帮助自己落回现实节奏。",
        "relax": "适合收纳、慢走、规律饮食，用秩序感安顿压力。",
        "actions": ["整理财务", "稳定执行", "处理家务"],
        "avoid": ["拖延堆积", "过度担忧"],
        "year_focus": "重视稳定、积累、承载、责任边界和现实落地。",
        "wellbeing": "照顾脾胃和作息，少让琐事长期堆在心里。",
    },
    "金": {
        "colors": ["白色", "金色"],
        "wearing": "可选择白色、金属色或线条清晰的配饰，提醒自己保持边界和标准。",
        "relax": "适合断舍离、清理桌面、做一次简短复盘，让注意力回到重点。",
        "actions": ["制定规则", "精修作品", "处理文书"],
        "avoid": ["语气过硬", "苛责细节"],
        "year_focus": "重视规则、执行、专业标准、收束整理和边界感。",
        "wellbeing": "留意呼吸、肩颈和干燥感，适合用稳定节奏替代硬撑。",
    },
    "水": {
        "colors": ["黑色", "深蓝"],
        "wearing": "可选择深蓝、黑色或有流动感的小物，提醒自己保持弹性。",
        "relax": "适合听音乐、泡脚、安静阅读，让信息量沉淀下来。",
        "actions": ["信息整理", "复盘沟通", "灵感记录"],
        "avoid": ["想太多不行动", "夜间过度消耗"],
        "year_focus": "重视信息、流动、沟通、资源调度和内在恢复。",
        "wellbeing": "注意补水、睡眠和情绪回收，不把所有事都留到深夜消化。",
    },
}


def _split_pillar(pillar: str) -> tuple[str, str]:
    return (pillar[0], pillar[1]) if len(pillar) >= 2 else ("", "")


def _get_day_pillar(target_date: date) -> str:
    """Return the verified day pillar or fail without inventing a value."""
    try:
        from lunar_python import Solar

        try:
            solar = Solar(target_date.year, target_date.month, target_date.day, 12, 0, 0)
        except TypeError:
            solar = Solar.fromYmdHms(target_date.year, target_date.month, target_date.day, 12, 0, 0)
        eight_char = solar.getLunar().getEightChar()
        for method_name in ["getDay", "getDayInGanZhi"]:
            method = getattr(eight_char, method_name, None)
            if callable(method):
                value = method()
                if value:
                    return str(value)
    except Exception as exc:
        raise PopularAdviceUnavailableError("今日干支暂时无法计算") from exc

    raise PopularAdviceUnavailableError("今日干支暂时无法计算")


def _today_in_shanghai() -> date:
    return datetime.now(ZoneInfo(SHANGHAI_TIMEZONE)).date()


def _merge_element_lists(primary: str, secondary: str, field: str, limit: int) -> list[str]:
    values = []
    for element in [primary, secondary]:
        values.extend(ELEMENT_ADVICE.get(element, {}).get(field, []))
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result[:limit]


def build_daily_advice(target_date: date | None = None) -> dict:
    """生成不依赖个人命盘的每日建议。"""
    target_date = target_date or _today_in_shanghai()
    pillar = _get_day_pillar(target_date)
    gan, zhi = _split_pillar(pillar)
    gan_element = STEM_ELEMENTS.get(gan, "")
    zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
    primary = gan_element or zhi_element or "土"
    secondary = zhi_element or primary
    primary_rule = ELEMENT_ADVICE[primary]
    secondary_rule = ELEMENT_ADVICE[secondary]

    return {
        "date": target_date.isoformat(),
        "pillar": pillar,
        "day_pillar": pillar,
        "element_theme": primary,
        "timezone": SHANGHAI_TIMEZONE,
        "boundary_note": (
            "本内容未读取姓名、性别或出生资料，是同一天所有用户共用的传统历法生活参考，"
            "属于非个人命盘分析。不作为医疗、投资、法律、婚姻等重大决定依据。"
        ),
        "title": f"今日建议｜{pillar}日",
        "elements": [item for item in [gan_element, zhi_element] if item],
        "lucky_colors": _merge_element_lists(primary, secondary, "colors", 3),
        "wearing_advice": primary_rule["wearing"],
        "relaxation_advice": secondary_rule["relax"],
        "suitable_actions": _merge_element_lists(primary, secondary, "actions", 4),
        "actions_to_avoid": _merge_element_lists(primary, secondary, "avoid", 3),
        "basis": (
            f"依据今日干支{pillar}的天干五行{gan_element or '待查'}、"
            f"地支主气{zhi_element or '待查'}生成大众节律提醒；不替代个人命盘分析。"
        ),
    }


def build_yearly_popular_advice(target_year: int | None = None) -> dict:
    """生成不依赖个人命盘的年度大众建议。"""
    year = int(target_year or date.today().year)
    entry = get_jiazi_by_year(year)
    pillar = entry["pillar"]
    gan, zhi = _split_pillar(pillar)
    gan_element = STEM_ELEMENTS.get(gan, "")
    zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
    primary = gan_element or zhi_element or "土"
    secondary = zhi_element or primary
    primary_rule = ELEMENT_ADVICE[primary]
    secondary_rule = ELEMENT_ADVICE[secondary]

    keywords = []
    for element in [primary, secondary]:
        focus = ELEMENT_ADVICE[element]["year_focus"].replace("重视", "").replace("。", "")
        keywords.extend([part for part in focus.split("、") if part])
    keywords = list(dict.fromkeys(keywords))[:5]
    wellbeing_advice = list(dict.fromkeys([primary_rule["wellbeing"], secondary_rule["wellbeing"]]))
    if len(wellbeing_advice) < 2:
        wellbeing_advice.append("把重要事项分成小步推进，给休息、饮食和情绪恢复留出固定时间。")

    return {
        "year": year,
        "pillar": pillar,
        "title": f"今年建议｜{year}年 {pillar}",
        "elements": [item for item in [gan_element, zhi_element] if item],
        "keywords": keywords,
        "annual_tone": f"{pillar}年可从{primary_rule['year_focus']}同时留意{secondary_rule['year_focus']}",
        "action_advice": _merge_element_lists(primary, secondary, "actions", 5),
        "wellbeing_advice": wellbeing_advice,
        "colors": _merge_element_lists(primary, secondary, "colors", 4),
        "boundary_note": entry.get("lichun_boundary_note", "八字年柱通常以立春为换年点，年份边界需结合节气复核。"),
        "basis": (
            f"依据{year}年干支{pillar}、天干五行{gan_element or '待查'}、"
            f"地支主气{zhi_element or '待查'}生成大众化年度提醒；个人运势仍需结合完整命盘。"
        ),
    }
