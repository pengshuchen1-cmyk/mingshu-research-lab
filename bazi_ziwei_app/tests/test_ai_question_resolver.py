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


@pytest.mark.parametrize(
    "question",
    (
        "2020到2080财运走势",
        "、".join(f"{year}年" for year in range(2020, 2081)) + "财运走势",
        "未来六十一年财运走势",
    ),
)
def test_more_than_sixty_target_years_returns_safe_ambiguity(question):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.target_years == []
    assert result.ambiguity == "目标年份数量超过60个，请缩小时间范围。"


def test_reversed_range_does_not_inherit_previous_years():
    from core.ai_question_resolver import resolve_question

    previous = resolve_question("2027年财运怎么样", now=NOW)
    result = resolve_question("那2032到2027年呢", now=NOW, previous=previous)

    assert result.target_years == []
    assert result.ambiguity == "年份范围的起止顺序需要确认。"


@pytest.mark.parametrize(
    ("question", "months", "ambiguity"),
    [
        ("那2032到2027年每个月财运呢", list(range(1, 13)), "年份范围的起止顺序需要确认。"),
        ("那2080到2020年上半年财运呢", list(range(1, 7)), "年份范围的起止顺序需要确认。"),
        ("那2020到2080年3月财运呢", [3], "目标年份数量超过60个，请缩小时间范围。"),
    ],
)
def test_invalid_year_ranges_never_receive_month_fallback_or_receipts(
    question, months, ambiguity
):
    from core.ai_question_resolver import resolve_question

    previous = resolve_question("2027年财运怎么样", now=NOW)
    result = resolve_question(question, now=NOW, previous=previous)

    assert result.target_years == []
    assert result.target_months == months
    assert result.ambiguity == ambiguity
    assert result.interpretation_receipt == ""


@pytest.mark.parametrize("question", ("2027年3月财运", "明年三月财运"))
def test_explicit_month_resolves_to_single_month(question):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.target_years == [2027]
    assert result.target_months == [3]
    assert result.time_scope == "month_range"
    assert result.requested_depth == "monthly"


@pytest.mark.parametrize(
    ("question", "months", "label"),
    [
        ("2027年3月财运", [3], "3月"),
        ("明年上半年财运", list(range(1, 7)), "上半年（1—6月）"),
        ("明年下半年财运", list(range(7, 13)), "下半年（7—12月）"),
        ("明年每月财运", list(range(1, 13)), "每月（1—12月）"),
    ],
)
def test_month_receipt_states_the_resolved_month_scope(question, months, label):
    from core.ai_question_resolver import resolve_question
    from core.yearly_engine import get_year_pillar

    result = resolve_question(question, now=NOW)

    assert result.target_months == months
    assert result.interpretation_receipt == (
        f"本次按2027年（{get_year_pillar(2027)}）{label}分析。"
    )


def test_continuous_year_range_receipt_lists_all_years_and_pillars_when_it_fits():
    from core.ai_question_resolver import resolve_question
    from core.yearly_engine import get_year_pillar

    result = resolve_question("2027到2032年财运", now=NOW)

    entries = "、".join(
        f"{year}年（{get_year_pillar(year)}）" for year in range(2027, 2033)
    )
    assert result.interpretation_receipt == (
        f"本次按2027年（{get_year_pillar(2027)}）至2032年"
        f"（{get_year_pillar(2032)}）的连续年份范围（共6年）逐年分析：{entries}。"
    )


def test_long_continuous_year_range_receipt_preserves_range_endpoints_and_count():
    from core.ai_question_resolver import resolve_question
    from core.yearly_engine import get_year_pillar

    result = resolve_question("2020到2079年财运", now=NOW)

    assert result.target_years == list(range(2020, 2080))
    assert result.interpretation_receipt == (
        f"本次按2020年（{get_year_pillar(2020)}）至2079年"
        f"（{get_year_pillar(2079)}）的连续年份范围（共60年）分析。"
    )


@pytest.mark.parametrize("question", ("几岁开始走财运", "几岁走运"))
def test_unspecified_age_question_requests_age_mode_clarification(question):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.time_scope == "age"
    assert result.age_values == []
    assert result.age_mode == "unspecified"
    assert result.ambiguity == "该年龄问题需要确认具体年龄及按周岁还是虚岁理解。"


def test_numeric_age_without_mode_always_requests_clarification():
    from core.ai_question_resolver import resolve_question

    result = resolve_question("30岁开始走财运", now=NOW)

    assert result.age_values == [30]
    assert result.ambiguity == "该年龄问题需要确认按周岁还是虚岁理解。"


def test_discrete_year_receipt_lists_each_requested_year_and_pillar():
    from core.ai_question_resolver import resolve_question
    from core.yearly_engine import get_year_pillar

    result = resolve_question("2027年、2029年和2031年财运", now=NOW)

    assert result.target_years == [2027, 2029, 2031]
    assert result.interpretation_receipt == (
        "本次按2027年（"
        f"{get_year_pillar(2027)}）、2029年（{get_year_pillar(2029)}）、"
        f"2031年（{get_year_pillar(2031)}）分析。"
    )


@pytest.mark.parametrize(
    "question",
    (
        "2027年财运不要逐月看",
        "2027年财运不看流月",
        "不看明年每个月，只看全年财运",
        "不要看2027年每月，只看全年财运",
    ),
)
def test_negative_monthly_words_do_not_request_monthly_analysis(question):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.target_years == [2027]
    assert result.target_months == []
    assert result.time_scope == "target_year"


def test_monthly_keyword_every_month_is_supported():
    from core.ai_question_resolver import resolve_question

    result = resolve_question("明年每月财运", now=NOW)

    assert result.target_years == [2027]
    assert result.target_months == list(range(1, 13))
    assert result.time_scope == "month_range"


def test_birth_month_is_not_interpreted_as_a_forecast_month():
    from core.ai_question_resolver import resolve_question

    result = resolve_question("我3月出生，明年财运如何", now=NOW)

    assert result.target_years == [2027]
    assert result.target_months == []
    assert result.time_scope == "target_year"


@pytest.mark.parametrize(
    ("question", "year"),
    (("明年三月财运", 2027), ("2027年3月财运", 2027), ("三月财运", 2026)),
)
def test_forecast_month_expressions_remain_supported(question, year):
    from core.ai_question_resolver import resolve_question

    result = resolve_question(question, now=NOW)

    assert result.target_years == [year]
    assert result.target_months == [3]


def test_follow_up_reference_marks_only_actual_inheritance():
    from core.ai_question_resolver import resolve_question

    previous = resolve_question("2027年财运怎么样", now=NOW)
    inherited = resolve_question("那每个月呢", now=NOW, previous=previous)
    switched = resolve_question("那2028年事业呢", now=NOW, previous=previous)
    independent = resolve_question("2028年财运如何", now=NOW, previous=previous)

    assert inherited.follow_up_reference == "wealth"
    assert switched.domain == "career"
    assert switched.follow_up_reference == ""
    assert independent.follow_up_reference == ""
