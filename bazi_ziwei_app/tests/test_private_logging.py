from __future__ import annotations


def test_public_safe_log_record_rejects_personal_fields_and_sanitizes_lines():
    from utils.logger import build_safe_log_record

    record = build_safe_log_record(
        event_code="chart\ncreated|unsafe",
        request_id="req-123",
        algorithm_version="1.0.6",
        duration_ms=123.4,
        success=False,
        error_type="ValueError\n金丝雀姓名 1990-01-01 广东汕头",
        name="金丝雀姓名",
        birth_date="1990-01-01",
    )

    assert set(record) == {"event_code", "request_id", "algorithm_version", "duration_ms", "success", "error_type"}
    serialized = repr(record)
    for forbidden in ("金丝雀姓名", "1990-01-01", "广东汕头", "\n", "|"):
        assert forbidden not in serialized
    assert record["event_code"] == "unknown_event"


def test_public_logger_uses_stream_only_and_creates_no_log_file(monkeypatch, tmp_path):
    import logging
    import utils.logger as safe_logger

    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    monkeypatch.setattr(safe_logger, "LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(safe_logger, "LOG_PATH", str(tmp_path / "logs" / "app.log"))
    logger = logging.getLogger("命数研究室")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    safe_logger.get_logger().info("safe")

    assert not (tmp_path / "logs" / "app.log").exists()
