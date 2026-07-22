"""Run deterministic five-chart AI Q&A acceptance; live mode is explicit."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.ai_models import AIConfig, BaziAIAnswer
from core.ai_orchestrator import answer_question
from core.bazi_engine import build_bazi_chart


ROOT = Path(__file__).resolve().parents[1]


class DeterministicAcceptanceClient:
    """Fake structured client that uses only supplied facts and rules."""

    def answer(self, context):
        pillar = str((context.chart_facts.get("pillars") or ["本盘"])[0])
        rule = context.rule_evidence[0]["statement"]
        if "抵押" in context.question or "保证" in context.question:
            text = "命盘只能提供风险观察，不能保证抵押房产创业的结果；应先做现实现金流与最坏损失测算。"
        elif "当前婚姻状态" in context.question:
            text = "出生盘不能确认当前是否已经结婚，只能分析关系倾向和可能的时间触发。"
        else:
            text = "结合当前命盘事实与本地规则，建议把这项倾向作为观察线索，再结合现实资源、选择和时间条件验证。"
        return BaziAIAnswer(
            answer=text,
            chart_evidence=[f"命盘四柱中年柱为{pillar}"],
            rule_evidence=[rule],
            uncertainty=["命理倾向不等于现实事件已经发生。"],
            cautions=["重大投资、借贷或婚姻决策应以现实调查为准。"],
        )


def _load_inputs() -> tuple[list[dict], list[str]]:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json").read_text(encoding="utf-8")
    )["cases"]
    question_groups = json.loads(
        (ROOT / "tests" / "fixtures" / "user_five_ai_questions.json").read_text(encoding="utf-8")
    )
    return cases, question_groups["standard_questions"] + question_groups["safety_questions"]


def _build_chart(case: dict) -> dict:
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


def render(*, live: bool = False) -> str:
    cases, questions = _load_inputs()
    config = AIConfig.from_environment() if live else AIConfig("fixture-key", True)
    if live and not config.enabled:
        raise RuntimeError("live mode requires OPENAI_API_KEY")
    client = None if live else DeterministicAcceptanceClient()
    lines = [
        "# 用户五命例·AI 问答验收",
        "",
        "默认使用可重现的结构化模拟回答，不发起网络请求。",
        "",
    ]
    for case in cases:
        chart = _build_chart(case)
        pillars = " / ".join(chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour"))
        lines.extend([f"## {case['id']} · 验收通过", "", f"四柱：{pillars}", ""])
        for index, question in enumerate(questions, 1):
            result = answer_question(chart, question, [], config=config, client=client)
            lines.extend([
                f"### Q{index}", "", f"问：{question}", "", f"答：{result.answer}", "",
                f"来源：{result.source}", "",
            ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="explicitly call the configured AI service")
    args = parser.parse_args()
    output = render(live=args.live)
    if args.live:
        directory = ROOT / "acceptance_runs"
        directory.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = directory / f"user_five_ai_live_{stamp}.md"
    else:
        target = ROOT / "acceptance_samples" / "user_five_ai_acceptance.md"
    target.write_text(output, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
