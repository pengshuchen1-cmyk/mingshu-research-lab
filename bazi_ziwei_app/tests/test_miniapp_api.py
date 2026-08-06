from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import utils.database as database
from miniapp_api.app import app


PROFILE = {
    "name": "小程序接口测试",
    "gender": "男",
    "calendar_type": "solar",
    "birth_date": "1990-01-01",
    "birth_hour": 10,
    "birth_minute": 0,
    "birth_place": "上海",
    "is_leap_month": False,
    "time_known": True,
    "note": "",
}


def test_miniapp_chart_and_all_feature_documents(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "profiles.db"))
    headers = {"X-Session-Id": "pytest-miniapp-features"}

    with TestClient(app) as client:
        assert client.get("/api/health").json()["ok"] is True
        assert client.get("/api/v1/home").status_code == 200
        assert client.post("/api/v1/profile/preview", json=PROFILE).status_code == 200
        created = client.post("/api/v1/profile/chart", json=PROFILE, headers=headers)
        assert created.status_code == 200
        assert created.json()["document"]["key"] == "bazi"

        feature_names = (
            "bazi", "overview", "five-elements", "sixty-jiazi", "luck",
            "yearly", "career", "wealth", "love", "ziwei", "report",
        )
        for feature_name in feature_names:
            response = client.get(
                f"/api/v1/feature/{feature_name}?year=2026",
                headers=headers,
            )
            assert response.status_code == 200, response.text
            document = response.json()
            assert document["hero"]["title"]
            assert isinstance(document["sections"], list)


def test_miniapp_export_and_static_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "profiles.db"))
    headers = {"X-Session-Id": "pytest-miniapp-export"}

    with TestClient(app) as client:
        assert client.post("/api/v1/profile/chart", json=PROFILE, headers=headers).status_code == 200
        markdown = client.get("/api/v1/export/md", headers=headers)
        pdf = client.get("/api/v1/export/pdf?kind=career", headers=headers)
        assert markdown.status_code == 200
        assert "text/markdown" in markdown.headers["content-type"]
        assert len(markdown.content) > 1000
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")

    project_root = Path(__file__).resolve().parents[1] / "wechat_miniprogram"
    assert (project_root / "project.config.json").exists()
    assert len(list((project_root / "pages").glob("*/index.wxml"))) == 12


def test_miniapp_archive_compatibility_backup_and_ai(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "profiles.db"))
    headers = {"X-Session-Id": "pytest-miniapp-workspace"}
    second_profile = {
        **PROFILE,
        "name": "小程序接口测试乙方",
        "gender": "女",
        "birth_date": "1992-12-26",
        "birth_hour": 0,
        "birth_place": "北京",
    }

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/profile/chart?save=true",
            json=PROFILE,
            headers=headers,
        ).json()["profile_id"]
        second = client.post(
            "/api/v1/profile/chart?save=true",
            json=second_profile,
            headers=headers,
        ).json()["profile_id"]

        archives = client.get("/api/v1/archives").json()["items"]
        assert {item["id"] for item in archives} == {first, second}
        compatibility = client.post(
            "/api/v1/compatibility",
            json={"first_profile_id": first, "second_profile_id": second},
        )
        assert compatibility.status_code == 200
        assert compatibility.json()["hero"]["title"]

        assert client.post(f"/api/v1/archives/{first}/load", headers=headers).status_code == 200
        answer = client.post(
            "/api/v1/ai/ask",
            headers=headers,
            json={"question": "请简要总结事业优势"},
        )
        assert answer.status_code == 200
        assert answer.json()["answer"]

        settings = {
            "report_length": "详细版",
            "show_technical_details": True,
            "show_disclaimer": True,
            "default_export_format": "PDF",
            "enable_quality_check": True,
        }
        assert client.put("/api/v1/settings", headers=headers, json=settings).status_code == 200
        assert client.get("/api/v1/settings", headers=headers).json() == settings

        json_backup = client.get("/api/v1/backup")
        database_backup = client.get("/api/v1/backup/database")
        assert json_backup.status_code == 200
        assert "小程序接口测试" in json_backup.text
        assert database_backup.status_code == 200
        assert database_backup.content.startswith(b"SQLite format 3")

        assert client.delete(f"/api/v1/archives/{second}").status_code == 200
        remaining = client.get("/api/v1/archives").json()["items"]
        assert [item["id"] for item in remaining] == [first]
