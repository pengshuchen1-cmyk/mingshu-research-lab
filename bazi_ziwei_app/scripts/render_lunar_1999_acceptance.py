"""Render the deterministic, offline acceptance receipt for the L1999 case."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ai_models import AIConfig
from core.ai_orchestrator import answer_question
from core.bazi_engine import build_bazi_chart
from core.birth_input_preview import BirthFormInput, build_birth_preview
from scripts.run_user_five_ai_acceptance import DeterministicAcceptanceClient


FIXTURE = ROOT / "tests" / "fixtures" / "lunar_1999_bazi_case.json"
OUTPUT = ROOT / "acceptance_samples" / "lunar_1999_input_ai_acceptance.md"
SIX_SECTION_TITLES = [
    "分析结论",
    "命盘依据",
    "规则依据",
    "阶段与触发条件",
    "现实建议",
    "不确定性与限制",
]


def _case() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _birth_input(case: dict) -> BirthFormInput:
    hour, minute = (int(value) for value in case["time"].split(":"))
    return BirthFormInput(
        name="L1999-RAW-NAME",
        gender="男",
        calendar=case["calendar"],
        year=int(case["date"][:4]),
        month=int(case["date"][5:7]),
        day=int(case["date"][8:10]),
        hour=hour,
        minute=minute,
        is_leap_month=case["is_leap_month"],
        birth_place="L1999-RAW-PLACE",
        time_label=case["time_label"],
    )


def render() -> str:
    case = _case()
    birth_input = _birth_input(case)
    preview = build_birth_preview(birth_input)
    chart = build_bazi_chart(birth_input.to_profile())
    formal_pillars = tuple(
        chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
    )
    expected_pillars = tuple(case["expected_pillars"])
    if (
        preview.solar_datetime != f"{case['expected_solar_date']} {case['time']}"
        or preview.pillars != expected_pillars
        or formal_pillars != expected_pillars
        or preview.chart_fingerprint != chart["chart_fingerprint_v2"]
    ):
        raise RuntimeError("L1999 preview and formal chart acceptance failed")

    raw_question = (
        "姓名：L1999-QUESTION-NAME，出生日期1999-08-11 10:00，"
        "出生地：L1999-QUESTION-PLACE，目前是否结婚？"
    )
    client = DeterministicAcceptanceClient()
    cloud = answer_question(
        chart,
        raw_question,
        [],
        config=AIConfig("fixture-key", True),
        client=client,
    )
    if (
        cloud.source != "cloud_validated"
        or list(cloud.sections) != SIX_SECTION_TITLES
        or not all(cloud.sections.values())
    ):
        raise RuntimeError("L1999 cloud structured acceptance failed")

    local = answer_question(
        chart,
        "目前是否结婚？",
        [],
        config=AIConfig("", False),
    )
    if (
        local.source != "local_rules"
        or local.degraded_reason != "missing_api_key"
        or list(local.sections) != SIX_SECTION_TITLES
        or not all(local.sections.values())
    ):
        raise RuntimeError("L1999 local fallback acceptance failed")

    if len(client.contexts) != 1:
        raise RuntimeError("L1999 cloud request context acceptance failed")
    context = client.contexts[0]
    serialized = context.model_dump_json()
    forbidden = (
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
    )
    if any(value in serialized for value in forbidden):
        raise RuntimeError("L1999 privacy acceptance failed")

    pillars_text = " / ".join(preview.pillars)
    return (
        "# 1999 农历命例·输入与问答验收\n"
        "\n"
        f"原始输入：{preview.input_text}\n"
        f"标准时间：中国标准时间 {preview.solar_datetime}\n"
        f"四柱预览：{pillars_text}\n"
        "预览与正式命盘：一致\n"
        "云端结构化模拟：通过\n"
        "本地完整降级：通过\n"
        "隐私边界：通过\n"
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
