import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app import guidance
from app.config import BACKEND_DIR
from app.main import app


def test_migrated_today_contract_matches_known_daily_and_yearly_guidance():
    result = guidance.build_today_guidance(date(2026, 7, 11), 2026)
    daily = result["daily_guidance"]
    yearly = result["yearly_guidance"]

    assert result["timezone"] == "Asia/Shanghai"
    assert daily is not None
    assert set(daily) == {
        "kind",
        "is_personal",
        "date",
        "day_pillar",
        "title",
        "element_theme",
        "wearing_colors",
        "wearing_advice",
        "cautions",
        "primary_action",
        "theme",
        "focus",
        "action",
        "reminder",
        "details",
        "basis",
        "boundary_note",
    }
    assert daily["date"] == "2026-07-11"
    assert daily["day_pillar"] == "丙戌"
    assert daily["element_theme"] == "火"
    assert daily["is_personal"] is False
    assert "未读取姓名、性别或出生资料" in daily["boundary_note"]
    assert yearly["title"] == "今年建议｜2026年 丙午"
    assert yearly["is_personal"] is False
    assert guidance.build_today_guidance(date(2026, 7, 11), 2026) == result


def test_today_endpoint_is_public_json_safe_and_uses_date_year_by_default():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/guidance/today",
            params={"target_date": "2026-07-11"},
        )
        operation = client.get("/openapi.json").json()["paths"][
            "/api/v1/guidance/today"
        ]["get"]

    assert response.status_code == 200
    payload = response.json()
    assert payload["daily_guidance"]["date"] == "2026-07-11"
    assert payload["yearly_guidance"]["year"] == 2026
    assert "security" not in operation
    serialized = json.dumps(payload, ensure_ascii=False)
    for private_key in ("name", "birth_date", "birth_time", "birth_place", "profile_id"):
        assert private_key not in serialized


def test_today_endpoint_validates_supported_date_and_year_ranges():
    with TestClient(app) as client:
        too_early_date = client.get(
            "/api/v1/guidance/today",
            params={"target_date": "1899-12-31"},
        )
        too_late_year = client.get(
            "/api/v1/guidance/today",
            params={"target_year": 2101},
        )

    assert too_early_date.status_code == 422
    assert too_late_year.status_code == 422


def test_today_endpoint_keeps_yearly_guidance_when_daily_calendar_fails(monkeypatch):
    def unavailable(_: date) -> str:
        raise guidance.DailyGuidanceUnavailableError("calendar unavailable")

    monkeypatch.setattr(guidance, "_day_pillar", unavailable)
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/guidance/today",
            params={"target_date": "2026-07-11", "target_year": 2026},
        )

    assert response.status_code == 200
    assert response.json()["daily_guidance"] is None
    assert response.json()["yearly_guidance"]["year"] == 2026


def test_backend_guidance_has_no_legacy_application_dependency():
    source_paths = [
        BACKEND_DIR / "app" / "guidance.py",
        BACKEND_DIR / "app" / "api" / "v1" / "guidance.py",
    ]
    forbidden = ("bazi_ziwei_app", "from core.", "import core.", "sys.path")

    for path in source_paths:
        source = Path(path).read_text(encoding="utf-8")
        assert not any(marker in source for marker in forbidden), path
