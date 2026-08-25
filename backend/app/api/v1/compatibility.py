"""Two-profile compatibility analysis API."""

from __future__ import annotations

from copy import deepcopy
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response
from fastapi.concurrency import run_in_threadpool

from ...analysis.compatibility import analyze_compatibility
from ...analysis.luck_engine import get_luck_cycles
from ...chart_domain import owned_profile_chart, profile_payload
from ...database import DBSession
from ...domain_schemas import CompatibilityIn, CompatibilityOut
from ...errors import APIError, Errors
from ...reports.compatibility_report import (
    build_compatibility_markdown,
    build_compatibility_pdf,
    build_compatibility_text,
)
from ...security import CurrentUser

router = APIRouter(prefix="/compatibility", tags=["compatibility"])
ExportFormat = Literal["markdown", "txt", "pdf"]


async def _compatibility_result(body: CompatibilityIn, user: CurrentUser, db: DBSession):
    profile_1, stored_1 = await owned_profile_chart(db, body.profile_id_1, user.id)
    profile_2, stored_2 = await owned_profile_chart(db, body.profile_id_2, user.id)
    chart_1 = deepcopy(stored_1.chart_json)
    chart_2 = deepcopy(stored_2.chart_json)

    def build() -> dict:
        luck_1 = get_luck_cycles(profile_payload(profile_1), chart_1)
        luck_2 = get_luck_cycles(profile_payload(profile_2), chart_2)
        return analyze_compatibility(chart_1, chart_2, luck_1, luck_2)

    try:
        result = await run_in_threadpool(build)
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.COMPATIBILITY_UNAVAILABLE) from None
    return profile_1, stored_1, profile_2, stored_2, result


@router.post("/analyze", response_model=CompatibilityOut)
async def analyze_owned_profiles(body: CompatibilityIn, user: CurrentUser, db: DBSession):
    """比较当前用户拥有的两个命盘，返回维度评分、互补点、冲突点和建议。"""
    profile_1, stored_1, profile_2, stored_2, result = await _compatibility_result(
        body, user, db
    )
    return {
        "profile_id_1": profile_1.id,
        "profile_id_2": profile_2.id,
        "chart_fingerprint_1": stored_1.chart_fingerprint,
        "chart_fingerprint_2": stored_2.chart_fingerprint,
        "result": result,
    }


@router.post("/export")
async def export_compatibility_report(
    body: CompatibilityIn,
    user: CurrentUser,
    db: DBSession,
    format_: Annotated[ExportFormat, Query(alias="format")] = "markdown",
):
    """下载两个自有档案的合婚结果，支持 Markdown、TXT 和 PDF。"""
    profile_1, _, profile_2, _, result = await _compatibility_result(body, user, db)

    def build() -> tuple[bytes, str, str]:
        if format_ == "markdown":
            return (
                build_compatibility_markdown(result, profile_1.name, profile_2.name).encode("utf-8"),
                "md",
                "text/markdown; charset=utf-8",
            )
        if format_ == "txt":
            return (
                build_compatibility_text(result, profile_1.name, profile_2.name).encode("utf-8"),
                "txt",
                "text/plain; charset=utf-8",
            )
        pdf = build_compatibility_pdf(result, profile_1.name, profile_2.name)
        if not pdf.startswith(b"%PDF-"):
            raise RuntimeError("PDF renderer unavailable")
        return pdf, "pdf", "application/pdf"

    try:
        content, suffix, media_type = await run_in_threadpool(build)
    except (TypeError, ValueError, RuntimeError):
        raise APIError(Errors.REPORT_EXPORT_UNAVAILABLE) from None
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="mingshu-compatibility.{suffix}"'
        },
    )
