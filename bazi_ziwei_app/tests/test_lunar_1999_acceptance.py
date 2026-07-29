from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "lunar_1999_bazi_case.json").read_text(encoding="utf-8")
)


def _acceptance_controller():
    from core.ai_request_control import AIRequestController

    return AIRequestController(
        per_minute=20,
        daily_requests=20,
        daily_tokens=500_000,
        max_concurrent=4,
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
        request_controller=_acceptance_controller(),
        session_id="lunar-1999-cloud-and-local",
    )
    local = answer_question(
        chart,
        "目前是否结婚？",
        [],
        config=AIConfig("", False),
        client=DeterministicAcceptanceClient(),
        request_controller=_acceptance_controller(),
        session_id="lunar-1999-cloud-and-local",
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
        request_controller=_acceptance_controller(),
        session_id="lunar-1999-privacy",
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


def test_dayun_finance_question_receives_canonical_local_periods():
    from core.ai_models import (
        AIConfig,
        CloudBaziAnalysis,
        CloudGeneration,
    )
    from core.ai_orchestrator import answer_question

    class CapturingClient:
        def __init__(self):
            self.contexts = []

        def answer(self, context):
            self.contexts.append(context)
            return CloudGeneration(
                analysis=CloudBaziAnalysis(
                        segments=[
                            {
                                "claim_ids": [
                                    claim.id
                                    for claim in context.analysis_plan.claims
                                    if any(
                                        pillar in claim.local_text
                                        for pillar in ("己巳", "戊辰")
                                    )
                                ],
                            "text": (
                                "2030年开始进入戊辰正财大运，约31岁起。"
                                "此前2020—2029年的己巳偏财大运，"
                                "更偏机会型收入；进入戊辰后，"
                                "财务主题转向稳定现金流和长期经营。"
                            ),
                        }
                    ]
                )
            )

    client = CapturingClient()
    result = answer_question(
        _formal_chart(),
        "这个八字在几年后开始走正财大运",
        [],
        config=AIConfig("fixture-key", True),
        client=client,
        request_controller=_acceptance_controller(),
        session_id="lunar-1999-dayun",
    )

    assert result.source == "cloud_validated"
    assert len(client.contexts) == 1
    context = client.contexts[0]
    assert context.category == "wealth"
    assert context.requires_timing is True
    assert context.question == "这个八字在几年后开始走正财大运"
    target_period = next(
        item
        for item in context.chart_facts["dayun_periods"]
        if item["pillar"] == "戊辰"
    )
    assert {
        "pillar": target_period["pillar"],
        "start_age": target_period["start_age"],
        "end_age": target_period["end_age"],
        "start_year": target_period["start_year"],
        "end_year": target_period["end_year"],
        "ten_god": target_period["ten_god"],
    } == {
        "pillar": "戊辰",
        "start_age": 31,
        "end_age": 40,
        "start_year": 2030,
        "end_year": 2039,
        "ten_god": "正财",
    }
    assert target_period["branch_hidden_stems"] == [
        {"stem": "戊", "element": "土", "ten_god": "正财"},
        {"stem": "乙", "element": "木", "ten_god": "比肩"},
        {"stem": "癸", "element": "水", "ten_god": "偏印"},
    ]

    serialized = context.model_dump_json()
    for forbidden in (
        "lunar_year",
        "solar_datetime",
        "birth_date",
        "birth_place",
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
    import scripts.render_lunar_1999_acceptance as receipt

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
        "\n"
        "## 验收边界\n"
        "\n"
        "真实云端调用：0 次（仅使用离线 Kimi 模拟客户端）\n"
        "命例仅用于验收，不会进入生产规则或提示\n"
    )

    assert receipt.render() == expected
    assert receipt.render() == expected
    assert receipt.OUTPUT.read_text(encoding="utf-8") == expected


def test_lunar_1999_script_writes_the_complete_boundary_receipt(
    tmp_path,
    monkeypatch,
):
    import scripts.render_lunar_1999_acceptance as receipt

    target = tmp_path / "lunar-1999.md"
    monkeypatch.setattr(receipt, "OUTPUT", target)

    receipt.main()

    rendered = target.read_text(encoding="utf-8")
    assert rendered == receipt.render()
    assert "真实云端调用：0 次" in rendered
    assert "命例仅用于验收，不会进入生产规则或提示" in rendered


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
