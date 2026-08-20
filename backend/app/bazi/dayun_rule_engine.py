"""Explicit dayun direction, start-age and ten-year period rules."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from .bazi_calendar_adapter import BirthInput, jie_boundaries, normalize_birth_input
from .bazi_constants import EARTHLY_BRANCHES, HEAVENLY_STEMS
from .four_pillars_engine import FourPillarsResult, calculate_four_pillars


@dataclass(frozen=True)
class DayunBasis:
    direction: str
    direction_label: str
    boundary_name: str
    boundary_datetime: datetime
    interval_seconds: int
    start_age_years: int
    start_age_months: int
    start_age_days: int
    start_datetime: datetime
    start_text: str
    time_is_estimated: bool
    rule_ids: tuple[str, ...]


def interval_to_start_age(interval_seconds: int) -> tuple[int, int, int]:
    total_days = max(0, interval_seconds) / 86400
    total_months = total_days * 4
    years = int(total_months // 12)
    remaining_months = total_months - years * 12
    months = int(remaining_months)
    days = round((remaining_months - months) * 30)
    if days == 30:
        months += 1
        days = 0
    if months == 12:
        years += 1
        months = 0
    return years, months, days


def _nearby_jie(at: datetime) -> tuple[object, ...]:
    values = (
        jie_boundaries(at.year - 1)
        + jie_boundaries(at.year)
        + jie_boundaries(at.year + 1)
    )
    return tuple(sorted(values, key=lambda item: item.at))


def calculate_dayun(
    birth: BirthInput,
    pillars: FourPillarsResult | None = None,
) -> DayunBasis:
    pillars = pillars or calculate_four_pillars(birth)
    calendar = normalize_birth_input(birth)
    at = calendar.civil_datetime
    time_is_estimated = at is None
    if at is None:
        at = datetime.combine(calendar.converted_solar_date, datetime.min.time()) + timedelta(hours=12)

    yang_year = HEAVENLY_STEMS.index(pillars.year.gan) % 2 == 0
    forward = (birth.gender == "male" and yang_year) or (
        birth.gender == "female" and not yang_year
    )
    direction = "forward" if forward else "reverse"
    candidates = _nearby_jie(at)
    if forward:
        boundary = min((item for item in candidates if item.at >= at), key=lambda item: item.at)
    else:
        boundary = max((item for item in candidates if item.at <= at), key=lambda item: item.at)
    interval_seconds = int(abs((boundary.at - at).total_seconds()))
    years, months, days = interval_to_start_age(interval_seconds)
    age_years = years + months / 12 + days / 360
    start_datetime = at + timedelta(days=age_years * 365.2425)
    direction_label = "顺排" if forward else "逆排"
    start_text = (
        ("时辰不详，暂按12:00估算；" if time_is_estimated else "")
        +
        f"{direction_label}，取{boundary.name}（{boundary.at:%Y-%m-%d %H:%M:%S}）折算，"
        f"约{years}年{months}个月{days}天起运（约{start_datetime:%Y-%m-%d}）。"
    )
    return DayunBasis(
        direction=direction,
        direction_label=direction_label,
        boundary_name=boundary.name,
        boundary_datetime=boundary.at,
        interval_seconds=interval_seconds,
        start_age_years=years,
        start_age_months=months,
        start_age_days=days,
        start_datetime=start_datetime,
        start_text=start_text,
        time_is_estimated=time_is_estimated,
        rule_ids=("DAYUN-DIRECTION", "DAYUN-START-DIV3"),
    )


def sixty_jiazi() -> tuple[str, ...]:
    return tuple(
        f"{HEAVENLY_STEMS[index % 10]}{EARTHLY_BRANCHES[index % 12]}"
        for index in range(60)
    )


def build_dayun_periods(
    month_pillar: str,
    basis: DayunBasis,
    birth_year: int,
    count: int = 10,
) -> list[dict[str, int | str]]:
    cycle = sixty_jiazi()
    month_index = cycle.index(month_pillar)
    step = 1 if basis.direction == "forward" else -1
    initial_age = basis.start_age_years
    if basis.start_age_months or basis.start_age_days:
        initial_age = math.floor(
            basis.start_age_years
            + basis.start_age_months / 12
            + basis.start_age_days / 360
        )
    periods: list[dict[str, int | str]] = []
    for index in range(count):
        pillar = cycle[(month_index + step * (index + 1)) % 60]
        start_age = initial_age + index * 10
        target_year = basis.start_datetime.year + index * 10
        try:
            period_start = basis.start_datetime.replace(year=target_year)
        except ValueError:
            period_start = basis.start_datetime.replace(year=target_year, day=28)
        next_year = period_start.year + 10
        try:
            next_start = period_start.replace(year=next_year)
        except ValueError:
            next_start = period_start.replace(year=next_year, day=28)
        periods.append(
            {
                "index": index + 1,
                "pillar": pillar,
                "gan": pillar[0],
                "zhi": pillar[1],
                "start_age": start_age,
                "end_age": start_age + 9,
                "start_year": period_start.year,
                "end_year": period_start.year + 9,
                "start_date": period_start.date().isoformat(),
                "end_date": next_start.date().isoformat(),
            }
        )
    return periods
