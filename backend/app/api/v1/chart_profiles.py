"""Authenticated birth-profile and deterministic chart endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from ...chart_engine import GeneratedChart, generate_chart
from ...config import settings
from ...database import DBSession
from ...errors import APIError, Errors
from ...models import BaziChart, BirthProfile
from ...schemas import (
    BaziChartOut,
    BirthProfileConfirmIn,
    BirthProfileDetailOut,
    BirthProfileIn,
    BirthProfileOut,
    ChartPreviewOut,
)
from ...security import CurrentUser

router = APIRouter(prefix="/chart-profiles", tags=["charts"])


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _edit_state(profile: BirthProfile) -> tuple[datetime | None, bool]:
    if (
        profile.edit_count == 0
        or profile.last_edited_at is None
        or settings.profile_edit_cooldown_days == 0
    ):
        return None, True
    next_edit_at = _utc(profile.last_edited_at) + timedelta(
        days=settings.profile_edit_cooldown_days
    )
    return next_edit_at, datetime.now(UTC) >= next_edit_at


def _profile_out(profile: BirthProfile) -> BirthProfileOut:
    next_edit_at, can_edit = _edit_state(profile)
    return BirthProfileOut.model_validate(profile).model_copy(
        update={"next_edit_at": next_edit_at, "can_edit": can_edit}
    )


def _chart_out(chart: BaziChart) -> BaziChartOut:
    return BaziChartOut(
        id=chart.id,
        profile_id=chart.profile_id,
        input_fingerprint=chart.input_fingerprint,
        chart_fingerprint=chart.chart_fingerprint,
        engine_version=chart.engine_version,
        chart=chart.chart_json,
        generated_at=chart.generated_at,
    )


async def _generate(value: BirthProfileIn) -> GeneratedChart:
    try:
        return await run_in_threadpool(generate_chart, value.model_dump())
    except (TypeError, ValueError, RuntimeError):
        raise APIError(Errors.BIRTH_PROFILE_INVALID) from None


def _confirm(value: BirthProfileConfirmIn, generated: GeneratedChart) -> None:
    if (
        value.expected_input_fingerprint != generated.input_fingerprint
        or value.expected_chart_fingerprint != generated.chart_fingerprint
    ):
        raise APIError(Errors.CHART_CONFIRMATION_MISMATCH)


def _apply_profile_input(
    profile: BirthProfile,
    value: BirthProfileIn,
    generated: GeneratedChart,
) -> None:
    profile.name = value.name.strip()
    profile.gender = value.gender
    profile.calendar_type = value.calendar_type
    profile.birth_date = value.birth_date
    profile.solar_birth_date = generated.solar_birth_date
    profile.birth_hour = value.birth_hour
    profile.birth_minute = value.birth_minute
    profile.birth_place = value.birth_place.strip()
    profile.is_leap_month = value.is_leap_month
    profile.time_label = value.time_label


def _apply_chart(chart: BaziChart, generated: GeneratedChart) -> None:
    chart.input_fingerprint = generated.input_fingerprint
    chart.chart_fingerprint = generated.chart_fingerprint
    chart.engine_version = generated.engine_version
    chart.chart_json = generated.chart
    chart.generated_at = datetime.now(UTC)


async def _owned_profile(db: DBSession, profile_id: str, user_id: str) -> BirthProfile:
    profile = (
        await db.execute(
            select(BirthProfile).where(
                BirthProfile.id == profile_id,
                BirthProfile.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if profile is None:
        raise APIError(Errors.BIRTH_PROFILE_NOT_FOUND)
    return profile


async def _profile_chart(db: DBSession, profile_id: str) -> BaziChart:
    chart = (
        await db.execute(select(BaziChart).where(BaziChart.profile_id == profile_id))
    ).scalar_one_or_none()
    if chart is None:
        raise APIError(Errors.CHART_NOT_FOUND)
    return chart


@router.post("/preview", response_model=ChartPreviewOut)
async def preview_birth_profile(body: BirthProfileIn, _: CurrentUser):
    """Validate birth information and return a deterministic confirmation preview."""
    generated = await _generate(body)
    return ChartPreviewOut(
        input_fingerprint=generated.input_fingerprint,
        chart_fingerprint=generated.chart_fingerprint,
        engine_version=generated.engine_version,
        input_text=generated.input_text,
        solar_datetime=generated.solar_datetime,
        pillars=generated.pillars,
        calculation_basis=generated.calculation_basis,
    )


@router.post("", response_model=BirthProfileDetailOut, status_code=status.HTTP_201_CREATED)
async def create_birth_profile(
    body: BirthProfileConfirmIn,
    user: CurrentUser,
    db: DBSession,
):
    """Rebuild the confirmed preview, then atomically save its profile and chart."""
    generated = await _generate(body)
    _confirm(body, generated)
    profile = BirthProfile(
        user_id=user.id,
        name=body.name.strip(),
        gender=body.gender,
        calendar_type=body.calendar_type,
        birth_date=body.birth_date,
        solar_birth_date=generated.solar_birth_date,
        birth_hour=body.birth_hour,
        birth_minute=body.birth_minute,
        birth_place=body.birth_place.strip(),
        is_leap_month=body.is_leap_month,
        time_label=body.time_label,
    )
    db.add(profile)
    await db.flush()
    chart = BaziChart(profile_id=profile.id)
    _apply_chart(chart, generated)
    db.add(chart)
    await db.commit()
    await db.refresh(profile)
    await db.refresh(chart)
    return BirthProfileDetailOut(profile=_profile_out(profile), chart=_chart_out(chart))


@router.get("", response_model=list[BirthProfileOut])
async def list_birth_profiles(
    user: CurrentUser,
    db: DBSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List only the current user's birth profiles, newest first."""
    profiles = (
        (
            await db.execute(
                select(BirthProfile)
                .where(BirthProfile.user_id == user.id)
                .order_by(BirthProfile.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [_profile_out(profile) for profile in profiles]


@router.get("/{profile_id}", response_model=BirthProfileDetailOut)
async def get_birth_profile(profile_id: str, user: CurrentUser, db: DBSession):
    """Return one owned profile together with its stored chart snapshot."""
    profile = await _owned_profile(db, profile_id, user.id)
    chart = await _profile_chart(db, profile.id)
    return BirthProfileDetailOut(profile=_profile_out(profile), chart=_chart_out(chart))


@router.put("/{profile_id}", response_model=BirthProfileDetailOut)
async def update_birth_profile(
    profile_id: str,
    body: BirthProfileConfirmIn,
    user: CurrentUser,
    db: DBSession,
):
    """Replace birth information after cooldown and atomically regenerate its chart."""
    generated = await _generate(body)
    _confirm(body, generated)
    profile = (
        await db.execute(
            select(BirthProfile)
            .where(BirthProfile.id == profile_id, BirthProfile.user_id == user.id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if profile is None:
        raise APIError(Errors.BIRTH_PROFILE_NOT_FOUND)
    _, can_edit = _edit_state(profile)
    if not can_edit:
        raise APIError(Errors.BIRTH_PROFILE_EDIT_COOLDOWN)
    chart = (
        await db.execute(
            select(BaziChart).where(BaziChart.profile_id == profile.id).with_for_update()
        )
    ).scalar_one_or_none()
    if chart is None:
        chart = BaziChart(profile_id=profile.id)
        db.add(chart)
    _apply_profile_input(profile, body, generated)
    profile.edit_count += 1
    profile.last_edited_at = datetime.now(UTC)
    _apply_chart(chart, generated)
    await db.commit()
    await db.refresh(profile)
    await db.refresh(chart)
    return BirthProfileDetailOut(profile=_profile_out(profile), chart=_chart_out(chart))


@router.get("/{profile_id}/chart", response_model=BaziChartOut)
async def get_birth_chart(profile_id: str, user: CurrentUser, db: DBSession):
    """Return the stored deterministic chart without recalculating on every request."""
    profile = await _owned_profile(db, profile_id, user.id)
    return _chart_out(await _profile_chart(db, profile.id))


@router.post("/{profile_id}/regenerate", response_model=BaziChartOut)
async def regenerate_birth_chart(profile_id: str, user: CurrentUser, db: DBSession):
    """Rebuild a stored profile after a rule-engine upgrade without changing personal data."""
    # Serialize against profile edits. Otherwise a regeneration that read old
    # personal data could overwrite the chart produced by a concurrent edit.
    profile = (
        await db.execute(
            select(BirthProfile)
            .where(BirthProfile.id == profile_id, BirthProfile.user_id == user.id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if profile is None:
        raise APIError(Errors.BIRTH_PROFILE_NOT_FOUND)
    body = BirthProfileIn(
        name=profile.name,
        gender=profile.gender,
        calendar_type=profile.calendar_type,
        birth_date=profile.birth_date,
        birth_hour=profile.birth_hour,
        birth_minute=profile.birth_minute,
        birth_place=profile.birth_place,
        is_leap_month=profile.is_leap_month,
        time_label=profile.time_label,
    )
    generated = await _generate(body)
    chart = (
        await db.execute(
            select(BaziChart)
            .where(BaziChart.profile_id == profile.id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if chart is None:
        raise APIError(Errors.CHART_NOT_FOUND)
    _apply_chart(chart, generated)
    await db.commit()
    await db.refresh(chart)
    return _chart_out(chart)
