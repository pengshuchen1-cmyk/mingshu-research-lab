"""FastAPI entry point for the phase-one frontend API."""

from __future__ import annotations

import asyncio
import contextlib
import os
import uuid
from collections.abc import Mapping
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.schemas import (
    BirthInputRequest,
    ConfirmChartRequest,
    ConfirmChartResponse,
    ErrorDetail,
    ErrorResponse,
    GetChartResponse,
    HealthResponse,
    PreviewResponse,
)
from backend.session_store import SessionCapacityError, SessionStore
from core.birth_input_preview import BirthFormInput, build_birth_preview
from core.chart_facts import chart_facts_from_chart
from utils.runtime_mode import get_runtime_mode


API_VERSION = "1.0.0"
COOKIE_NAME = "mingshu_session"
DEFAULT_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
SCHEMA_FIELDS = frozenset(
    {
        "name", "gender", "calendar", "year", "month", "day", "hour", "minute",
        "is_leap_month", "birth_place", "time_label", "privacy_consent", "preview_id",
        "input_fingerprint", "chart_fingerprint", "chart_id",
    }
)
ERROR_RESPONSES = {
    status: {"model": ErrorResponse}
    for status in (403, 404, 409, 410, 422, 500, 503)
}


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def _integer_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _cookie_secure() -> bool:
    if get_runtime_mode() == "public":
        return True
    raw = os.getenv("MINGSHU_SESSION_COOKIE_SECURE")
    if raw is not None:
        return raw.strip().lower() not in {"0", "false", "no"}
    return False


def _origins() -> list[str]:
    raw = os.getenv("MINGSHU_CORS_ORIGINS", "")
    origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]
    origins = origins or list(DEFAULT_ORIGINS)
    return [origin for origin in dict.fromkeys(origins) if origin != "*"]


def _birth_input(value: BirthInputRequest) -> BirthFormInput:
    return BirthFormInput(
        name=value.name,
        gender=value.gender,
        calendar=value.calendar,
        year=value.year,
        month=value.month,
        day=value.day,
        hour=value.hour,
        minute=value.minute,
        is_leap_month=value.is_leap_month,
        birth_place=value.birth_place,
        time_label=value.time_label,
    )


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_thaw(item) for item in value]
    return value


def _error_payload(request: Request, code: str, message: str, fields=None) -> dict:
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, fields=fields or []),
        request_id=request.state.request_id,
    ).model_dump()


def _validation_fields(exc: RequestValidationError) -> list[str]:
    fields: set[str] = set()
    for error in exc.errors():
        parts = error.get("loc", ())[1:]
        candidate = str(parts[-1]) if parts else "body"
        if candidate in SCHEMA_FIELDS or candidate == "body":
            fields.add(candidate)
        elif error.get("type") == "value_error":
            fields.add("body")
        else:
            fields.add("unknown_field")
    return sorted(fields or {"body"})


def create_app(*, clock=None) -> FastAPI:
    ttl = _integer_env("MINGSHU_SESSION_TTL_SECONDS", 1800)
    capacity = _integer_env("MINGSHU_SESSION_CAPACITY", 4096)
    store_args = {"session_capacity": capacity}
    store = (
        SessionStore(ttl, clock=clock, **store_args)
        if clock is not None
        else SessionStore(ttl, **store_args)
    )
    cleanup_interval = max(1.0, min(float(ttl), 60.0))

    async def cleanup_loop() -> None:
        while True:
            await asyncio.sleep(cleanup_interval)
            store.cleanup()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(cleanup_loop())
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            store.clear()

    api = FastAPI(title="Mingshu Chart API", version=API_VERSION, lifespan=lifespan)
    api.state.session_store = store

    @api.middleware("http")
    async def security_middleware(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        is_api = request.url.path.startswith("/api/v1/")
        cookie_value = request.cookies.get(COOKIE_NAME)
        request.state.session_id = None
        request.state.session_status = "missing"
        if is_api and request.method != "OPTIONS" and cookie_value:
            session_status, session_id = store.verify_status(cookie_value)
            request.state.session_status = session_status
            request.state.session_id = session_id
        try:
            response = await call_next(request)
        except Exception:
            # This outer boundary also covers exceptions raised outside
            # FastAPI's registered handlers. Never serialize exception text.
            response = JSONResponse(
                status_code=500,
                content=_error_payload(
                    request, "INTERNAL_ERROR", "服务器暂时无法处理请求。"
                ),
            )
        response.headers["X-Request-ID"] = request.state.request_id
        if is_api:
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["Pragma"] = "no-cache"
            if request.method != "OPTIONS":
                session_id = request.state.session_id
                if session_id and store.is_live(session_id):
                    response.set_cookie(
                        COOKIE_NAME,
                        store.sign(session_id),
                        max_age=ttl,
                        httponly=True,
                        secure=_cookie_secure(),
                        samesite="lax",
                        path="/",
                    )
                elif cookie_value:
                    response.delete_cookie(
                        COOKIE_NAME,
                        httponly=True,
                        secure=_cookie_secure(),
                        samesite="lax",
                        path="/",
                    )
        return response

    # Register CORS after the security middleware so Starlette wraps it as the
    # outermost layer. Even security-generated 500 responses then receive CORS
    # headers for an explicitly allowed origin.
    api.add_middleware(
        CORSMiddleware,
        allow_origins=_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @api.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, exc.code, exc.message),
        )

    @api.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                request, "VALIDATION_ERROR", "请求参数无效。", _validation_fields(exc)
            ),
        )

    @api.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = "请求的资源不存在。" if exc.status_code == 404 else "请求无法处理。"
        return JSONResponse(status_code=exc.status_code, content=_error_payload(request, code, message))

    @api.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, _: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_payload(request, "INTERNAL_ERROR", "服务器暂时无法处理请求。"),
        )

    def optional_session(request: Request) -> str | None:
        return request.state.session_id

    @api.get("/healthz", response_model=HealthResponse)
    def healthz() -> HealthResponse:
        return HealthResponse(status="ok", version=API_VERSION, runtime_mode=get_runtime_mode())

    @api.post(
        "/api/v1/chart/preview",
        response_model=PreviewResponse,
        responses={status: ERROR_RESPONSES[status] for status in (403, 410, 422, 500, 503)},
    )
    def preview_chart(
        request: Request,
        value: BirthInputRequest,
        session_id: str | None = Depends(optional_session),
    ) -> PreviewResponse:
        if get_runtime_mode() == "public" and not value.privacy_consent:
            raise ApiError(403, "PRIVACY_CONSENT_REQUIRED", "公网模式需要先同意隐私处理。")
        try:
            preview = build_birth_preview(_birth_input(value))
        except ValueError as exc:
            raise ApiError(422, "INVALID_BIRTH_INPUT", "出生信息无法生成命盘。") from exc
        if session_id is None:
            try:
                session_id, _ = store.issue()
            except SessionCapacityError as exc:
                raise ApiError(503, "SESSION_CAPACITY", "服务繁忙，请稍后重试。") from exc
            request.state.session_id = session_id
        state, preview_id, token = store.create_preview(
            session_id, preview.input_fingerprint, preview.chart_fingerprint
        )
        if state != "ok" or preview_id is None or token is None:
            raise ApiError(410, "SESSION_EXPIRED", "会话已过期，请重新预览。")
        return PreviewResponse(
            preview_id=preview_id,
            input_text=preview.input_text,
            solar_datetime=preview.solar_datetime,
            pillars=preview.pillars,
            calculation_basis=preview.calculation_basis,
            input_fingerprint=token,
            chart_fingerprint=preview.chart_fingerprint,
        )

    @api.post(
        "/api/v1/chart/confirm",
        response_model=ConfirmChartResponse,
        responses={status: ERROR_RESPONSES[status] for status in (403, 409, 410, 422, 500)},
    )
    def confirm_chart(
        request: Request,
        value: ConfirmChartRequest,
        session_id: str | None = Depends(optional_session),
    ) -> ConfirmChartResponse:
        if session_id is None:
            if request.state.session_status == "expired":
                raise ApiError(410, "SESSION_EXPIRED", "会话已过期，请重新预览。")
            raise ApiError(409, "SESSION_REQUIRED", "预览会话不存在或已过期。")
        if get_runtime_mode() == "public" and not value.privacy_consent:
            raise ApiError(403, "PRIVACY_CONSENT_REQUIRED", "公网模式需要先同意隐私处理。")
        birth_input = _birth_input(value)
        raw_input_hash = birth_input.fingerprint()
        state, reservation = store.begin_confirmation(
            session_id,
            value.preview_id,
            value.input_fingerprint,
            value.chart_fingerprint,
            raw_input_hash,
        )
        if state == "expired":
            raise ApiError(410, "SESSION_EXPIRED", "会话已过期，请重新预览。")
        if state != "ok" or reservation is None:
            raise ApiError(409, "PREVIEW_CONFLICT", "预览无效、已使用或不属于当前会话。")
        try:
            preview = build_birth_preview(birth_input)
            chart = _thaw(preview.chart)
            facts = chart_facts_from_chart(chart).to_dict()
        except ValueError as exc:
            store.cancel_confirmation(session_id, reservation)
            raise ApiError(422, "INVALID_BIRTH_INPUT", "出生信息无法生成命盘。") from exc
        except Exception:
            store.cancel_confirmation(session_id, reservation)
            raise
        state, chart_id = store.finish_confirmation(
            session_id,
            reservation,
            preview.input_fingerprint,
            preview.chart_fingerprint,
            chart,
            facts,
        )
        if state == "expired":
            chart.clear()
            facts.clear()
            raise ApiError(410, "SESSION_EXPIRED", "会话已过期，请重新预览。")
        if state == "mismatch":
            chart.clear()
            facts.clear()
            raise ApiError(409, "FINGERPRINT_MISMATCH", "输入或命盘已变化，请重新预览。")
        if state != "ok" or chart_id is None:
            chart.clear()
            facts.clear()
            raise ApiError(409, "PREVIEW_CONFLICT", "预览已被使用，请重新预览。")
        return ConfirmChartResponse(
            chart_id=chart_id,
            chart_facts=facts,
            chart_fingerprint=preview.chart_fingerprint,
        )

    @api.get(
        "/api/v1/chart/{chart_id}",
        response_model=GetChartResponse,
        responses={status: ERROR_RESPONSES[status] for status in (403, 404, 410, 422, 500)},
    )
    def get_chart(
        request: Request,
        chart_id: str,
        session_id: str | None = Depends(optional_session),
    ) -> GetChartResponse:
        if session_id is None:
            if request.state.session_status == "expired":
                raise ApiError(410, "CHART_EXPIRED", "命盘会话已过期。")
            raise ApiError(403, "SESSION_REQUIRED", "命盘会话不存在或已过期。")
        state, snapshot = store.get(session_id, chart_id)
        errors = {
            "missing": (404, "CHART_NOT_FOUND", "命盘不存在。"),
            "expired": (410, "CHART_EXPIRED", "命盘会话已过期。"),
            "invalidated": (410, "CHART_INVALIDATED", "该命盘已被新确认的命盘替换。"),
            "forbidden": (403, "CHART_SESSION_MISMATCH", "该命盘不属于当前会话。"),
        }
        if snapshot is None:
            status_code, code, message = errors.get(
                state, (404, "CHART_NOT_FOUND", "命盘不存在。")
            )
            raise ApiError(status_code, code, message)
        return GetChartResponse(
            chart_id=chart_id,
            chart_facts=snapshot.facts,
            chart_fingerprint=snapshot.fingerprint,
        )

    return api


app = create_app()
