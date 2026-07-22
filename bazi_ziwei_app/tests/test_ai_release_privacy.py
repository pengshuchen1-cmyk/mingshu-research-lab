from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ai_transport_is_responses_only_and_disables_storage():
    source = (ROOT / "services" / "openai_bazi_client.py").read_text(encoding="utf-8")
    assert source.count("responses.parse") == 1
    assert "store=False" in source
    assert "conversations" not in source.lower()
    assert "chat.completions" not in source.lower()


def test_api_key_is_not_read_or_rendered_by_customer_ui():
    ui_source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "ui").glob("*.py"))
    assert "OPENAI_API_KEY" not in ui_source
    assert "api_key" not in ui_source


def test_context_and_logs_exclude_customer_identity_and_content():
    context_source = (ROOT / "core" / "ai_context.py").read_text(encoding="utf-8")
    logger_source = (ROOT / "utils" / "logger.py").read_text(encoding="utf-8")
    for forbidden in ("name", "birth_date", "birth_time", "birth_place", "longitude", "profile_id"):
        assert f'chart_facts["{forbidden}"]' not in context_source
    assert "**_forbidden_fields" in logger_source
    assert "build_ai_log_record" in logger_source


def test_release_ignores_secrets_and_live_acceptance_runs():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ignored
    assert "acceptance_runs/" in ignored


def test_customer_output_omits_removed_fields():
    customer_source = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in (ROOT / "ui", ROOT / "report")
        for path in folder.glob("*.py")
    )
    assert "算法版本" not in customer_source
    assert "调候依据" not in customer_source
