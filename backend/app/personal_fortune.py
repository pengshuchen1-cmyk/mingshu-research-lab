"""Backend adapter for the fully migrated personal fortune engines."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from .bazi.bazi_calendar_adapter import BirthInput
from .bazi.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from .bazi.dayun_rule_engine import build_dayun_periods, calculate_dayun
from .bazi.four_pillars_engine import calculate_four_pillars
from .bazi.ten_gods import get_ten_god
from .fortune.evidence_display import build_display_trigger_factors
from .fortune.monthly_engine import analyze_monthly_fortune
from .fortune.monthly_event_activation_bridge import build_year_monthly_event_results
from .fortune.stage_engine import analyze_luck_stage
from .fortune.yearly_engine import analyze_yearly_fortune

FORTUNE_ENGINE_VERSION = "personal-fortune-legacy-equivalent-v1"
RELATION_GODS = {"男": {"正财", "偏财"}, "女": {"正官", "七杀"}}


@dataclass(frozen=True, slots=True)
class FortuneProfileInput:
    calendar_type: Literal["solar", "lunar"]
    birth_date: str
    birth_hour: int | None
    birth_minute: int | None
    gender: Literal["男", "女"]
    is_leap_month: bool


def _birth_input(profile: FortuneProfileInput) -> BirthInput:
    year, month, day = (int(part) for part in profile.birth_date.split("-"))
    return BirthInput(
        profile.calendar_type,
        year,
        month,
        day,
        profile.birth_hour,
        profile.birth_minute,
        "male" if profile.gender == "男" else "female",
        profile.is_leap_month,
    )


def _build_luck_data(
    profile: FortuneProfileInput,
    chart: dict[str, Any],
) -> dict[str, Any]:
    """Build the same luck-cycle input consumed by the legacy yearly page."""
    try:
        birth = _birth_input(profile)
        pillars = calculate_four_pillars(birth)
        basis = calculate_dayun(birth, pillars)
        periods = build_dayun_periods(
            pillars.month.text,
            basis,
            pillars.calendar.converted_solar_date.year,
            10,
        )
        dayun_list: list[dict[str, Any]] = []
        for period in periods:
            item = dict(period)
            gan = str(item["gan"])
            zhi = str(item["zhi"])
            item.update(
                {
                    "gan_element": STEM_ELEMENTS.get(gan, ""),
                    "zhi_element": BRANCH_MAIN_ELEMENTS.get(zhi, ""),
                    "ten_god": get_ten_god(str(chart.get("day_master", "")), gan),
                }
            )
            item.update(analyze_luck_stage(chart, item))
            dayun_list.append(item)
        return {
            "available": True,
            "direction": basis.direction,
            "direction_label": basis.direction_label,
            "start_age": basis.start_age_years,
            "start_year": basis.start_datetime.year,
            "start_month": basis.start_age_months,
            "start_day": basis.start_age_days,
            "start_text": basis.start_text,
            "dayun_list": dayun_list,
            "data_warnings": [],
        }
    except (KeyError, TypeError, ValueError, RuntimeError):
        return {
            "available": False,
            "direction": None,
            "direction_label": None,
            "start_text": "大运背景暂时无法计算；年度和流月结果仍可使用。",
            "dayun_list": [],
            "data_warnings": [],
        }


def _luck_context(luck_data: dict[str, Any], target_year: int) -> dict[str, Any]:
    current = next(
        (
            item
            for item in luck_data.get("dayun_list", [])
            if int(item["start_year"]) <= target_year <= int(item["end_year"])
        ),
        None,
    )
    return {
        "available": bool(luck_data.get("available")),
        "direction": luck_data.get("direction"),
        "direction_label": luck_data.get("direction_label"),
        "start_text": str(luck_data.get("start_text", "")),
        "current_period": current,
    }


def _relationship_months(
    monthly: list[dict[str, Any]], gender: Literal["男", "女"]
) -> tuple[list[str], list[str]]:
    gods = RELATION_GODS[gender]
    favorable = [
        str(item.get("month_name", ""))
        for item in monthly
        if item.get("ten_god") in gods and item.get("relation_to_favorable") == "喜用相关"
    ]
    unfavorable = [
        str(item.get("month_name", ""))
        for item in monthly
        if item.get("ten_god") in gods and item.get("relation_to_favorable") == "忌神相关"
    ]
    return favorable[:4], unfavorable[:4]


def build_personal_fortune(
    profile_id: str,
    chart_fingerprint: str,
    profile: FortuneProfileInput,
    chart: dict[str, Any],
    target_year: int,
) -> dict[str, Any]:
    """Run the migrated legacy pipeline over one stored chart snapshot."""
    analysis_chart = deepcopy(chart)
    luck_data = _build_luck_data(profile, analysis_chart)
    monthly = analyze_monthly_fortune(analysis_chart, target_year)
    yearly = analyze_yearly_fortune(
        analysis_chart,
        target_year,
        luck_data,
        monthly_data=monthly,
    )
    relationship_good, relationship_bad = _relationship_months(monthly, profile.gender)
    yearly["relationship_good_months"] = relationship_good
    yearly["relationship_bad_months"] = relationship_bad
    event_results = build_year_monthly_event_results(
        analysis_chart,
        monthly,
        yearly,
        luck_data,
    )
    monthly_with_events = []
    for index, item in enumerate(monthly):
        combined = dict(item)
        event_result = event_results[index] if index < len(event_results) else {}
        combined["top_events"] = [
            {
                **event,
                "display_trigger_factors": build_display_trigger_factors(event),
            }
            for event in event_result.get("top_events", [])
        ]
        monthly_with_events.append(combined)

    return {
        "kind": "personal_fortune",
        "is_personal": True,
        "profile_id": profile_id,
        "chart_fingerprint": chart_fingerprint,
        "target_year": target_year,
        "fortune_engine_version": FORTUNE_ENGINE_VERSION,
        "generated_at": datetime.now(UTC),
        "luck_context": _luck_context(luck_data, target_year),
        "yearly": yearly,
        "monthly": monthly_with_events,
        "boundary_note": "本结果基于传统命理模型，仅供个人兴趣与文化研究参考；不替代医疗、法律、投资或其他专业意见。",
    }
