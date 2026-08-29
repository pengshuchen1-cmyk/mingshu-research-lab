from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from backend.main import create_app


def _birth(**overrides):
    value = {
        "name": "测试用户",
        "gender": "男",
        "calendar": "solar",
        "year": 1994,
        "month": 9,
        "day": 23,
        "hour": None,
        "minute": None,
        "is_leap_month": False,
        "birth_place": "测试地点",
        "time_label": "时辰不详",
        "privacy_consent": True,
    }
    value.update(overrides)
    return value


def _preview_and_confirm(client: TestClient, **overrides):
    birth = _birth(**overrides)
    preview = client.post("/api/v1/chart/preview", json=birth)
    assert preview.status_code == 200
    confirmation = birth | {
        "preview_id": preview.json()["preview_id"],
        "input_fingerprint": preview.json()["input_fingerprint"],
        "chart_fingerprint": preview.json()["chart_fingerprint"],
    }
    confirmed = client.post("/api/v1/chart/confirm", json=confirmation)
    assert confirmed.status_code == 200
    return birth, preview.json(), confirmed.json()


def test_health_reports_version_and_runtime_mode(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    response = TestClient(create_app()).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0", "runtime_mode": "public"}
    assert len(response.headers["x-request-id"]) == 32


def test_preview_unknown_hour_is_safe_and_does_not_echo_pii():
    response = TestClient(create_app()).post("/api/v1/chart/preview", json=_birth())
    assert response.status_code == 200
    body = response.json()
    assert body["pillars"][3] == "时柱不详"
    assert set(body) == {
        "preview_id", "input_text", "solar_datetime", "pillars", "calculation_basis",
        "input_fingerprint", "chart_fingerprint",
    }
    encoded = response.text
    assert "测试用户" not in encoded
    assert "测试地点" not in encoded
    assert "profile" not in encoded


def test_validation_rejects_extra_fields_and_does_not_echo_values():
    response = TestClient(create_app()).post(
        "/api/v1/chart/preview",
        json=_birth(secret_value="do-not-echo-this"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["fields"] == ["unknown_field"]
    assert "do-not-echo-this" not in response.text


def test_hour_and_minute_must_be_a_pair():
    response = TestClient(create_app()).post(
        "/api/v1/chart/preview", json=_birth(hour=23, minute=None)
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"] == ["body"]
    assert "1994" not in response.text


def test_public_preview_requires_consent(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    app = create_app()
    response = TestClient(app).post(
        "/api/v1/chart/preview", json=_birth(privacy_consent=False)
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PRIVACY_CONSENT_REQUIRED"
    assert "set-cookie" not in response.headers
    assert app.state.session_store.counts()[0] == 0


def test_input_fingerprint_tamper_is_rejected():
    client = TestClient(create_app())
    birth = _birth()
    preview = client.post("/api/v1/chart/preview", json=birth).json()
    response = client.post(
        "/api/v1/chart/confirm",
        json=birth | {
            "preview_id": preview["preview_id"],
            "input_fingerprint": "0" * 64,
            "chart_fingerprint": preview["chart_fingerprint"],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PREVIEW_CONFLICT"
    assert "set-cookie" in response.headers


def test_chart_fingerprint_tamper_is_rejected():
    client = TestClient(create_app())
    birth = _birth()
    preview = client.post("/api/v1/chart/preview", json=birth).json()
    response = client.post(
        "/api/v1/chart/confirm",
        json=birth | {
            "preview_id": preview["preview_id"],
            "input_fingerprint": preview["input_fingerprint"],
            "chart_fingerprint": "0" * 64,
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PREVIEW_CONFLICT"


def test_confirm_and_get_return_canonical_facts_and_secure_cookie():
    client = TestClient(create_app())
    _, preview, confirmed = _preview_and_confirm(client)
    response = client.get(f"/api/v1/chart/{confirmed['chart_id']}")
    assert response.status_code == 200
    assert response.json()["chart_facts"] == confirmed["chart_facts"]
    assert response.json()["chart_fingerprint"] == preview["chart_fingerprint"]
    cookie = client.cookies.get("mingshu_session")
    assert cookie and "." in cookie
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "测试用户" not in response.text
    assert "测试地点" not in response.text


def test_chart_cannot_be_read_by_another_session():
    owner = TestClient(create_app())
    _, _, confirmed = _preview_and_confirm(owner)
    # Both clients must address the same process-local app/store.
    intruder = TestClient(owner.app)
    assert intruder.post("/api/v1/chart/preview", json=_birth(year=1995)).status_code == 200
    response = intruder.get(f"/api/v1/chart/{confirmed['chart_id']}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CHART_SESSION_MISMATCH"


def test_confirming_new_chart_invalidates_previous_chart():
    client = TestClient(create_app())
    _, _, first = _preview_and_confirm(client)
    _, _, second = _preview_and_confirm(client, year=1995)
    assert first["chart_id"] != second["chart_id"]
    response = client.get(f"/api/v1/chart/{first['chart_id']}")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "CHART_INVALIDATED"


def test_session_ttl_expires_chart(monkeypatch):
    now = [100.0]
    monkeypatch.setenv("MINGSHU_SESSION_TTL_SECONDS", "10")
    client = TestClient(create_app(clock=lambda: now[0]))
    _, _, confirmed = _preview_and_confirm(client)
    now[0] += 11
    response = client.get(f"/api/v1/chart/{confirmed['chart_id']}")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "CHART_EXPIRED"
    assert confirmed["chart_id"] not in client.app.state.session_store._charts
    assert confirmed["chart_id"] in client.app.state.session_store._tombstones


def test_cors_uses_exact_allowlist(monkeypatch):
    monkeypatch.setenv("MINGSHU_CORS_ORIGINS", "https://frontend.example")
    client = TestClient(create_app())
    allowed = client.options(
        "/api/v1/chart/preview",
        headers={
            "Origin": "https://frontend.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    denied = client.options(
        "/api/v1/chart/preview",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "https://frontend.example"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in denied.headers
    assert client.app.state.session_store.counts()[0] == 0


def test_public_api_never_connects_to_sqlite(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    monkeypatch.setenv("MINGSHU_SESSION_COOKIE_SECURE", "false")

    def forbidden_connect(*args, **kwargs):
        raise AssertionError("public API must not touch SQLite")

    monkeypatch.setattr(sqlite3, "connect", forbidden_connect)
    client = TestClient(create_app())
    assert client.get("/healthz").status_code == 200
    assert client.post("/api/v1/chart/preview", json=_birth()).status_code == 200


def test_openapi_is_available_and_documents_strict_schema():
    body = TestClient(create_app()).get("/openapi.json").json()
    assert "/api/v1/chart/preview" in body["paths"]
    assert body["components"]["schemas"]["BirthInputRequest"]["additionalProperties"] is False
    for path, statuses in {
        "/api/v1/chart/preview": ("403", "410", "422", "500", "503"),
        "/api/v1/chart/confirm": ("403", "409", "410", "422", "500"),
        "/api/v1/chart/{chart_id}": ("403", "404", "410", "422", "500"),
    }.items():
        method = "get" if "{chart_id}" in path else "post"
        responses = body["paths"][path][method]["responses"]
        for status in statuses:
            assert responses[status]["content"]["application/json"]["schema"]["$ref"].endswith(
                "/ErrorResponse"
            )


def test_solar_input_rejects_leap_month():
    response = TestClient(create_app()).post(
        "/api/v1/chart/preview", json=_birth(is_leap_month=True)
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"] == ["body"]


def test_preview_token_is_session_bound_and_opaque():
    app = create_app()
    first = TestClient(app).post("/api/v1/chart/preview", json=_birth()).json()
    second = TestClient(app).post("/api/v1/chart/preview", json=_birth()).json()
    assert first["input_fingerprint"] != second["input_fingerprint"]
    assert len(first["input_fingerprint"]) == 64


def test_cross_session_preview_cannot_be_confirmed():
    app = create_app()
    owner = TestClient(app)
    intruder = TestClient(app)
    birth = _birth()
    preview = owner.post("/api/v1/chart/preview", json=birth).json()
    assert intruder.post("/api/v1/chart/preview", json=_birth(year=1995)).status_code == 200
    response = intruder.post(
        "/api/v1/chart/confirm",
        json=birth | {
            "preview_id": preview["preview_id"],
            "input_fingerprint": preview["input_fingerprint"],
            "chart_fingerprint": preview["chart_fingerprint"],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PREVIEW_CONFLICT"


def test_confirm_requires_preview_and_is_one_time():
    client = TestClient(create_app())
    birth, preview, confirmed = _preview_and_confirm(client)
    confirmation = birth | {
        "preview_id": preview["preview_id"],
        "input_fingerprint": preview["input_fingerprint"],
        "chart_fingerprint": preview["chart_fingerprint"],
    }
    replay = client.post("/api/v1/chart/confirm", json=confirmation)
    skipped = TestClient(client.app).post("/api/v1/chart/confirm", json=confirmation)
    assert confirmed["chart_id"]
    assert replay.status_code == 409
    assert skipped.status_code == 409


def test_session_expiring_during_confirmation_returns_410(monkeypatch):
    from backend import main as backend_main

    now = [100.0]
    calls = [0]
    original = backend_main.build_birth_preview

    def expiring_build(value):
        result = original(value)
        calls[0] += 1
        if calls[0] == 2:
            now[0] += 11
        return result

    monkeypatch.setenv("MINGSHU_SESSION_TTL_SECONDS", "10")
    monkeypatch.setattr(backend_main, "build_birth_preview", expiring_build)
    client = TestClient(create_app(clock=lambda: now[0]))
    birth = _birth()
    preview = client.post("/api/v1/chart/preview", json=birth).json()
    response = client.post(
        "/api/v1/chart/confirm",
        json=birth | {
            "preview_id": preview["preview_id"],
            "input_fingerprint": preview["input_fingerprint"],
            "chart_fingerprint": preview["chart_fingerprint"],
        },
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert client.cookies.get("mingshu_session") is None


def test_cookie_less_invalid_requests_do_not_create_sessions():
    app = create_app()
    client = TestClient(app)
    first = client.post("/api/v1/chart/preview", json={"secret-value-key": "secret-value"})
    second = client.post("/api/v1/chart/preview", json={"secret-value-key": "secret-value"})
    assert first.status_code == second.status_code == 422
    assert "set-cookie" not in first.headers and "set-cookie" not in second.headers
    assert "secret-value-key" not in first.text
    assert "secret-value" not in first.text
    assert app.state.session_store.counts()[0] == 0


def test_tampered_cookie_gets_403_and_is_cleared_without_new_session():
    app = create_app()
    client = TestClient(app)
    _, _, confirmed = _preview_and_confirm(client)
    client.cookies.set(
        "mingshu_session", "tampered", domain="testserver.local", path="/"
    )
    response = client.get(f"/api/v1/chart/{confirmed['chart_id']}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SESSION_REQUIRED"
    assert "set-cookie" in response.headers
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert client.cookies.get("mingshu_session") is None
    assert app.state.session_store.counts()[0] == 1


def test_public_cookie_is_always_secure_even_when_override_is_false(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    monkeypatch.setenv("MINGSHU_SESSION_COOKIE_SECURE", "false")
    response = TestClient(create_app()).post("/api/v1/chart/preview", json=_birth())
    cookie = response.headers["set-cookie"].lower()
    assert "secure" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_all_api_responses_disable_caching():
    client = TestClient(create_app())
    success = client.post("/api/v1/chart/preview", json=_birth())
    error = client.post("/api/v1/chart/preview", json={})
    for response in (success, error):
        assert response.headers["cache-control"] == "no-store, private"
        assert response.headers["pragma"] == "no-cache"


def test_tampered_birth_input_is_rejected_before_chart_build(monkeypatch):
    from backend import main as backend_main

    client = TestClient(create_app())
    birth = _birth()
    preview = client.post("/api/v1/chart/preview", json=birth).json()
    calls = [0]
    original = backend_main.build_birth_preview

    def spy(value):
        calls[0] += 1
        return original(value)

    monkeypatch.setattr(backend_main, "build_birth_preview", spy)
    response = client.post(
        "/api/v1/chart/confirm",
        json=(birth | {"year": 1995}) | {
            "preview_id": preview["preview_id"],
            "input_fingerprint": preview["input_fingerprint"],
            "chart_fingerprint": preview["chart_fingerprint"],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PREVIEW_CONFLICT"
    assert calls[0] == 0


def test_unexpected_preview_error_is_safe_and_does_not_create_session(monkeypatch):
    from backend import main as backend_main

    def fail(_):
        raise RuntimeError("secret exception detail")

    monkeypatch.setattr(backend_main, "build_birth_preview", fail)
    app = create_app()
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/chart/preview", json=_birth()
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret exception detail" not in response.text
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["cache-control"] == "no-store, private"
    assert response.headers["pragma"] == "no-cache"
    assert "set-cookie" not in response.headers
    assert app.state.session_store.counts()[0] == 0


def test_allowed_origin_receives_cors_headers_on_unexpected_500(monkeypatch):
    from backend import main as backend_main

    monkeypatch.setenv("MINGSHU_CORS_ORIGINS", "https://frontend.example")

    def fail(_):
        raise RuntimeError("secret exception detail")

    monkeypatch.setattr(backend_main, "build_birth_preview", fail)
    response = TestClient(create_app(), raise_server_exceptions=False).post(
        "/api/v1/chart/preview",
        json=_birth(),
        headers={"Origin": "https://frontend.example"},
    )
    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "https://frontend.example"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret exception detail" not in response.text
    assert response.headers["cache-control"] == "no-store, private"
    assert response.headers["pragma"] == "no-cache"
    assert len(response.headers["x-request-id"]) == 32


def test_preview_session_capacity_is_bounded_and_returns_503(monkeypatch):
    monkeypatch.setenv("MINGSHU_SESSION_CAPACITY", "1")
    app = create_app()
    assert TestClient(app).post("/api/v1/chart/preview", json=_birth()).status_code == 200
    response = TestClient(app).post("/api/v1/chart/preview", json=_birth(year=1995))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SESSION_CAPACITY"
    assert app.state.session_store.counts()[0] == 1
