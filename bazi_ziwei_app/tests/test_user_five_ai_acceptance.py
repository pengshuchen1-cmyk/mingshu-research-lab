from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads(
    (ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json").read_text(encoding="utf-8")
)["cases"]
QUESTIONS = json.loads(
    (ROOT / "tests" / "fixtures" / "user_five_ai_questions.json").read_text(encoding="utf-8")
)
TRACKED_ARTIFACT = ROOT / "acceptance_samples" / "user_five_ai_acceptance.md"


def _acceptance_controller():
    from core.ai_request_control import AIRequestController

    return AIRequestController(
        per_minute=200,
        daily_requests=200,
        daily_tokens=500_000,
        max_concurrent=4,
    )


def _assert_artifact_current(path: Path, rendered: str) -> None:
    assert path.read_text(encoding="utf-8") == rendered


def _chart(case: dict) -> dict:
    from core.bazi_engine import build_bazi_chart

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
    return build_bazi_chart(profile)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_all_six_ai_questions_are_grounded_for_each_user_chart(case):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from scripts.run_user_five_ai_acceptance import KimiAcceptanceClient

    chart = _chart(case)
    client = KimiAcceptanceClient()
    controller = _acceptance_controller()
    answers = []
    for question in QUESTIONS["standard_questions"] + QUESTIONS["safety_questions"]:
        result = answer_question(
            chart,
            question,
            [],
            config=AIConfig("fixture-key", True),
            client=client,
            request_controller=controller,
            session_id=f"offline-six-question-{case['id']}",
        )
        answers.append(result)
        assert result.source == "cloud_validated"
        assert result.sections == {}
        assert result.answer.strip()
        assert "### 分析结论" not in result.answer
        assert result.chart_evidence
        assert result.rule_evidence
        assert result.timing_conditions
        assert result.practical_advice
        assert result.uncertainty
        assert result.degraded_reason is None
        assert not any(term in result.answer for term in ("一定会", "肯定发财", "保证成功"))

    assert "不能保证" in answers[-2].answer
    assert "单凭八字，不能确认现实中的婚姻登记状态" in answers[-1].answer
    assert len(client.completions.calls) == 6
    assert len(client.contexts) == 6
    for call, context in zip(client.completions.calls, client.contexts):
        assert call["model"] == "kimi-k3"
        assert call["response_format"]["type"] == "json_schema"
        assert call["stream"] is False
        payload = json.loads(call["messages"][1]["content"])
        assert set(payload) == {
            "allowed_claim_ids",
            "fact_packet",
            "analysis_plan",
        }
        assert payload["fact_packet"]["facts"]
        assert payload["analysis_plan"]["claims"]
        expected_claim_ids = [
            claim.id for claim in context.analysis_plan.claims
        ]
        assert payload["allowed_claim_ids"] == expected_claim_ids
        claim_items = call["response_format"]["json_schema"]["schema"][
            "$defs"
        ]["CloudSegment"]["properties"]["claim_ids"]["items"]
        assert claim_items["enum"] == expected_claim_ids


def test_five_chart_ai_acceptance_renderer_is_deterministic():
    import scripts.run_user_five_ai_acceptance as acceptance

    first = acceptance.render()
    second = acceptance.render()

    assert first == second
    assert first.count("## U0") == 5
    assert first.count("验收通过") == 5
    assert "不能保证" in first
    assert "单凭八字，不能确认现实中的婚姻登记状态" in first
    assert "答：###" not in first
    assert "\n答：\n\n结合当前命盘事实与本地规则" in first
    for title in (
        "分析结论",
        "命盘依据",
        "规则依据",
        "阶段与触发条件",
        "现实建议",
        "不确定性与限制",
    ):
        assert f"#### {title}\n" not in first
        assert f"\n### {title}\n" not in first
    _assert_artifact_current(TRACKED_ARTIFACT, first)


def test_stale_five_chart_ai_artifact_fails_currentness_check(tmp_path):
    stale = tmp_path / "user_five_ai_acceptance.md"
    stale.write_text("stale content\n", encoding="utf-8")

    with pytest.raises(AssertionError):
        _assert_artifact_current(stale, "fresh content\n")


def test_five_chart_ai_acceptance_script_runs_to_explicit_temporary_output(
    tmp_path,
):
    import scripts.run_user_five_ai_acceptance as acceptance

    tracked_before = TRACKED_ARTIFACT.read_bytes()
    target = tmp_path / "user_five_ai_acceptance.md"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_user_five_ai_acceptance.py",
            "--output",
            str(target),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert str(target) in completed.stdout
    output = target.read_text(encoding="utf-8")
    assert output == acceptance.render()
    assert output.count("来源：cloud_validated") == 30
    assert "rate_limited" not in output
    assert TRACKED_ARTIFACT.read_bytes() == tracked_before


def test_live_acceptance_without_credentials_names_supported_providers(monkeypatch):
    from scripts.run_user_five_ai_acceptance import render

    for name in (
        "MINGSHU_AI_PROVIDER",
        "MOONSHOT_API_KEY",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(
        RuntimeError,
        match="live mode requires configured Kimi/OpenAI API credentials",
    ):
        render(live=True)


def test_live_acceptance_does_not_inject_offline_request_controls(monkeypatch):
    from types import SimpleNamespace

    from core.ai_models import AIConfig
    import scripts.run_user_five_ai_acceptance as acceptance

    captured = []

    def fake_answer_question(chart, question, history, **kwargs):
        captured.append(kwargs)
        return SimpleNamespace(answer="live answer", source="cloud_validated")

    monkeypatch.setattr(
        acceptance.AIConfig,
        "from_environment",
        lambda: AIConfig("live-key", True),
    )
    monkeypatch.setattr(acceptance, "answer_question", fake_answer_question)

    acceptance.render(live=True)

    assert len(captured) == 30
    assert all("request_controller" not in kwargs for kwargs in captured)
    assert all("session_id" not in kwargs for kwargs in captured)


@pytest.mark.parametrize(
    "question",
    (
        "她目前结婚了吗？",
        "现在已婚吗？",
        "当前未婚，想问姻缘",
        "目前是否结婚？",
        "现在有没有结婚？",
    ),
)
def test_current_marriage_status_variants_trigger_safe_acceptance_answer(question):
    from core.ai_models import AIConfig
    from core.ai_orchestrator import answer_question
    from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient

    result = answer_question(
        _chart(CASES[0]),
        question,
        [],
        config=AIConfig("fixture-key", True),
        client=DeterministicAcceptanceClient(),
        request_controller=_acceptance_controller(),
        session_id=f"offline-marriage-variant-{question}",
    )

    assert "单凭八字，不能确认现实中的婚姻登记状态" in result.answer
