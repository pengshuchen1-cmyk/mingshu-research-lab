"""Compatibility adapter over the project-local dayun rule engine."""

from __future__ import annotations

from datetime import date, datetime

from core.bazi_calendar_adapter import BirthInput
from core.bazi_constants import (
    BRANCH_MAIN_ELEMENTS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
)
from core.chart_facts import attach_chart_facts
from core.dayun_rule_engine import build_dayun_periods, calculate_dayun
from core.four_pillars_engine import calculate_four_pillars
from core.stage_engine import analyze_luck_stage
from core.ten_gods import get_ten_god
from core.yearly_engine import analyze_yearly_fortune


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def _normalize_age_range(
    raw_start_age: int,
    raw_end_age: int,
    reference_start_age: int = 0,
    index: int = 0,
) -> tuple[int, int, str]:
    data_warning = ""
    if raw_start_age < 0:
        data_warning = "大运起运年龄为负，已按规则边界重新归零"
        start_age = max(0, reference_start_age, raw_end_age - 9)
    elif reference_start_age > 0 and raw_start_age < reference_start_age and index == 0:
        start_age = reference_start_age
    else:
        start_age = max(0, raw_start_age)
    end_age = raw_end_age if raw_end_age >= start_age else start_age + 9
    return start_age, end_age, data_warning


def _pillar_year(year: int) -> str:
    return f"{HEAVENLY_STEMS[(year - 4) % 10]}{EARTHLY_BRANCHES[(year - 4) % 12]}"


def _build_yearly_list(chart: dict, years: int = 10) -> list[dict]:
    current_year = datetime.now().year
    items: list[dict] = []
    for year in range(current_year, current_year + years):
        try:
            items.append(
                analyze_yearly_fortune(
                    chart,
                    year,
                    include_monthly_analysis=False,
                )
            )
        except Exception:
            continue
    return items


def _birth_from_profile(profile: dict) -> BirthInput:
    calendar = "lunar" if profile.get("calendar_type") == "lunar" else "solar"
    source = profile.get("lunar_birth_date") if calendar == "lunar" else None
    year, month, day = _parse_birth_date(source or profile.get("birth_date"))
    hour = None if profile.get("birth_hour") is None else int(profile.get("birth_hour", 0))
    minute = None if profile.get("birth_minute") is None else int(profile.get("birth_minute", 0))
    gender = "female" if str(profile.get("gender", "")).lower() in {"女", "female", "f"} else "male"
    return BirthInput(
        calendar,
        year,
        month,
        day,
        hour,
        minute,
        gender,
        is_leap_month=bool(profile.get("is_leap_month", False)),
    )


def get_luck_cycles(
    profile: dict,
    chart: dict | None = None,
    *,
    include_yearly_list: bool = True,
) -> dict:
    try:
        chart = chart or {}
        birth = _birth_from_profile(profile)
        pillars = calculate_four_pillars(birth)
        basis = calculate_dayun(birth, pillars)
        periods = build_dayun_periods(
            pillars.month.text,
            basis,
            pillars.calendar.converted_solar_date.year,
            10,
        )
        dayun_list: list[dict] = []
        for item in periods:
            enriched = dict(item)
            gan = str(enriched["gan"])
            zhi = str(enriched["zhi"])
            enriched.update(
                {
                    "gan_element": STEM_ELEMENTS.get(gan, ""),
                    "zhi_element": BRANCH_MAIN_ELEMENTS.get(zhi, ""),
                    "ten_god": get_ten_god(chart.get("day_master", ""), gan),
                }
            )
            enriched.update(analyze_luck_stage(chart, enriched))
            dayun_list.append(enriched)

        basis_dict = {
            "direction": basis.direction,
            "direction_label": basis.direction_label,
            "boundary_name": basis.boundary_name,
            "boundary_datetime": basis.boundary_datetime.isoformat(sep=" "),
            "interval_seconds": basis.interval_seconds,
            "start_age_years": basis.start_age_years,
            "start_age_months": basis.start_age_months,
            "start_age_days": basis.start_age_days,
            "start_datetime": basis.start_datetime.isoformat(sep=" "),
            "start_text": basis.start_text,
            "time_is_estimated": basis.time_is_estimated,
            "rule_ids": list(basis.rule_ids),
        }
        if chart:
            chart["dayun_basis"] = basis_dict
            attach_chart_facts(chart)
        return {
            "available": True,
            "direction": basis.direction,
            "direction_label": basis.direction_label,
            "start_age": basis.start_age_years,
            "start_year": basis.start_datetime.year,
            "start_month": basis.start_age_months,
            "start_day": basis.start_age_days,
            "start_text": basis.start_text,
            "dayun_basis": basis_dict,
            "dayun_list": dayun_list,
            "yearly_list": _build_yearly_list(chart, 10) if include_yearly_list else [],
            "data_warnings": [],
        }
    except Exception as exc:
        return {
            "available": False,
            "message": "当前资料暂无法完成起运计算，请检查日期与时辰。",
            "debug_message": str(exc),
        }
