"""Compatibility facade backed by the explicit local Four Pillars engine."""

from __future__ import annotations

from core.bazi_calendar_adapter import BirthInput
from core.bazi_constants import BRANCH_MAIN_ELEMENTS, NAYIN_ELEMENT, STEM_ELEMENTS
from core.four_pillars_engine import calculate_four_pillars


def _ensure_float(value, field_name: str = "longitude", default: float = 120.0) -> float:
    """Legacy input normalizer; longitude no longer changes the chart."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except (TypeError, ValueError):
            pass
    return default


def _solar_time_correction(hour: int, minute: int, longitude: float = 120.0) -> tuple[int, int]:
    """Deprecated pure utility kept for old integrations; production charts do not call it."""
    offset = int(round((_ensure_float(longitude) - 120.0) * 4))
    total = int(hour) * 60 + int(minute) + offset
    return (total // 60) % 24, total % 60


def get_zi_time_boundary_note(hour: int, minute: int = 0) -> str:
    """Describe the project's single, explicit 23:00 day-roll rule."""
    try:
        total = int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return ""
    if total >= 23 * 60:
        return "出生钟表时间已到23:00，统一按次日换日；时柱按子时计算。"
    if total < 60:
        return "出生钟表时间在00:00-00:59，日柱按当前公历日，时柱按子时计算。"
    return ""


def _legacy_pillar_fields(prefix: str, pillar) -> dict[str, str]:
    text = pillar.text if pillar is not None else ""
    gan = pillar.gan if pillar is not None else ""
    zhi = pillar.zhi if pillar is not None else ""
    return {
        f"{prefix}_pillar": text,
        f"{prefix}_gan": gan,
        f"{prefix}_zhi": zhi,
        f"{prefix}_na_yin" if prefix != "hour" else "time_na_yin": NAYIN_ELEMENT.get(text, ""),
        f"{prefix}_wu_xing" if prefix != "hour" else "time_wu_xing": (
            f"{STEM_ELEMENTS.get(gan, '')}{BRANCH_MAIN_ELEMENTS.get(zhi, '')}"
        ),
    }


def get_lunar_eight_char(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    longitude: float = 120.0,
    **extra,
) -> dict:
    """Return the historical dictionary shape without using the legacy chart calculator."""
    try:
        result = calculate_four_pillars(
            BirthInput("solar", int(year), int(month), int(day), int(hour), int(minute), "male")
        )
        payload = {
            "time_mode": "china_standard",
            "original_longitude": None,
            "true_solar_time_applied": False,
            "original_birth_hour": int(hour),
            "original_birth_minute": int(minute),
            "adjusted_birth_hour": int(hour),
            "adjusted_birth_minute": int(minute),
            "zi_time_boundary_note": get_zi_time_boundary_note(hour, minute),
            "solar": f"{int(year):04d}-{int(month):02d}-{int(day):02d} {int(hour):02d}:{int(minute):02d}:00",
            "lunar_text": result.calendar.lunar_text,
            "day_master": result.day.gan,
            "year_xun_kong": "",
            "month_xun_kong": "",
            "day_xun_kong": "",
            "time_xun_kong": "",
            "year_di_shi": "",
            "month_di_shi": "",
            "day_di_shi": "",
            "time_di_shi": "",
            "ming_gong": "",
            "shen_gong": "",
            "tai_yuan": "",
            "tai_xi": "",
            "pillar_evidence": result.evidence.public_text(),
        }
        payload.update(_legacy_pillar_fields("year", result.year))
        payload.update(_legacy_pillar_fields("month", result.month))
        payload.update(_legacy_pillar_fields("day", result.day))
        payload.update(_legacy_pillar_fields("hour", result.hour))
        payload["hour_pillar"] = result.hour.text if result.hour is not None else ""
        payload["hour_gan"] = result.hour.gan if result.hour is not None else ""
        payload["hour_zhi"] = result.hour.zhi if result.hour is not None else ""
        return payload
    except Exception as exc:
        return {"error": f"日期不合法或排盘失败：{exc}"}
