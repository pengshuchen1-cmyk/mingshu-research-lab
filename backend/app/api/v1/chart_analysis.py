"""Migrated Bazi interpretation, luck-cycle and Jiazi APIs."""

from __future__ import annotations

from copy import deepcopy
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from ...analysis.chart_type import classify_chart
from ...analysis.life_assessment import life_overview
from ...analysis.life_overview_engine import analyze_life_overview
from ...analysis.luck_engine import get_luck_cycles
from ...analysis.sixty_jiazi import get_jiazi_by_pillar, get_jiazi_by_year, load_sixty_jiazi
from ...analysis.useful_god_engine import analyze_useful_god
from ...chart_domain import owned_profile_chart, profile_payload
from ...database import DBSession
from ...domain_schemas import (
    ChartInterpretationOut,
    ChartSixtyJiaziOut,
    LuckCyclesOut,
    SixtyJiaziListOut,
)
from ...errors import APIError, Errors
from ...reports.bazi_report import generate_basic_bazi_report
from ...reports.five_element_deep_report import generate_five_element_deep_report
from ...reports.sixty_jiazi_report import (
    build_four_pillar_jiazi_cards,
    compare_nayin_with_chart_elements,
)
from ...security import CurrentUser

router = APIRouter(tags=["chart-analysis"])


@router.get(
    "/chart-profiles/{profile_id}/analysis",
    response_model=ChartInterpretationOut,
)
async def get_chart_interpretation(profile_id: str, user: CurrentUser, db: DBSession):
    """返回八字类型、命盘总览、五行喜忌和基础白话解读。"""
    _, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    chart = deepcopy(stored_chart.chart_json)

    def build() -> dict:
        return {
            "profile_id": profile_id,
            "chart_fingerprint": stored_chart.chart_fingerprint,
            "chart_type": classify_chart(chart),
            "basic_report": generate_basic_bazi_report(chart),
            "life_assessment": life_overview(chart),
            "life_overview": analyze_life_overview(chart),
            "five_elements": generate_five_element_deep_report(chart),
            "useful_god": analyze_useful_god(chart),
        }

    try:
        return await run_in_threadpool(build)
    except (KeyError, TypeError, ValueError, RuntimeError):
        raise APIError(Errors.CHART_ANALYSIS_UNAVAILABLE) from None


@router.get(
    "/chart-profiles/{profile_id}/luck-cycles",
    response_model=LuckCyclesOut,
)
async def get_chart_luck_cycles(profile_id: str, user: CurrentUser, db: DBSession):
    """返回起运依据、十步完整大运和从当前年开始的未来十年流年。"""
    profile, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    chart = deepcopy(stored_chart.chart_json)
    result = await run_in_threadpool(get_luck_cycles, profile_payload(profile), chart)
    if not result.get("available"):
        raise APIError(Errors.LUCK_CYCLES_UNAVAILABLE)
    return {
        "profile_id": profile_id,
        "chart_fingerprint": stored_chart.chart_fingerprint,
        **result,
    }


@router.get("/knowledge/sixty-jiazi", response_model=SixtyJiaziListOut)
async def list_sixty_jiazi(
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    pillar: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=60)] = 60,
):
    """按年份、干支或分页查询六十甲子知识；该接口无需登录。"""
    if year is not None and pillar is not None:
        raise APIError(Errors.SIXTY_JIAZI_QUERY_CONFLICT)
    if year is not None:
        items = [get_jiazi_by_year(year)]
    elif pillar is not None:
        item = get_jiazi_by_pillar(pillar)
        if item is None:
            raise APIError(Errors.SIXTY_JIAZI_NOT_FOUND)
        items = [item]
    else:
        items = load_sixty_jiazi()
    return {
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "items": items[offset : offset + limit],
    }


@router.get(
    "/chart-profiles/{profile_id}/sixty-jiazi",
    response_model=ChartSixtyJiaziOut,
)
async def get_chart_sixty_jiazi(profile_id: str, user: CurrentUser, db: DBSession):
    """返回当前命盘四柱各自的六十甲子卡片和纳音五行对照。"""
    _, stored_chart = await owned_profile_chart(db, profile_id, user.id)
    chart = deepcopy(stored_chart.chart_json)
    return {
        "profile_id": profile_id,
        "chart_fingerprint": stored_chart.chart_fingerprint,
        "pillar_cards": await run_in_threadpool(build_four_pillar_jiazi_cards, chart),
        "nayin_comparison": await run_in_threadpool(compare_nayin_with_chart_elements, chart),
    }
