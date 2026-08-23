"""Specialized report and report-export APIs."""

from __future__ import annotations

from copy import deepcopy
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response
from fastapi.concurrency import run_in_threadpool

from ...analysis.luck_engine import get_luck_cycles
from ...chart_domain import owned_profile_chart, profile_payload
from ...database import DBSession
from ...domain_schemas import SpecialReportOut
from ...errors import APIError, Errors
from ...reports.bazi_report import generate_basic_bazi_report
from ...reports.career_report import generate_career_report
from ...reports.export_report import (
    build_markdown_report,
    build_pdf_report,
    build_special_markdown,
    build_special_pdf_report,
    build_special_text_report,
    build_text_report,
)
from ...reports.love_report import generate_love_report
from ...reports.wealth_report import generate_wealth_report
from ...security import CurrentUser

router = APIRouter(prefix="/chart-profiles", tags=["reports"])
ReportType = Literal["career", "wealth", "love"]
ExportReportType = Literal["comprehensive", "career", "wealth", "love"]
ExportFormat = Literal["markdown", "txt", "pdf"]


def _special_report(report_type: ReportType, chart: dict, profile: dict) -> dict:
    if report_type == "career":
        return generate_career_report(chart)
    if report_type == "wealth":
        return generate_wealth_report(chart)
    return generate_love_report(chart, profile)


@router.get("/{profile_id}/reports/{report_type}", response_model=SpecialReportOut)
async def get_special_report(
    profile_id: str,
    report_type: ReportType,
    user: CurrentUser,
    db: DBSession,
):
    """按事业、财富或感情类型生成结构化专项报告。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    chart = deepcopy(stored_chart.chart_json)
    report = await run_in_threadpool(
        _special_report, report_type, chart, profile_payload(profile)
    )
    return {
        "profile_id": profile_id,
        "chart_fingerprint": stored_chart.chart_fingerprint,
        "report_type": report_type,
        "report": report,
    }


@router.get("/{profile_id}/reports/{report_type}/export")
async def export_chart_report(
    profile_id: str,
    report_type: ExportReportType,
    user: CurrentUser,
    db: DBSession,
    format_: Annotated[ExportFormat, Query(alias="format")] = "markdown",
):
    """将综合或专项命盘报告下载为 Markdown、TXT 或 PDF。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    profile_data = profile_payload(profile)
    chart = deepcopy(stored_chart.chart_json)

    def build() -> tuple[bytes, str, str]:
        suffix = {"markdown": "md", "txt": "txt", "pdf": "pdf"}[format_]
        media_type = {
            "markdown": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "pdf": "application/pdf",
        }[format_]
        if report_type == "comprehensive":
            basic = generate_basic_bazi_report(chart)
            luck = get_luck_cycles(profile_data, chart)
            if format_ == "markdown":
                payload = build_markdown_report(profile_data, chart, basic, luck)
            elif format_ == "txt":
                payload = build_text_report(profile_data, chart, basic, luck)
            else:
                pdf = build_pdf_report(profile_data, chart, basic, luck)
                if not pdf.startswith(b"%PDF-"):
                    raise RuntimeError("PDF renderer unavailable")
                return pdf, suffix, media_type
        else:
            special = _special_report(report_type, chart, profile_data)
            if format_ == "markdown":
                payload = build_special_markdown(special)
            elif format_ == "txt":
                payload = build_special_text_report(special)
            else:
                pdf = build_special_pdf_report(special)
                if not pdf.startswith(b"%PDF-"):
                    raise RuntimeError("PDF renderer unavailable")
                return pdf, suffix, media_type
        return payload.encode("utf-8"), suffix, media_type

    try:
        content, suffix, media_type = await run_in_threadpool(build)
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.REPORT_EXPORT_UNAVAILABLE) from None
    filename = f"mingshu-{report_type}-{profile_id}.{suffix}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
