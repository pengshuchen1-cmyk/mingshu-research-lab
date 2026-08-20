"""Backend-owned adapter around the deterministic Bazi calculation package."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal

from .bazi.birth_input_preview import BirthFormInput, build_birth_preview


@dataclass(frozen=True, slots=True)
class GeneratedChart:
    chart: dict[str, Any]
    input_fingerprint: str
    chart_fingerprint: str
    engine_version: str
    input_text: str
    solar_datetime: str
    solar_birth_date: date
    pillars: list[str]
    calculation_basis: str


def _mutable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _mutable(item) for key, item in value.items()}
    if isinstance(value, (tuple, frozenset)):
        return [_mutable(item) for item in value]
    return value


def _remove_duplicate_personal_data(chart: dict[str, Any]) -> None:
    """Keep identity fields in BirthProfile only, not in the chart JSON snapshot."""
    profile = chart.get("profile")
    if isinstance(profile, dict):
        profile.pop("name", None)
        profile.pop("birth_place", None)


def _calendar_type(value: object) -> Literal["solar", "lunar"]:
    """Validate and narrow an untyped mapping value to the engine contract."""
    if value == "solar":
        return "solar"
    if value == "lunar":
        return "lunar"
    raise ValueError("calendar_type must be 'solar' or 'lunar'")


def generate_chart(value: Mapping[str, Any]) -> GeneratedChart:
    source_date = str(value["birth_date"])
    year, month, day = (int(part) for part in source_date.split("-"))
    birth_input = BirthFormInput(
        name=str(value["name"]),
        gender=str(value["gender"]),
        calendar=_calendar_type(value["calendar_type"]),
        year=year,
        month=month,
        day=day,
        hour=value.get("birth_hour"),
        minute=value.get("birth_minute"),
        is_leap_month=bool(value.get("is_leap_month", False)),
        birth_place=str(value.get("birth_place", "")),
        time_label=str(value.get("time_label", "精确时间")),
    )
    preview = build_birth_preview(birth_input)
    solar_birth_date = date.fromisoformat(preview.solar_datetime[:10])
    if solar_birth_date > datetime.now(UTC).date():
        raise ValueError("converted solar birth date cannot be in the future")
    chart = _mutable(preview.chart)
    _remove_duplicate_personal_data(chart)
    return GeneratedChart(
        chart=chart,
        input_fingerprint=preview.input_fingerprint,
        chart_fingerprint=preview.chart_fingerprint,
        engine_version=str(chart.get("rule_version", "unknown")),
        input_text=preview.input_text,
        solar_datetime=preview.solar_datetime,
        solar_birth_date=solar_birth_date,
        pillars=list(preview.pillars),
        calculation_basis=preview.calculation_basis,
    )
