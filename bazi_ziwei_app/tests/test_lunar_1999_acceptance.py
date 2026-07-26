from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "lunar_1999_bazi_case.json").read_text(encoding="utf-8")
)
def _birth_input():
    from core.birth_input_preview import BirthFormInput

    hour, minute = (int(value) for value in FIXTURE["time"].split(":"))
    return BirthFormInput(
        name="L1999-RAW-NAME",
        gender="男",
        calendar=FIXTURE["calendar"],
        year=1999,
        month=7,
        day=1,
        hour=hour,
        minute=minute,
        is_leap_month=FIXTURE["is_leap_month"],
        birth_place="L1999-RAW-PLACE",
        time_label=FIXTURE["time_label"],
    )


def _formal_chart() -> dict:
    from core.bazi_engine import build_bazi_chart

    return build_bazi_chart(_birth_input().to_profile())


def test_lunar_1999_input_preview_and_formal_chart_share_authoritative_fingerprint():
    from core.birth_input_preview import build_birth_preview

    preview = build_birth_preview(_birth_input())
    chart = _formal_chart()
    pillars = tuple(
        chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
    )

    assert preview.input_text == "农历1999年七月初一，非闰月，男，巳时"
    assert preview.solar_datetime == "1999-08-11 10:00"
    assert preview.pillars == tuple(FIXTURE["expected_pillars"])
    assert chart["profile"]["birth_date"] == FIXTURE["expected_solar_date"]
    assert pillars == preview.pillars
    assert chart["chart_fingerprint_v2"] == preview.chart_fingerprint


def test_lunar_1999_cloud_and_no_key_paths_return_guarded_adaptive_answers():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient

    chart = _formal_chart()
    cloud = answer_question(
        chart,
        "目前是否结婚？",
        [],
        config=AIConfig("fixture-key", True),
        client=DeterministicAcceptanceClient(),
    )
    local = answer_question(
        chart,
        "目前是否结婚？",
        [],
        config=AIConfig("", False),
        client=DeterministicAcceptanceClient(),
    )

    assert cloud.source == "cloud_validated"
    assert cloud.sections == {}
    assert cloud.answer.strip()
    assert "### 分析结论" not in cloud.answer
    assert "单凭八字，不能确认现实中的婚姻登记状态" in cloud.answer
    assert cloud.degraded_reason is None

    assert local.source == "local_rules"
    assert local.sections == {}
    assert local.answer.strip()
    assert "### 分析结论" not in local.answer
    assert local.degraded_reason == "missing_api_key"
    assert "不能确认现实中的婚姻登记状态" in local.answer


def test_lunar_1999_cloud_context_serialization_excludes_raw_birth_and_identity():
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient

    client = DeterministicAcceptanceClient()
    result = answer_question(
        _formal_chart(),
        (
            "姓名：L1999-QUESTION-NAME，出生日期1999-08-11 10:00，"
            "出生地：L1999-QUESTION-PLACE，目前是否结婚？"
        ),
        [],
        config=AIConfig("fixture-key", True),
        client=client,
    )
    assert result.source == "cloud_validated"
    assert len(client.contexts) == 1
    context = client.contexts[0]
    assert "当前婚姻状态" in context.question
    serialized = context.model_dump_json()

    for forbidden in (
        "L1999-RAW-NAME",
        "L1999-RAW-PLACE",
        "L1999-QUESTION-NAME",
        "L1999-QUESTION-PLACE",
        "1999-07-01",
        "1999-08-11",
        "10:00",
        '"name"',
        "birth_date",
        "birth_place",
        "lunar_birth_date",
    ):
        assert forbidden not in serialized


def test_original_five_case_chain_remains_exact_and_passing():
    from core.bazi_engine import build_bazi_chart

    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json").read_text(
            encoding="utf-8"
        )
    )["cases"]
    assert [case["id"] for case in cases] == ["U01", "U02", "U03", "U04", "U05"]

    for case in cases:
        hour, minute = (int(value) for value in case["time"].split(":"))
        profile = {
            "gender": "女" if case["gender"] == "female" else "男",
            "calendar_type": case["calendar"],
            "birth_date": case["date"],
            "birth_hour": hour,
            "birth_minute": minute,
            "time_mode": "china_standard",
        }
        if case["calendar"] == "lunar":
            profile["lunar_birth_date"] = case["date"]
        chart = build_bazi_chart(profile)
        pillars = [
            chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
        ]
        assert chart["profile"]["birth_date"] == case["expected_solar_date"]
        assert pillars == case["expected_pillars"]


def test_lunar_1999_receipt_renderer_is_exact_and_deterministic():
    from scripts.render_lunar_1999_acceptance import OUTPUT, render

    expected = (
        "# 1999 农历命例·输入与问答验收\n"
        "\n"
        "原始输入：农历1999年七月初一，非闰月，男，巳时\n"
        "标准时间：中国标准时间 1999-08-11 10:00\n"
        "四柱预览：己卯 / 壬申 / 乙未 / 辛巳\n"
        "预览与正式命盘：一致\n"
        "云端自然回答模拟：通过\n"
        "本地完整降级：通过\n"
        "隐私边界：通过\n"
    )

    assert render() == expected
    assert render() == expected
    assert OUTPUT.read_text(encoding="utf-8") == expected


def test_lunar_1999_receipt_privacy_verdict_uses_actual_cloud_context(monkeypatch):
    import scripts.render_lunar_1999_acceptance as receipt
    from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient

    class LeakyAcceptanceClient(DeterministicAcceptanceClient):
        def answer(self, context):
            answer = super().answer(context)
            self.contexts[-1] = context.model_copy(
                update={"question": "L1999-QUESTION-NAME"}
            )
            return answer

    monkeypatch.setattr(receipt, "DeterministicAcceptanceClient", LeakyAcceptanceClient)

    with pytest.raises(RuntimeError, match="privacy acceptance failed"):
        receipt.render()
