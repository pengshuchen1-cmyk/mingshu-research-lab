"""Narrow lunar_python adapter for conversion, day seed and exact Jie times."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from typing import Literal


JIE_NAMES = (
    "小寒",
    "立春",
    "惊蛰",
    "清明",
    "立夏",
    "芒种",
    "小暑",
    "立秋",
    "白露",
    "寒露",
    "立冬",
    "大雪",
)


@dataclass(frozen=True)
class BirthInput:
    calendar: Literal["solar", "lunar"]
    year: int
    month: int
    day: int
    hour: int | None
    minute: int | None
    gender: Literal["male", "female"]
    is_leap_month: bool = False
    time_mode: Literal["china_standard"] = "china_standard"

    def __post_init__(self) -> None:
        if self.calendar not in {"solar", "lunar"}:
            raise ValueError("calendar must be solar or lunar")
        if self.gender not in {"male", "female"}:
            raise ValueError("gender must be male or female")
        if self.time_mode != "china_standard":
            raise ValueError("only china_standard time is supported")
        if (self.hour is None) != (self.minute is None):
            raise ValueError("hour and minute must both be known or unknown")
        if self.hour is not None and not 0 <= self.hour <= 23:
            raise ValueError("hour must be between 0 and 23")
        if self.minute is not None and not 0 <= self.minute <= 59:
            raise ValueError("minute must be between 0 and 59")
        if self.calendar == "solar" and self.is_leap_month:
            raise ValueError("leap month is only valid for lunar input")


@dataclass(frozen=True)
class CalendarEvidence:
    civil_datetime: datetime | None
    converted_solar_date: date
    original_date: date
    source_calendar: str
    is_leap_month: bool
    time_mode_label: str
    lunar_text: str


@dataclass(frozen=True)
class JieBoundary:
    name: str
    at: datetime


def _solar_date(solar: object) -> date:
    return date(int(solar.getYear()), int(solar.getMonth()), int(solar.getDay()))


def _solar_datetime(solar: object) -> datetime:
    return datetime(
        int(solar.getYear()),
        int(solar.getMonth()),
        int(solar.getDay()),
        int(solar.getHour()),
        int(solar.getMinute()),
        int(solar.getSecond()),
    )


def normalize_birth_input(value: BirthInput) -> CalendarEvidence:
    original = date(value.year, value.month, value.day)
    if value.calendar == "lunar":
        from lunar_python import Lunar

        lunar_month = -value.month if value.is_leap_month else value.month
        lunar = Lunar.fromYmdHms(
            value.year,
            lunar_month,
            value.day,
            value.hour or 0,
            value.minute or 0,
            0,
        )
        converted = _solar_date(lunar.getSolar())
    else:
        converted = original

    civil = None
    if value.hour is not None and value.minute is not None:
        civil = datetime(
            converted.year,
            converted.month,
            converted.day,
            value.hour,
            value.minute,
        )
    from lunar_python import Solar

    display_solar = Solar.fromYmdHms(
        converted.year,
        converted.month,
        converted.day,
        value.hour or 0,
        value.minute or 0,
        0,
    )
    lunar_text = str(display_solar.getLunar().toFullString())
    return CalendarEvidence(
        civil_datetime=civil,
        converted_solar_date=converted,
        original_date=original,
        source_calendar=value.calendar,
        is_leap_month=value.is_leap_month,
        time_mode_label="中国标准时间（北京时间）",
        lunar_text=lunar_text,
    )


def day_pillar_seed(day: date) -> tuple[str, str]:
    from lunar_python import Solar

    text = str(Solar.fromYmd(day.year, day.month, day.day).getLunar().getDayInGanZhi())
    if len(text) != 2:
        raise ValueError(f"invalid day pillar seed: {text!r}")
    return text[0], text[1]


@lru_cache(maxsize=32)
def jie_boundaries(year: int) -> tuple[JieBoundary, ...]:
    from lunar_python import Solar

    table = Solar.fromYmd(year, 6, 15).getLunar().getJieQiTable()
    boundaries: list[JieBoundary] = []
    for name in JIE_NAMES:
        solar = table.get(name)
        if solar is None:
            raise ValueError(f"missing Jie boundary: {year} {name}")
        boundary = JieBoundary(name=name, at=_solar_datetime(solar))
        if boundary.at.year != year:
            raise ValueError(f"Jie boundary has wrong year: {name} {boundary.at}")
        boundaries.append(boundary)
    if any(left.at >= right.at for left, right in zip(boundaries, boundaries[1:])):
        raise ValueError(f"Jie boundaries are not ordered for {year}")
    return tuple(boundaries)
