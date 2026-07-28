from __future__ import annotations

from datetime import datetime

import pytest


def _lunar_1999_chart():
    from core.bazi_engine import build_bazi_chart
    from core.birth_input_preview import BirthFormInput

    return build_bazi_chart(
        BirthFormInput(
            name="PRIVATE-NAME",
            gender="男",
            calendar="lunar",
            year=1999,
            month=7,
            day=1,
            hour=10,
            minute=0,
            is_leap_month=False,
            birth_place="PRIVATE-PLACE",
            time_label="巳时",
        ).to_profile()
    )


def test_monthly_question_compiles_only_requested_year_and_months():
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    chart = _lunar_1999_chart()
    resolved = resolve_question(
        "明年每个月财运如何", now=datetime(2026, 7, 28)
    )

    packet = compile_fact_packet(chart, resolved)

    texts = [item.text for item in packet.facts]
    assert any("2027" in text and "丁未" in text for text in texts)
    assert sum(item.kind == "month" for item in packet.facts) == 12
    assert all(
        "2027年" in item.text
        for item in packet.facts
        if item.kind == "month"
    )
    serialized = packet.model_dump_json()
    assert "PRIVATE-NAME" not in serialized
    assert "PRIVATE-PLACE" not in serialized
    assert "birth_date" not in serialized
    assert "birth_place" not in serialized


def test_fact_packet_redacts_identity_and_birth_details_from_resolved_question():
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    resolved = resolve_question(
        (
            "姓名：张三，出生日期1999-08-11 10:00，"
            "出生地：上海，明年每个月财运如何"
        ),
        now=datetime(2026, 7, 28),
    )

    packet = compile_fact_packet(_lunar_1999_chart(), resolved)
    serialized = packet.model_dump_json()

    assert "张三" not in serialized
    assert "1999-08-11" not in serialized
    assert "10:00" not in serialized
    assert "上海" not in serialized
    assert "财运" in packet.resolved.safe_question
    assert packet.resolved.target_years == [2027]
    assert packet.resolved.target_months == list(range(1, 13))


def test_unresolved_age_ambiguity_blocks_age_facts():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question(
        "30岁以后什么时候走财运", now=datetime(2026, 7, 28)
    )

    assert resolved.ambiguity
    with pytest.raises(FactCompilationError):
        compile_fact_packet(synthetic_chart(), resolved)


def test_explicit_solar_age_maps_to_local_date_range_and_covering_dayun():
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    resolved = resolve_question(
        "30周岁以后什么时候走财运", now=datetime(2026, 7, 28)
    )

    packet = compile_fact_packet(_lunar_1999_chart(), resolved)
    age_text = " ".join(item.text for item in packet.facts if item.kind == "age")
    dayun_text = " ".join(item.text for item in packet.facts if item.kind == "dayun")

    assert "30周岁" in age_text
    assert "2029-08-11至2030-08-10" in age_text
    assert "己巳" in dayun_text
    assert "2020-08-24至2030-08-24" in dayun_text


def test_explicit_nominal_age_maps_to_local_calendar_year():
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    resolved = resolve_question(
        "30虚岁以后什么时候走财运", now=datetime(2026, 7, 28)
    )

    packet = compile_fact_packet(_lunar_1999_chart(), resolved)
    age_text = " ".join(item.text for item in packet.facts if item.kind == "age")

    assert "30虚岁" in age_text
    assert "2028-01-01至2028-12-31" in age_text
