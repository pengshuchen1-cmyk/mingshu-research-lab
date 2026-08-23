"""Shared database access and profile projections for chart-domain APIs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .errors import APIError, Errors
from .models import BaziChart, BirthProfile


async def owned_profile_chart(
    db: AsyncSession,
    profile_id: str,
    user_id: str,
) -> tuple[BirthProfile, BaziChart]:
    """Load an owned profile and its stored chart without leaking foreign IDs."""
    row = (
        await db.execute(
            select(BirthProfile, BaziChart)
            .join(BaziChart, BaziChart.profile_id == BirthProfile.id)
            .where(BirthProfile.id == profile_id, BirthProfile.user_id == user_id)
        )
    ).one_or_none()
    if row is not None:
        return row[0], row[1]
    profile_exists = (
        await db.execute(
            select(BirthProfile.id).where(
                BirthProfile.id == profile_id,
                BirthProfile.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if profile_exists is None:
        raise APIError(Errors.BIRTH_PROFILE_NOT_FOUND)
    raise APIError(Errors.CHART_NOT_FOUND)


def profile_payload(profile: BirthProfile, *, use_solar_date: bool = False) -> dict:
    """Project an ORM profile into the legacy-compatible pure-engine input."""
    birth_date = profile.solar_birth_date.isoformat() if use_solar_date else profile.birth_date
    return {
        "id": profile.id,
        "name": profile.name,
        "gender": profile.gender,
        "calendar_type": "solar" if use_solar_date else profile.calendar_type,
        "birth_date": birth_date,
        "birth_hour": profile.birth_hour,
        "birth_minute": profile.birth_minute,
        "birth_place": profile.birth_place,
        "is_leap_month": False if use_solar_date else profile.is_leap_month,
        "time_label": profile.time_label,
    }
