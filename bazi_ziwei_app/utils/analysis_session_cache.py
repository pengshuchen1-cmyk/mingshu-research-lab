"""Session-scoped caches for expensive, privacy-sensitive analysis results."""

from __future__ import annotations

import hashlib
import json
from collections.abc import MutableMapping

from core.monthly_engine import analyze_monthly_fortune
from core.monthly_event_activation_bridge import build_year_monthly_event_results
from core.yearly_engine import analyze_yearly_fortune


YEAR_ANALYSIS_KEY = "current_year_analysis_key"
YEARLY_DATA_KEY = "current_yearly_data"
MONTHLY_DATA_KEY = "current_monthly_data"
MONTHLY_EVENTS_KEY = "current_monthly_event_results"


def chart_analysis_fingerprint(chart: dict) -> str:
    """Return an anonymous stable key derived only from calculation results."""
    existing = str(chart.get("chart_fingerprint_v2") or "").strip()
    if existing:
        return existing

    pillars = chart.get("pillars", {}) if isinstance(chart.get("pillars"), dict) else {}
    strength = (
        chart.get("day_master_strength", {})
        if isinstance(chart.get("day_master_strength"), dict)
        else {}
    )
    payload = {
        "pillars": [
            str((pillars.get(position) or {}).get("pillar") or "")
            for position in ("year", "month", "day", "hour")
        ],
        "day_master": str(chart.get("day_master") or ""),
        "strength": str(strength.get("strength") or ""),
        "favorable": list(strength.get("favorable_elements") or []),
        "unfavorable": list(strength.get("unfavorable_elements") or []),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _luck_analysis_fingerprint(luck_data: dict | None) -> str:
    """Hash only the luck-cycle facts consumed by year and event analysis."""
    if not isinstance(luck_data, dict) or not luck_data.get("available"):
        return "unavailable"
    periods = []
    for item in luck_data.get("dayun_list", []):
        if not isinstance(item, dict):
            continue
        periods.append(
            {
                "pillar": str(item.get("pillar") or ""),
                "start_year": item.get("start_year"),
                "end_year": item.get("end_year"),
                "start_date": str(item.get("start_date") or ""),
            }
        )
    encoded = json.dumps(
        periods,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def year_analysis_key(
    chart: dict,
    target_year: int,
    version: str,
    luck_data: dict | None = None,
) -> str:
    """Build a versioned session key without retaining birth data."""
    return ":".join(
        (
            version,
            chart_analysis_fingerprint(chart),
            str(int(target_year)),
            _luck_analysis_fingerprint(luck_data),
        )
    )


def get_or_build_year_analysis(
    state: MutableMapping,
    chart: dict,
    target_year: int,
    luck_data: dict | None,
    *,
    version: str,
) -> tuple[dict, list[dict], list[dict]]:
    """Reuse one complete year analysis until chart, year, or version changes."""
    key = year_analysis_key(chart, target_year, version, luck_data)
    yearly = state.get(YEARLY_DATA_KEY)
    monthly = state.get(MONTHLY_DATA_KEY)
    events = state.get(MONTHLY_EVENTS_KEY)
    if (
        state.get(YEAR_ANALYSIS_KEY) == key
        and isinstance(yearly, dict)
        and isinstance(monthly, list)
        and isinstance(events, list)
    ):
        return yearly, monthly, events

    monthly = analyze_monthly_fortune(chart, int(target_year))
    yearly = analyze_yearly_fortune(
        chart,
        int(target_year),
        luck_data,
        monthly_data=monthly,
    )
    events = build_year_monthly_event_results(
        chart,
        monthly,
        yearly,
        luck_data,
    )
    state[YEAR_ANALYSIS_KEY] = key
    state[YEARLY_DATA_KEY] = yearly
    state[MONTHLY_DATA_KEY] = monthly
    state[MONTHLY_EVENTS_KEY] = events
    return yearly, monthly, events


def clear_year_analysis(state: MutableMapping) -> None:
    """Remove only the current session's derived year-analysis values."""
    for key in (
        YEAR_ANALYSIS_KEY,
        YEARLY_DATA_KEY,
        MONTHLY_DATA_KEY,
        MONTHLY_EVENTS_KEY,
    ):
        state.pop(key, None)
