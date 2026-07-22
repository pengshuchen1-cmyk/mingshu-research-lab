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
        "event_code", "category", "model_alias", "latency_bucket", "reason_code"
    }
    assert record["latency_bucket"] == "3-10s"
    serialized = repr(record)
    for forbidden in ("抵押房子", "不能保证", "1996-09-04"):
        assert forbidden not in serialized


def test_ai_log_event_codes_are_restricted():
    from utils.logger import build_ai_log_record

    record = build_ai_log_record(event_code="question:\u91d1丝雀", category="other")
    assert record["event_code"] == "AI_QA_UNKNOWN"
