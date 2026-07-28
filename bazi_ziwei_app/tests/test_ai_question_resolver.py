from datetime import datetime

import pytest


NOW = datetime(2026, 7, 28, 12, 0)


@pytest.mark.parametrize(
    ("question", "years", "months", "scope", "depth"),
    [
        ("明年财运怎么样", [2027], [], "target_year", "single_year"),
        ("三年后事业怎么样", [2029], [], "target_year", "single_year"),
        ("未来五年财运", [2026, 2027, 2028, 2029, 2030], [], "year_range", "long_range"),
        ("2027到2032财运走势", list(range(2027, 2033)), [], "year_range", "long_range"),
        ("明年每个月财运", [2027], list(range(1, 13)), "month_range", "monthly"),
        ("下半年财运", [2026], list(range(7, 13)), "month_range", "monthly"),
        ("30岁以后什么时候走财运", [], [], "age", "long_range"),
    ],
)
def test_resolve_common_time_phrases(question, years, months, scope, depth):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.target_years == years
    assert result.target_months == months
    assert result.time_scope == scope
    assert result.requested_depth == depth


def test_follow_up_inherits_previous_domain_and_year():
    from core.ai_question_resolver import resolve_question

    previous = resolve_question("2027年财运怎么样", now=NOW)
    result = resolve_question("那每个月呢", now=NOW, previous=previous)

    assert result.domain == "wealth"
    assert result.target_years == [2027]
    assert result.target_months == list(range(1, 13))


def test_reversed_year_range_requests_clarification():
    from core.ai_question_resolver import resolve_question

    result = resolve_question("2032到2027财运走势", now=NOW)

    assert result.target_years == []
    assert result.ambiguity == "年份范围的起止顺序需要确认。"


@pytest.mark.parametrize(
    ("question", "age_mode"),
    [
        ("30周岁以后什么时候走财运", "solar_age"),
        ("30虚岁以后什么时候走财运", "nominal_age"),
    ],
)
def test_explicit_age_mode_is_recorded(question, age_mode):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.age_values == [30]
    assert result.age_mode == age_mode
    assert result.ambiguity == ""
