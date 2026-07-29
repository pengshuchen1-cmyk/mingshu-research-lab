from __future__ import annotations


def test_ai_log_records_only_allowlisted_metadata():
    from utils.logger import build_ai_log_record

    record = build_ai_log_record(
        event_code="AI_QA_FALLBACK",
        category="wealth",
        model_alias="primary",
        latency_ms=4123,
        reason_code="guard_rejected",
        question="我能不能抵押房子创业？",
        answer="不能保证。",
        birth_date="1996-09-04",
    )

    assert set(record) == {
        "event_code",
        "category",
        "time_scope",
        "model_alias",
        "latency_bucket",
        "reason_code",
        "violation_code",
    }
    assert record["latency_bucket"] == "3-10s"
    serialized = repr(record)
    for forbidden in ("抵押房子", "不能保证", "1996-09-04"):
        assert forbidden not in serialized


def test_ai_log_event_codes_are_restricted():
    from utils.logger import build_ai_log_record

    record = build_ai_log_record(event_code="question:\u91d1丝雀", category="other")
    assert record["event_code"] == "AI_QA_UNKNOWN"


def test_ai_log_record_rejects_raw_content():
    from utils.logger import build_ai_log_record

    record = build_ai_log_record(
        event_code="AI_QA_SEGMENT_REPLACED",
        category="wealth",
        time_scope="target_year",
        violation_code="GUARD_YEAR_CONFLICT",
        question="明年财运如何",
        answer="原文",
    )

    assert "question" not in record
    assert "answer" not in record
    assert record["violation_code"] == "GUARD_YEAR_CONFLICT"
    assert record["time_scope"] == "target_year"
    assert record["event_code"] == "AI_QA_SEGMENT_REPLACED"


def test_private_logger_rotates_at_utc_midnight_and_keeps_thirty_backups(
    monkeypatch,
    tmp_path,
):
    import logging
    from logging.handlers import TimedRotatingFileHandler

    import utils.logger as logger_module

    app_logger = logging.getLogger("命数研究室")
    existing_handlers = list(app_logger.handlers)
    for handler in existing_handlers:
        app_logger.removeHandler(handler)
    monkeypatch.setattr(logger_module, "is_public_mode", lambda: False)
    monkeypatch.setattr(logger_module, "LOG_PATH", str(tmp_path / "app.log"))

    try:
        handler = logger_module.get_logger().handlers[0]
        assert isinstance(handler, TimedRotatingFileHandler)
        assert handler.backupCount == 30
        assert handler.utc is True
    finally:
        for handler in list(app_logger.handlers):
            app_logger.removeHandler(handler)
            handler.close()
        for handler in existing_handlers:
            app_logger.addHandler(handler)
