"""Ziwei chart, readable life card and report API."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response
from fastapi.concurrency import run_in_threadpool

from ...chart_domain import owned_profile_chart, profile_payload
from ...database import DBSession
from ...domain_schemas import ZiweiOut
from ...errors import APIError, Errors
from ...reports.export_report import (
    build_special_markdown,
    build_special_pdf_report,
    build_special_text_report,
)
from ...reports.ziwei_report import generate_ziwei_report
from ...security import CurrentUser
from ...ziwei.ziwei_engine import build_ziwei_chart
from ...ziwei.ziwei_life_card_engine import analyze_ziwei_life_card

router = APIRouter(prefix="/chart-profiles", tags=["ziwei"])
ExportFormat = Literal["markdown", "txt", "pdf"]


def _build_ziwei(value: dict, profile_id: str, chart_fingerprint: str) -> dict:
    chart = build_ziwei_chart(value)
    if not chart.get("available"):
        raise ValueError("Ziwei chart unavailable")
    return {
        "profile_id": profile_id,
        "chart_fingerprint": chart_fingerprint,
        "chart": chart,
        "life_card": analyze_ziwei_life_card(chart),
        "report": generate_ziwei_report(chart),
    }


@router.get("/{profile_id}/ziwei", response_model=ZiweiOut)
async def get_ziwei_analysis(profile_id: str, user: CurrentUser, db: DBSession):
    """由已确认档案生成紫微十二宫、星曜、四化、大限和白话综合报告。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    # Ziwei's calendar adapter expects a Gregorian date, so use the profile's
    # persisted confirmed solar date for both solar and lunar source profiles.
    value = profile_payload(profile, use_solar_date=True)

    def build() -> dict:
        return _build_ziwei(value, profile_id, stored_chart.chart_fingerprint)

    try:
        return await run_in_threadpool(build)
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.ZIWEI_UNAVAILABLE) from None


@router.get("/{profile_id}/ziwei/export")
async def export_ziwei_analysis(
    profile_id: str,
    user: CurrentUser,
    db: DBSession,
    format_: Annotated[ExportFormat, Query(alias="format")] = "markdown",
):
    """下载紫微综合报告，支持 Markdown、TXT 和 PDF。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    value = profile_payload(profile, use_solar_date=True)

    def build() -> tuple[bytes, str, str]:
        report = _build_ziwei(value, profile_id, stored_chart.chart_fingerprint)["report"]
        if format_ == "markdown":
            return build_special_markdown(report).encode("utf-8"), "md", "text/markdown; charset=utf-8"
        if format_ == "txt":
            return build_special_text_report(report).encode("utf-8"), "txt", "text/plain; charset=utf-8"
        pdf = build_special_pdf_report(report)
        if not pdf.startswith(b"%PDF-"):
            raise RuntimeError("PDF renderer unavailable")
        return pdf, "pdf", "application/pdf"

    try:
        content, suffix, media_type = await run_in_threadpool(build)
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.REPORT_EXPORT_UNAVAILABLE) from None
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="mingshu-ziwei-{profile_id}.{suffix}"'
        },
    )
