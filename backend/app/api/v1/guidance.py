"""Public daily and yearly guidance endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import AfterValidator

from ...guidance import build_today_guidance
from ...schemas import TodayGuidanceOut

router = APIRouter(prefix="/guidance", tags=["guidance"])
MIN_GUIDANCE_DATE = date(1900, 1, 1)
MAX_GUIDANCE_DATE = date(2100, 12, 31)


def _validate_target_date(value: date | None) -> date | None:
    """Keep date validation typed instead of passing dates to numeric Query bounds."""
    if value is not None and not MIN_GUIDANCE_DATE <= value <= MAX_GUIDANCE_DATE:
        raise ValueError("target_date must be between 1900-01-01 and 2100-12-31")
    return value


@router.get("/today", response_model=TodayGuidanceOut)
def today_guidance(
    target_date: Annotated[
        date | None,
        AfterValidator(_validate_target_date),
        Query(
            description="要查看的公历日期（1900-01-01 至 2100-12-31）；省略时按 Asia/Shanghai 的当天计算",
        ),
    ] = None,
    target_year: Annotated[
        int | None,
        Query(
            ge=1900,
            le=2100,
            description="年度建议年份；省略时使用 target_date 所在年份",
        ),
    ] = None,
):
    """返回无需登录和出生资料的公共今日指引与年度节奏。"""
    return build_today_guidance(target_date, target_year)
