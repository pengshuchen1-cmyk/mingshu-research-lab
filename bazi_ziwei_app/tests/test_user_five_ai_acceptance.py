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
    from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient

    chart = _chart(case)
    client = DeterministicAcceptanceClient()
    answers = []
    for question in QUESTIONS["standard_questions"] + QUESTIONS["safety_questions"]:
        result = answer_question(
            chart,
            question,
            [],
            config=AIConfig("fixture-key", True),
            client=client,
        )
        answers.append(result)
        assert result.source == "cloud_validated"
        assert len(result.sections) == 6
        assert result.chart_evidence
        assert result.rule_evidence
        assert result.timing_conditions
        assert result.practical_advice
        assert result.uncertainty
        assert result.degraded_reason is None
        assert not any(term in result.answer for term in ("一定会", "肯定发财", "保证成功"))

    assert "不能保证" in answers[-2].answer
    assert "不能确认当前是否已经结婚" in answers[-1].answer


def test_five_chart_ai_acceptance_renderer_is_deterministic():
    from scripts.run_user_five_ai_acceptance import render

    first = render()
    second = render()

    assert first == second
    assert first.count("## U0") == 5
    assert first.count("验收通过") == 5
    assert "不能保证" in first
    assert "不能确认当前是否已经结婚" in first


def test_five_chart_ai_acceptance_script_runs_from_project_root():
    completed = subprocess.run(
        [sys.executable, "scripts/run_user_five_ai_acceptance.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "acceptance_samples/user_five_ai_acceptance.md" in completed.stdout


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
    )

    assert "不能确认当前是否已经结婚" in result.answer
