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
    assert context.question == "问题类别：财运；时间维度：是；目标年份：2026年"
    assert context.history[0].content == "此前用户询问：事业"
