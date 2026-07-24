"""Pure birth-input preview contract backed by the authoritative chart engine."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping

from core.bazi_engine import build_bazi_chart
from utils.validators import validate_profile


CHINESE_MONTHS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二")
CHINESE_DAYS = (
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
)
TRADITIONAL_TIMES = {
    "子时（23:00–23:59）": (23, 30),
    "子时（00:00–00:59）": (0, 30),
    "丑时": (2, 0),
    "寅时": (4, 0),
    "卯时": (6, 0),
    "辰时": (8, 0),
    "巳时": (10, 0),
    "午时": (12, 0),
    "未时": (14, 0),
    "申时": (16, 0),
    "酉时": (18, 0),
    "戌时": (20, 0),
    "亥时": (22, 0),
}


def traditional_time(label: str) -> tuple[int, int, str]:
    try:
        hour, minute = TRADITIONAL_TIMES[label]
    except KeyError as exc:
        raise ValueError("请选择有效的传统时辰。") from exc
    return hour, minute, label


@dataclass(frozen=True)
class BirthFormInput:
    name: str
    gender: str
    calendar: Literal["solar", "lunar"]
    year: int
    month: int
    day: int
    hour: int | None
    minute: int | None
    is_leap_month: bool = False
    birth_place: str = ""
    time_label: str = "精确时间"

    def to_profile(self) -> dict:
        source_date = f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        profile = {
            "name": self.name.strip() or "访客",
            "gender": self.gender,
            "calendar_type": self.calendar,
            "birth_date": source_date,
            "birth_hour": self.hour,
            "birth_minute": self.minute,
            "birth_place": self.birth_place.strip(),
            "is_leap_month": bool(self.is_leap_month and self.calendar == "lunar"),
            "use_solar_time": False,
            "use_true_solar_time": False,
            "birth_longitude": None,
            "time_mode": "china_standard",
        }
        if self.calendar == "lunar":
            profile["lunar_birth_date"] = source_date
        return profile

    def fingerprint(self) -> str:
        payload = json.dumps(
            {"profile": self.to_profile(), "time_label": self.time_label},
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BirthPreview:
    profile: Mapping[str, Any]
    chart: Mapping[str, Any]
    input_text: str
    solar_datetime: str
    pillars: tuple[str, str, str, str]
    calculation_basis: str
    input_fingerprint: str
    chart_fingerprint: str


def _freeze(value: Any) -> Any:
    """Recursively freeze preview data without changing engine input types."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _input_text(value: BirthFormInput) -> str:
    if value.calendar == "solar":
        prefix = f"公历{value.year}年{value.month}月{value.day}日"
    else:
        leap = "闰" if value.is_leap_month else ""
        prefix = (
            f"农历{value.year}年{leap}{CHINESE_MONTHS[value.month - 1]}月"
            f"{CHINESE_DAYS[value.day - 1]}"
        )
        prefix += "，闰月" if value.is_leap_month else "，非闰月"
    return f"{prefix}，{value.gender}，{value.time_label}"


def build_birth_preview(value: BirthFormInput) -> BirthPreview:
    profile = value.to_profile()
    ok, message = validate_profile(profile)
    if not ok:
        if value.calendar == "lunar" and "出生日期" in message:
            raise ValueError(f"农历日期无法转换：{message}")
        raise ValueError(message)
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        label = "农历日期" if value.calendar == "lunar" else "出生日期"
        raise ValueError(f"{label}无法转换：{chart['error']}")
    pillars = tuple(
        chart["pillars"][key]["pillar"]
        or ("时柱不详" if key == "hour" else "")
        for key in ("year", "month", "day", "hour")
    )
    time_text = (
        f"{value.hour:02d}:{value.minute:02d}"
        if value.hour is not None and value.minute is not None
        else "时辰不详"
    )
    return BirthPreview(
        profile=_freeze(profile),
        chart=_freeze(chart),
        input_text=_input_text(value),
        solar_datetime=f"{chart['profile']['birth_date']} {time_text}",
        pillars=pillars,
        calculation_basis=chart["pillar_evidence"]["public_text"],
        input_fingerprint=value.fingerprint(),
        chart_fingerprint=chart["chart_fingerprint_v2"],
    )
