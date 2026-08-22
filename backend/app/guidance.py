"""Deterministic public daily and yearly guidance migrated from the legacy UI."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .bazi.bazi_calendar_adapter import day_pillar_seed
from .bazi.bazi_constants import (
    BRANCH_MAIN_ELEMENTS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
)

SHANGHAI_TIMEZONE = "Asia/Shanghai"


class DailyGuidanceUnavailableError(RuntimeError):
    """Raised when the authoritative calendar adapter cannot produce a day pillar."""


ELEMENT_ADVICE: dict[str, dict[str, str | list[str]]] = {
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


def today_in_shanghai() -> date:
    """Return the product's authoritative public-guidance date."""
    return datetime.now(ZoneInfo(SHANGHAI_TIMEZONE)).date()


def _day_pillar(target_date: date) -> str:
    try:
        stem, branch = day_pillar_seed(target_date)
        return f"{stem}{branch}"
    except Exception as exc:
        raise DailyGuidanceUnavailableError("daily calendar data is unavailable") from exc


def _year_pillar(year: int) -> str:
    """Return the sexagenary year name; 4 CE and 1984 are both Jia-Zi years."""
    offset = year - 4
    return f"{HEAVENLY_STEMS[offset % 10]}{EARTHLY_BRANCHES[offset % 12]}"


def _rule_text(element: str, field: str) -> str:
    value = ELEMENT_ADVICE[element][field]
    if not isinstance(value, str):
        raise TypeError(f"guidance field {field} must be text")
    return value


def _merge_element_lists(
    primary: str, secondary: str, field: str, limit: int
) -> list[str]:
    result: list[str] = []
    for element in (primary, secondary):
        values = ELEMENT_ADVICE[element][field]
        if not isinstance(values, list):
            raise TypeError(f"guidance field {field} must be a list")
        for value in values:
            if value and value not in result:
                result.append(value)
    return result[:limit]


def build_daily_guidance(target_date: date | None = None) -> dict:
    """Build the public daily DTO without reading user or birth-profile data."""
    resolved_date = target_date or today_in_shanghai()
    pillar = _day_pillar(resolved_date)
    stem_element = STEM_ELEMENTS.get(pillar[0], "")
    branch_element = BRANCH_MAIN_ELEMENTS.get(pillar[1], "")
    primary = stem_element or branch_element or "土"
    secondary = branch_element or primary
    actions = _merge_element_lists(primary, secondary, "actions", 4)
    cautions = _merge_element_lists(primary, secondary, "avoid", 3)
    colors = _merge_element_lists(primary, secondary, "colors", 3)
    wearing_advice = _rule_text(primary, "wearing")

    return {
        "kind": "daily_guidance",
        "is_personal": False,
        "date": resolved_date.isoformat(),
        "day_pillar": pillar,
        "title": f"今日建议｜{pillar}日",
        "element_theme": primary,
        "wearing_colors": colors,
        "wearing_advice": wearing_advice,
        "cautions": cautions,
        "primary_action": actions[0] if actions else "整理当下重点",
        "theme": primary,
        "focus": actions[0] if actions else "整理当下重点",
        "action": wearing_advice,
        "reminder": cautions[0] if cautions else "避免过度消耗",
        "details": {
            "colors": list(colors),
            "relaxation": _rule_text(secondary, "relax"),
            "actions": actions,
        },
        "basis": (
            f"依据今日干支{pillar}的天干五行{stem_element or '待查'}、"
            f"地支主气{branch_element or '待查'}生成大众节律提醒；不替代个人命盘分析。"
        ),
        "boundary_note": (
            "本内容未读取姓名、性别或出生资料，是同一天所有用户共用的传统历法生活参考，"
            "属于非个人命盘分析。不作为医疗、投资、法律、婚姻等重大决定依据。"
        ),
    }


def build_yearly_guidance(target_year: int) -> dict:
    """Build the public yearly DTO paired with the daily-guidance page."""
    pillar = _year_pillar(target_year)
    stem_element = STEM_ELEMENTS.get(pillar[0], "")
    branch_element = BRANCH_MAIN_ELEMENTS.get(pillar[1], "")
    primary = stem_element or branch_element or "土"
    secondary = branch_element or primary
    keywords: list[str] = []
    for element in (primary, secondary):
        focus = _rule_text(element, "year_focus").replace("重视", "").replace("。", "")
        keywords.extend(part for part in focus.split("、") if part)
    keywords = list(dict.fromkeys(keywords))[:5]

    return {
        "kind": "yearly_guidance",
        "is_personal": False,
        "year": target_year,
        "title": f"今年建议｜{target_year}年 {pillar}",
        "theme": (
            f"{pillar}年可从{_rule_text(primary, 'year_focus')}"
            f"同时留意{_rule_text(secondary, 'year_focus')}"
        ),
        "focus": keywords[0] if keywords else "整理年度重点",
        "actions": _merge_element_lists(primary, secondary, "actions", 5),
        "basis": (
            f"依据{target_year}年干支{pillar}、天干五行{stem_element or '待查'}、"
            f"地支主气{branch_element or '待查'}生成大众化年度提醒；个人运势仍需结合完整命盘。"
        ),
        "boundary_note": (
            "八字年柱通常以立春为换年点，不是简单按公历1月1日切换；"
            "如果生日在2月3日至2月5日前后，需要结合当年立春时间复核。"
        ),
    }


def build_today_guidance(
    target_date: date | None = None,
    target_year: int | None = None,
) -> dict:
    """Build the whole public Today-page contract with graceful daily fallback."""
    resolved_date = target_date or today_in_shanghai()
    try:
        daily = build_daily_guidance(resolved_date)
    except DailyGuidanceUnavailableError:
        daily = None
    resolved_year = target_year if target_year is not None else resolved_date.year
    return {
        "timezone": SHANGHAI_TIMEZONE,
        "daily_guidance": daily,
        "yearly_guidance": build_yearly_guidance(resolved_year),
    }
