from __future__ import annotations

import json


def test_outbound_context_contains_no_raw_profile_identity():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    chart = build_bazi_chart(
        {
            "name": "SENTINEL-NAME",
            "profile_id": "SENTINEL-ID",
            "gender": "女",
            "birth_date": "1986-08-15",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "SENTINEL-CITY",
            "longitude": 116.4,
        }
    )
    context = build_ai_context(
        build_chart_facts(chart),
        "今年财运如何？",
        [
            {"role": "user", "content": "上一问"},
            {"role": "assistant", "content": "上一答"},
        ],
    )
    payload = context.model_dump_json()

    for forbidden in (
        "SENTINEL-NAME", "SENTINEL-ID", "SENTINEL-CITY", "1986-08-15", "116.4",
        "name", "profile_id", "birth_date", "birth_place", "longitude", "database_id",
        "internal_rule_version",
    ):
        assert forbidden not in payload


def test_history_is_capped_to_six_messages_and_6000_characters():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
        )
    )
    history = [
        {"role": "user" if index % 2 == 0 else "assistant", "content": str(index) * 1500}
        for index in range(10)
    ]
    context = build_ai_context(facts, "事业如何？", history)

    assert len(context.history) <= 6
    assert sum(len(item.content) for item in context.history) <= 6000
    assert all(len(item.content) <= 4000 for item in context.history)
    assert set(json.loads(context.model_dump_json())["history"][0]) == {"role", "content"}


def test_question_and_history_redact_common_personal_identifiers():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
        )
    )
    context = build_ai_context(
        facts,
        "姓名：金丝雀，生日1996-09-04 23:45，请看2026年财运",
        [{"role": "user", "content": "邮箱 a@example.com，手机13800138000"}],
    )
    payload = context.model_dump_json()

    for forbidden in ("金丝雀", "1996-09-04", "23:45", "a@example.com", "13800138000"):
        assert forbidden not in payload
    assert "2026年" in context.question


def test_unlabelled_chinese_identity_date_and_city_never_leave_as_raw_text():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "女", "birth_date": "1986-08-15", "birth_hour": 10, "birth_minute": 0}
        )
    )
    raw = "我是金丝雀，1996年9月4日出生于上海，请看2026年财运"
    context = build_ai_context(
        facts,
        raw,
        [{"role": "user", "content": "我住在广州，叫陈小明，想问事业"}],
    )
    payload = context.model_dump_json()

    for forbidden in (raw, "金丝雀", "1996年9月4日", "上海", "广州", "陈小明"):
        assert forbidden not in payload
    assert '"year":1996' not in payload
    assert "2026年财运" in context.question
    assert "想问事业" in context.history[0].content


def test_birth_year_shorthand_is_never_mistaken_for_forecast_year():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
        )
    )
    for question in (
        "我是1996年生，想看2026年财运",
        "生于1996年，想看2026年财运",
        "1996年属鼠，想看2026年财运",
        "1996年9月4号出生，想看2026年财运",
    ):
        context = build_ai_context(facts, question, [])
        assert "1996年" not in context.question
        assert "2026年财运" in context.question
        assert context.chart_facts["target_years"] == [
            {"year": 2026, "year_pillar": "丙午"}
        ]


def test_labeled_ids_coordinates_secrets_and_logs_are_redacted():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
        )
    )
    context = build_ai_context(
        facts,
        (
            "profile_id: PROFILE-7788，database_id=DB-9911，"
            "API key：sk-secret-token，internal_rule_version=9.9.9；"
            "经度116.4074，这是sk-another-secret-token，想问2027年AI创业现金流。"
        ),
        [
            {
                "role": "user",
                "content": "说明如下，日志：customer_id=LOG-123 raw_name=李雷\n仍想问抵押房子的风险",
            }
        ],
    )
    payload = context.model_dump_json()

    for forbidden in (
        "PROFILE-7788",
        "DB-9911",
        "sk-secret-token",
        "sk-another-secret-token",
        "9.9.9",
        "116.4074",
        "LOG-123",
        "李雷",
        "profile_id",
        "database_id",
        "internal_rule_version",
    ):
        assert forbidden not in payload
    for useful in ("2027年", "AI创业", "现金流"):
        assert useful in context.question
    assert "抵押房子的风险" in context.history[0].content


def test_concrete_chinese_contact_birth_and_location_forms_are_redacted():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "女", "birth_date": "1986-08-15", "birth_hour": 10, "birth_minute": 0}
        )
    )
    context = build_ai_context(
        facts,
        (
            "我叫王小红，生日是1996年9月4日，出生地：北京市朝阳区，"
            "现居上海市，电话+86 138-0013-8000，邮箱wang@example.cn，"
            "想看2026年10月为什么事业要调整？"
        ),
        [],
    )

    for forbidden in (
        "王小红",
        "1996年9月4日",
        "北京市朝阳区",
        "上海市",
        "138-0013-8000",
        "wang@example.cn",
    ):
        assert forbidden not in context.question
    for useful in ("2026年10月", "为什么", "事业", "调整"):
        assert useful in context.question


def test_labeled_english_identity_and_lunar_birth_forms_are_redacted():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "女", "birth_date": "1986-08-15", "birth_hour": 10, "birth_minute": 0}
        )
    )
    context = build_ai_context(
        facts,
        (
            "name: Alice Smith, birth_place=Shenzhen, residence=Guangzhou；"
            "生日：农历一九九六年八月初三，出生时间：晚上十一点四十五分，"
            "想问2028年3月为什么要转向AI行业？"
        ),
        [],
    )

    for forbidden in (
        "Alice Smith",
        "Shenzhen",
        "Guangzhou",
        "农历一九九六年八月初三",
        "晚上十一点四十五分",
    ):
        assert forbidden not in context.question
    for useful in ("2028年3月", "为什么", "转向AI行业"):
        assert useful in context.question


def test_unrecognized_names_and_cities_are_dropped_by_safe_semantic_projection():
    from core.ai_context import build_ai_context
    from core.bazi_engine import build_bazi_chart
    from core.chart_facts import build_chart_facts

    facts = build_chart_facts(
        build_bazi_chart(
            {"gender": "男", "birth_date": "1994-09-23", "birth_hour": 18, "birth_minute": 0}
        )
    )
    context = build_ai_context(
        facts,
        "玄鸟从海棠城来，考虑2026年抵押房子做AI创业，因为现金流紧张，怎么办？",
        [
            {
                "role": "assistant",
                "content": "青禾在云州市说，2027年的事业转换因为现金流压力，需要注意风险。",
            }
        ],
    )
    payload = context.model_dump_json()

    for forbidden in ("玄鸟", "海棠城", "青禾", "云州市"):
        assert forbidden not in payload
    for useful in ("2026年", "抵押房子", "AI创业", "因为现金流紧张", "怎么办"):
        assert useful in context.question
    history = context.history[0].content
    for useful in ("2027年的事业转换", "因为现金流压力", "注意风险"):
        assert useful in history
