from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest


EXTENDED_DOMAIN_RULE_IDS = {
    "career": {"CAREER-STRUCTURE", "CAREER-ROLE-FIT"},
    "family": {"FAMILY-STRUCTURE", "FAMILY-BOUNDARY"},
    "health_advisory": {"HEALTH-NONDIAGNOSTIC", "HEALTH-BALANCE"},
    "children": {"CHILDREN-STRUCTURE", "CHILDREN-STATUS-UNKNOWN"},
    "education": {"EDU-LEARNING-STYLE", "EDU-TIMING"},
    "relocation": {"MOVE-ACTIVATION", "MOVE-REALITY"},
    "property": {"PROPERTY-CAPACITY", "PROPERTY-RISK"},
    "benefactor": {"BENEFACTOR-SUPPORT", "BENEFACTOR-CONDITION"},
}


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


def _minimal_luck() -> dict:
    return {
        "available": True,
        "dayun_list": [
            {
                "pillar": "甲子",
                "start_age": 1,
                "end_age": 120,
                "start_year": 2000,
                "end_year": 2099,
                "start_date": "2000-01-01",
                "end_date": "2100-01-01",
                "ten_god": "比肩",
            }
        ],
        "yearly_list": [],
    }


@pytest.mark.parametrize("domain", tuple(EXTENDED_DOMAIN_RULE_IDS))
def test_fact_packet_loads_only_the_resolved_extended_domain_rules(domain):
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_models import ResolvedQuestion
    from tests.bazi_ai_fixtures import synthetic_chart

    packet = compile_fact_packet(
        synthetic_chart(),
        ResolvedQuestion(safe_question="请分析", domain=domain),
    )

    evidence_ids = {item["id"] for item in packet.rule_evidence}
    all_extended_ids = set().union(*EXTENDED_DOMAIN_RULE_IDS.values())
    assert evidence_ids & all_extended_ids == EXTENDED_DOMAIN_RULE_IDS[domain]
    assert {
        "SAFETY-NONDETERMINISTIC",
        "SAFETY-STATUS-UNKNOWN",
    } <= evidence_ids


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


def test_monthly_fact_compilation_calls_local_month_engine_once_for_target_year():
    from core import monthly_engine
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    resolved = resolve_question(
        "明年每个月财运如何",
        now=datetime(2026, 7, 28),
    )
    with patch(
        "core.monthly_engine.analyze_monthly_fortune",
        wraps=monthly_engine.analyze_monthly_fortune,
    ) as observed_monthly:
        with patch(
            "core.ai_fact_compiler.analyze_monthly_fortune",
            new=observed_monthly,
        ):
            packet = compile_fact_packet(_lunar_1999_chart(), resolved)

    assert sum(item.kind == "month" for item in packet.facts) == 12
    assert observed_monthly.call_count == 1
    assert {call.args[1] for call in observed_monthly.call_args_list} == {2027}


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


def test_luck_engine_exception_uses_stable_error_without_sensitive_message():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("2027年财运如何", now=datetime(2026, 7, 28))
    with patch(
        "core.ai_fact_compiler.get_luck_cycles",
        side_effect=RuntimeError("PRIVATE-BIRTH-1999-08-11"),
    ):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_LUCK_ENGINE_ERROR"
    assert str(caught.value) == "FACT_LUCK_ENGINE_ERROR: 本地大运引擎暂不可用。"
    assert "PRIVATE-BIRTH" not in str(caught.value)


def test_wrong_year_engine_type_uses_stable_fact_compilation_error():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("2027年财运如何", now=datetime(2026, 7, 28))
    with (
        patch("core.ai_fact_compiler.get_luck_cycles", return_value=_minimal_luck()),
        patch("core.ai_fact_compiler.analyze_yearly_fortune", return_value=[]),
    ):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_YEAR_OUTPUT_INVALID"
    assert str(caught.value) == "FACT_YEAR_OUTPUT_INVALID: 本地流年引擎返回了无效结果。"


def test_malformed_dayun_output_uses_stable_invalid_output_error():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("大运如何", now=datetime(2026, 7, 28))
    malformed = {"available": True, "dayun_list": [{"pillar": "甲子"}]}
    with patch("core.ai_fact_compiler.get_luck_cycles", return_value=malformed):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_LUCK_OUTPUT_INVALID"


def test_year_result_without_target_pillar_is_treated_as_missing_fact():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("2027年财运如何", now=datetime(2026, 7, 28))
    with (
        patch("core.ai_fact_compiler.get_luck_cycles", return_value=_minimal_luck()),
        patch(
            "core.ai_fact_compiler.analyze_yearly_fortune",
            return_value={"year": 2027},
        ),
    ):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_YEAR_FACTS_MISSING"


def test_missing_requested_month_uses_stable_fact_compilation_error():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("2027年2月财运如何", now=datetime(2026, 7, 28))
    yearly = {"year": 2027, "pillar": "丁未", "ten_god": "劫财"}
    wrong_month = [{"month": 1, "pillar": "壬寅"}]
    with (
        patch("core.ai_fact_compiler.get_luck_cycles", return_value=_minimal_luck()),
        patch("core.ai_fact_compiler.analyze_yearly_fortune", return_value=yearly),
        patch("core.ai_fact_compiler.analyze_monthly_fortune", return_value=wrong_month),
    ):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_MONTH_FACTS_MISSING"
    assert str(caught.value) == "FACT_MONTH_FACTS_MISSING: 未找到全部目标月份事实。"


def test_malformed_month_item_uses_stable_invalid_output_error():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    resolved = resolve_question("2027年2月财运如何", now=datetime(2026, 7, 28))
    yearly = {"year": 2027, "pillar": "丁未"}
    with (
        patch("core.ai_fact_compiler.get_luck_cycles", return_value=_minimal_luck()),
        patch("core.ai_fact_compiler.analyze_yearly_fortune", return_value=yearly),
        patch(
            "core.ai_fact_compiler.analyze_monthly_fortune",
            return_value=[{"month": object(), "pillar": "壬寅"}],
        ),
    ):
        with pytest.raises(FactCompilationError) as caught:
            compile_fact_packet(synthetic_chart(), resolved)

    assert caught.value.code == "FACT_MONTH_OUTPUT_INVALID"


def test_explicit_age_requires_local_range_and_covering_dayun_facts():
    from core.ai_fact_compiler import FactCompilationError, compile_fact_packet
    from core.ai_question_resolver import resolve_question
    from tests.bazi_ai_fixtures import synthetic_chart

    chart = synthetic_chart()
    chart["profile"] = {key: value for key, value in chart["profile"].items() if key != "birth_date"}
    resolved = resolve_question("30周岁财运如何", now=datetime(2026, 7, 28))
    with pytest.raises(FactCompilationError) as missing_age:
        compile_fact_packet(chart, resolved)
    assert missing_age.value.code == "FACT_AGE_RANGE_MISSING"

    with patch(
        "core.ai_fact_compiler.get_luck_cycles",
        return_value={"available": True, "dayun_list": [], "yearly_list": []},
    ):
        with pytest.raises(FactCompilationError) as missing_dayun:
            compile_fact_packet(synthetic_chart(), resolved)
    assert missing_dayun.value.code == "FACT_DAYUN_FACTS_MISSING"


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


@pytest.mark.parametrize(
    ("question", "expected_age_range"),
    (
        ("31周岁以后什么时候走财运", "2030-08-11至2031-08-10"),
        ("32虚岁以后什么时候走财运", "2030-01-01至2030-12-31"),
    ),
)
def test_age_calendar_range_can_intersect_two_exact_dayun_periods(
    question,
    expected_age_range,
):
    from core.ai_fact_compiler import compile_fact_packet
    from core.ai_question_resolver import resolve_question

    resolved = resolve_question(question, now=datetime(2026, 7, 28))

    packet = compile_fact_packet(_lunar_1999_chart(), resolved)
    age_text = " ".join(item.text for item in packet.facts if item.kind == "age")
    dayun_text = " ".join(item.text for item in packet.facts if item.kind == "dayun")

    assert expected_age_range in age_text
    assert "己巳" in dayun_text
    assert "戊辰" in dayun_text
    assert "2020-08-24至2030-08-24" in dayun_text
    assert "2030-08-24至2040-08-24" in dayun_text


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
