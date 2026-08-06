"""命数研究室微信小程序测试 API。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime
import os
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

os.environ.setdefault("MINGSHU_RUNTIME_MODE", "local")

from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from core.ai_models import AIConfig
from core.ai_orchestrator import answer_question
from core.bazi_engine import build_bazi_chart
from core.birth_input_preview import BirthFormInput, build_birth_preview
from core.compatibility import analyze_compatibility
from core.life_overview_engine import analyze_life_overview
from core.luck_engine import get_luck_cycles
from core.monthly_engine import analyze_monthly_fortune
from core.monthly_event_inference_engine import build_year_monthly_event_results
from core.popular_advice_engine import build_daily_advice, build_yearly_popular_advice
from core.ziwei_engine import build_ziwei_chart
from core.ziwei_readable_engine import build_ziwei_capability_review, build_ziwei_plain_guide
from core.ziwei_sihua_engine import apply_sihua_to_chart, get_sihua_by_year_gan
from core.ziwei_star_engine import get_year_gan_from_profile
from core.yearly_engine import analyze_yearly_fortune
from miniapp_api.models import (
    ArchiveUpdatePayload,
    AskPayload,
    CompatibilityPayload,
    ImportPayload,
    ProfilePayload,
    SettingsPayload,
)
from miniapp_api.presenters import (
    FEATURES,
    acceptance_document,
    bazi_document,
    compatibility_document,
    five_elements_document,
    home_document,
    json_safe,
    luck_document,
    overview_document,
    report_document,
    sixty_jiazi_document,
    yearly_document,
    ziwei_document,
)
from miniapp_api.session_store import store
from report.bazi_report import generate_basic_bazi_report
from report.career_report import generate_career_report
from report.export_report import (
    build_markdown_report,
    build_pdf_report,
    build_special_pdf_report,
    build_special_text_report,
    build_text_report,
)
from report.five_element_deep_report import generate_five_element_deep_report
from report.love_report import generate_love_report
from report.sixty_jiazi_report import build_four_pillar_jiazi_cards, compare_nayin_with_chart_elements
from report.special_report_common import build_special_markdown
from report.wealth_report import generate_wealth_report
from report.ziwei_report import generate_ziwei_report
from utils.backup import backup_database, export_profiles_to_json, import_profiles_from_json
from utils.database import (
    delete_profile,
    get_profile,
    init_db,
    save_profile,
    search_profiles,
    update_chart_and_report,
    update_profile_basic,
    update_profile_birth_info,
)
from utils.validators import validate_profile


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="命数研究室小程序 API",
    description="复用现有 Python 核心的小程序测试适配层。",
    version="1.0.0-test",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _session_id(value: str | None) -> str:
    return (value or "test-session").strip()[:96] or "test-session"


def _session(value: str | None):
    return store.get(_session_id(value))


def _require_chart(value: str | None):
    session = _session(value)
    if not session.chart or session.chart.get("error"):
        raise HTTPException(status_code=409, detail="请先新建或加载一个命盘。")
    return session


def _preview_input(payload: ProfilePayload) -> BirthFormInput:
    try:
        source = date.fromisoformat(payload.birth_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="出生日期格式应为 YYYY-MM-DD。") from exc
    hour = payload.birth_hour if payload.time_known else None
    minute = payload.birth_minute if payload.time_known else None
    return BirthFormInput(
        name=payload.name,
        gender=payload.gender,
        calendar=payload.calendar_type,
        year=source.year,
        month=source.month,
        day=source.day,
        hour=hour,
        minute=minute,
        is_leap_month=payload.is_leap_month,
        birth_place=payload.birth_place,
        time_label="精确时间" if payload.time_known else "时辰不详",
    )


def _profile_from_loaded(loaded: dict) -> dict:
    keys = (
        "name", "gender", "calendar_type", "birth_date", "lunar_birth_date",
        "birth_hour", "birth_minute", "birth_place", "is_leap_month",
        "time_mode", "time_known", "use_solar_time", "note",
    )
    return {key: loaded.get(key) for key in keys if key in loaded}


def _set_current(session, profile: dict, chart: dict, report: dict) -> None:
    session.profile = profile
    session.chart = chart
    session.report = report
    session.chat_history.clear()
    session.touch()


def _special_report(kind: str, chart: dict, profile: dict) -> dict:
    if kind == "career":
        return generate_career_report(chart)
    if kind == "wealth":
        return generate_wealth_report(chart)
    if kind == "love":
        return generate_love_report(chart, profile)
    raise HTTPException(status_code=404, detail="未知专项报告。")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "mingshu-miniapp-api", "mode": "test", "time": datetime.now().isoformat()}


@app.get("/api/v1/home")
def home() -> dict:
    return home_document(build_daily_advice(), build_yearly_popular_advice())


@app.get("/api/v1/features")
def features() -> dict:
    return {"items": FEATURES}


@app.post("/api/v1/profile/preview")
def preview_profile(payload: ProfilePayload) -> dict:
    try:
        preview = build_birth_preview(_preview_input(payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return json_safe({
        "input_text": preview.input_text,
        "solar_datetime": preview.solar_datetime,
        "pillars": preview.pillars,
        "calculation_basis": preview.calculation_basis,
        "input_fingerprint": preview.input_fingerprint,
        "chart_fingerprint": preview.chart_fingerprint,
    })


@app.post("/api/v1/profile/chart")
def create_chart(
    payload: ProfilePayload,
    save: bool = Query(default=False),
    x_session_id: str | None = Header(default=None),
) -> dict:
    profile = payload.to_profile()
    ok, message = validate_profile(profile)
    if not ok:
        raise HTTPException(status_code=422, detail=message)
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        raise HTTPException(status_code=422, detail=chart["error"])
    normalized_profile = chart.get("profile", profile)
    report = generate_basic_bazi_report(chart)
    session = _session(x_session_id)
    _set_current(session, normalized_profile, chart, report)
    profile_id = save_profile(normalized_profile, chart, report) if save else None
    return {"ok": True, "profile_id": profile_id, "document": bazi_document(normalized_profile, chart, report)}


@app.get("/api/v1/session")
def session_status(x_session_id: str | None = Header(default=None)) -> dict:
    session = _session(x_session_id)
    return {
        "has_profile": bool(session.profile),
        "has_chart": bool(session.chart and not session.chart.get("error")),
        "profile": json_safe(session.profile) if session.profile else None,
        "settings": json_safe(session.settings),
        "chat_count": len(session.chat_history),
    }


@app.delete("/api/v1/session")
def clear_session(x_session_id: str | None = Header(default=None)) -> dict:
    store.clear(_session_id(x_session_id))
    return {"ok": True}


@app.get("/api/v1/feature/{feature_key}")
def feature(
    feature_key: str,
    year: int = Query(default=date.today().year, ge=1900, le=2200),
    x_session_id: str | None = Header(default=None),
) -> dict:
    if feature_key == "acceptance":
        profiles = [
            {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海"},
            {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京"},
            {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州"},
            {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都"},
            {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州"},
        ]
        samples = []
        for profile in profiles:
            chart = build_bazi_chart(profile)
            samples.append({
                "profile": profile,
                "chart": chart,
                "overview": analyze_life_overview(chart),
                "yearly": analyze_yearly_fortune(chart, year),
            })
        return acceptance_document(samples)

    session = _require_chart(x_session_id)
    chart = session.chart
    profile = session.profile or chart.get("profile", {})
    report = session.report or generate_basic_bazi_report(chart)
    luck = get_luck_cycles(profile, chart)

    if feature_key == "bazi":
        return bazi_document(profile, chart, report)
    if feature_key == "overview":
        return overview_document(profile, chart, analyze_life_overview(chart, luck))
    if feature_key == "five-elements":
        return five_elements_document(chart, generate_five_element_deep_report(chart, luck))
    if feature_key == "luck":
        return luck_document(profile, chart, luck)
    if feature_key == "yearly":
        yearly = analyze_yearly_fortune(chart, year, luck)
        monthly = analyze_monthly_fortune(chart, year)
        events = build_year_monthly_event_results(chart, monthly, yearly, luck)
        return yearly_document(chart, yearly, monthly, events)
    if feature_key in {"career", "wealth", "love"}:
        names = {"career": "事业专项报告", "wealth": "财运专项报告", "love": "婚恋专项报告"}
        return report_document(_special_report(feature_key, chart, profile), names[feature_key], f"SPECIAL REPORT · {feature_key.upper()}")
    if feature_key == "ziwei":
        ziwei = build_ziwei_chart(profile)
        year_gan = get_year_gan_from_profile(profile)
        sihua = apply_sihua_to_chart(ziwei, get_sihua_by_year_gan(year_gan))
        guide = build_ziwei_plain_guide(ziwei, sihua.get("sihua_by_palace", {}))
        capability = build_ziwei_capability_review(ziwei)
        return ziwei_document(profile, ziwei, guide, capability, generate_ziwei_report(ziwei), sihua)
    if feature_key == "sixty-jiazi":
        return sixty_jiazi_document(chart, build_four_pillar_jiazi_cards(chart), compare_nayin_with_chart_elements(chart))
    if feature_key == "report":
        return report_document(report, "简明报告", "REPORT · SUMMARY")
    raise HTTPException(status_code=404, detail="未知功能页面。")


@app.post("/api/v1/ai/ask")
def ask(payload: AskPayload, x_session_id: str | None = Header(default=None)) -> dict:
    session = _require_chart(x_session_id)
    result = answer_question(
        session.chart,
        payload.question,
        session.chat_history[-12:],
        config=AIConfig.from_environment(),
        session_id=_session_id(x_session_id),
        request_id=uuid4().hex,
    )
    session.chat_history.extend([
        {"role": "user", "content": payload.question.strip()},
        {"role": "assistant", "content": result.answer},
    ])
    session.chat_history = session.chat_history[-20:]
    session.touch()
    return json_safe({
        "answer": result.answer,
        "sections": result.sections,
        "chart_evidence": result.chart_evidence,
        "rule_evidence": result.rule_evidence,
        "timing_conditions": result.timing_conditions,
        "practical_advice": result.practical_advice,
        "uncertainty": result.uncertainty,
        "source": result.source,
        "provider": result.provider,
        "degraded_reason": result.degraded_reason,
        "retryable": result.retryable,
    })


@app.get("/api/v1/ai/history")
def ai_history(x_session_id: str | None = Header(default=None)) -> dict:
    return {"items": json_safe(_session(x_session_id).chat_history)}


def _resolve_compat_profile(profile_id: int | None, payload: ProfilePayload | None) -> tuple[dict, dict]:
    if profile_id is not None:
        loaded = get_profile(profile_id)
        if not loaded:
            raise HTTPException(status_code=404, detail=f"未找到档案 {profile_id}。")
        profile = _profile_from_loaded(loaded)
        chart = loaded.get("chart") or build_bazi_chart(profile)
        return profile, chart
    if payload is None:
        raise HTTPException(status_code=422, detail="请选择档案或填写双方资料。")
    profile = payload.to_profile()
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        raise HTTPException(status_code=422, detail=chart["error"])
    return chart.get("profile", profile), chart


@app.post("/api/v1/compatibility")
def compatibility(payload: CompatibilityPayload) -> dict:
    first_profile, first_chart = _resolve_compat_profile(payload.first_profile_id, payload.first_profile)
    second_profile, second_chart = _resolve_compat_profile(payload.second_profile_id, payload.second_profile)
    if payload.first_profile_id is not None and payload.first_profile_id == payload.second_profile_id:
        raise HTTPException(status_code=422, detail="请选择两个不同的命盘。")
    first_luck = get_luck_cycles(first_profile, first_chart)
    second_luck = get_luck_cycles(second_profile, second_chart)
    result = analyze_compatibility(first_chart, second_chart, first_luck, second_luck)
    return compatibility_document(result, first_profile.get("name", "甲方"), second_profile.get("name", "乙方"))


@app.get("/api/v1/archives")
def archives(keyword: str = "", gender: str = "全部") -> dict:
    return {"items": json_safe(search_profiles(keyword=keyword, gender=gender))}


@app.post("/api/v1/archives/current")
def save_current(x_session_id: str | None = Header(default=None)) -> dict:
    session = _require_chart(x_session_id)
    profile_id = save_profile(session.profile, session.chart, session.report or generate_basic_bazi_report(session.chart))
    return {"ok": True, "profile_id": profile_id}


@app.post("/api/v1/archives/{profile_id}/load")
def load_archive(profile_id: int, x_session_id: str | None = Header(default=None)) -> dict:
    loaded = get_profile(profile_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="未找到该命盘。")
    profile = _profile_from_loaded(loaded)
    chart = loaded.get("chart") or build_bazi_chart(profile)
    report = loaded.get("report") or generate_basic_bazi_report(chart)
    _set_current(_session(x_session_id), profile, chart, report)
    return {"ok": True, "document": bazi_document(profile, chart, report)}


@app.patch("/api/v1/archives/{profile_id}")
def update_archive(profile_id: int, payload: ArchiveUpdatePayload) -> dict:
    if not get_profile(profile_id):
        raise HTTPException(status_code=404, detail="未找到该命盘。")
    update_profile_basic(profile_id, payload.name, payload.birth_place, payload.note)
    return {"ok": True}


@app.put("/api/v1/archives/{profile_id}/chart")
def rebuild_archive(profile_id: int, payload: ProfilePayload, x_session_id: str | None = Header(default=None)) -> dict:
    if not get_profile(profile_id):
        raise HTTPException(status_code=404, detail="未找到该命盘。")
    profile = payload.to_profile()
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        raise HTTPException(status_code=422, detail=chart["error"])
    profile = chart.get("profile", profile)
    report = generate_basic_bazi_report(chart)
    update_profile_birth_info(profile_id, profile)
    update_chart_and_report(profile_id, chart, report)
    _set_current(_session(x_session_id), profile, chart, report)
    return {"ok": True, "document": bazi_document(profile, chart, report)}


@app.delete("/api/v1/archives/{profile_id}")
def remove_archive(profile_id: int) -> dict:
    if not get_profile(profile_id):
        raise HTTPException(status_code=404, detail="未找到该命盘。")
    delete_profile(profile_id)
    return {"ok": True}


@app.get("/api/v1/backup", response_class=PlainTextResponse)
def backup() -> str:
    return export_profiles_to_json()


@app.post("/api/v1/backup/import")
def import_backup(payload: ImportPayload) -> dict:
    result = import_profiles_from_json(payload.payload)
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.get("/api/v1/backup/database")
def backup_database_file() -> FileResponse:
    result = backup_database()
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("message", "数据库备份失败。"))
    return FileResponse(
        result["path"],
        media_type="application/vnd.sqlite3",
        filename=Path(result["path"]).name,
    )


@app.get("/api/v1/settings")
def get_settings(x_session_id: str | None = Header(default=None)) -> dict:
    return json_safe(_session(x_session_id).settings)


@app.put("/api/v1/settings")
def put_settings(payload: SettingsPayload, x_session_id: str | None = Header(default=None)) -> dict:
    session = _session(x_session_id)
    session.settings = payload.model_dump()
    session.touch()
    return {"ok": True, "settings": session.settings}


@app.get("/api/v1/report")
def report_summary(x_session_id: str | None = Header(default=None)) -> dict:
    session = _require_chart(x_session_id)
    return report_document(session.report or generate_basic_bazi_report(session.chart), "简明报告", "REPORT · SUMMARY")


@app.get("/api/v1/export/{format_name}")
def export_report(
    format_name: str,
    kind: str = Query(default="full"),
    x_session_id: str | None = Header(default=None),
) -> Response:
    session = _require_chart(x_session_id)
    chart = session.chart
    profile = session.profile or chart.get("profile", {})
    safe_name = "".join(char for char in profile.get("name", "未命名") if char not in '/\\:*?"<>|') or "未命名"
    if kind in {"career", "wealth", "love"}:
        special = _special_report(kind, chart, profile)
        if format_name == "md":
            data, media = build_special_markdown(special).encode("utf-8"), "text/markdown; charset=utf-8"
        elif format_name == "txt":
            data, media = build_special_text_report(special).encode("utf-8"), "text/plain; charset=utf-8"
        elif format_name == "pdf":
            data, media = build_special_pdf_report(special), "application/pdf"
        else:
            raise HTTPException(status_code=404, detail="不支持该导出格式。")
        filename = f"{safe_name}_{kind}.{format_name}"
    else:
        report = session.report or generate_basic_bazi_report(chart)
        luck = get_luck_cycles(profile, chart)
        yearly = analyze_yearly_fortune(chart, date.today().year, luck)
        monthly = analyze_monthly_fortune(chart, date.today().year)
        if format_name == "md":
            data, media = build_markdown_report(profile, chart, report, luck, yearly, monthly).encode("utf-8"), "text/markdown; charset=utf-8"
        elif format_name == "txt":
            data, media = build_text_report(profile, chart, report, luck, yearly, monthly).encode("utf-8"), "text/plain; charset=utf-8"
        elif format_name == "pdf":
            data, media = build_pdf_report(profile, chart, report, luck, yearly, monthly), "application/pdf"
        else:
            raise HTTPException(status_code=404, detail="不支持该导出格式。")
        filename = f"{safe_name}_完整报告.{format_name}"
    ascii_name = f"mingshu-report.{format_name}"
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
    return Response(data, media_type=media, headers={"Content-Disposition": disposition})


@app.get("/")
def index() -> dict:
    return {"name": "命数研究室小程序测试 API", "docs": "/docs", "health": "/api/health"}
