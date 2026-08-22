"""Authenticated personal fortune endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, cast
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from ...database import DBSession
from ...errors import APIError, Errors
from ...models import BaziChart, BirthProfile
from ...personal_fortune import FortuneProfileInput, build_personal_fortune
from ...schemas import PersonalFortuneOut
from ...security import CurrentUser

router = APIRouter(prefix="/chart-profiles", tags=["fortunes"])
SHANGHAI_TIMEZONE = ZoneInfo("Asia/Shanghai")


@router.get("/{profile_id}/fortune", response_model=PersonalFortuneOut)
async def get_personal_fortune(
    profile_id: str,
    user: CurrentUser,
    db: DBSession,
    target_year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
):
    """Generate personal yearly and 12-month fortune from an owned stored chart."""
    row = (
        await db.execute(
            select(BirthProfile, BaziChart)
            .join(BaziChart, BaziChart.profile_id == BirthProfile.id)
            .where(
                BirthProfile.id == profile_id,
                BirthProfile.user_id == user.id,
            )
        )
    ).one_or_none()
    if row is None:
        profile_exists = (
            await db.execute(
                select(BirthProfile.id).where(
                    BirthProfile.id == profile_id,
                    BirthProfile.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if profile_exists is None:
            raise APIError(Errors.BIRTH_PROFILE_NOT_FOUND)
        raise APIError(Errors.CHART_NOT_FOUND)

    profile, chart = row
    profile_input = FortuneProfileInput(
        calendar_type=cast(Literal["solar", "lunar"], profile.calendar_type),
        birth_date=profile.birth_date,
        birth_hour=profile.birth_hour,
        birth_minute=profile.birth_minute,
        gender=cast(Literal["男", "女"], profile.gender),
        is_leap_month=profile.is_leap_month,
    )
    year = target_year or datetime.now(SHANGHAI_TIMEZONE).year
    try:
        result = await run_in_threadpool(
            build_personal_fortune,
            profile.id,
            chart.chart_fingerprint,
            profile_input,
            chart.chart_json,
            year,
        )
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.PERSONAL_FORTUNE_UNAVAILABLE) from None
    return PersonalFortuneOut.model_validate(result)
