from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.bazi_engine import build_bazi_chart
from core.luck_engine import get_luck_cycles


APPROVED_FIELDS = [
    "时间模式", "四柱计算依据", "起运方向", "起运时间",
    "强弱证据", "格局", "财运", "姻缘",
]
FIXTURE = ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json"
OUTPUT = ROOT / "acceptance_samples" / "user_five_bazi_acceptance.md"


def build_case(case: dict):
    hour, minute = (int(item) for item in case["time"].split(":"))
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
    if case.get("time_range_note"):
        profile["time_range_note"] = case["time_range_note"]
    chart = build_bazi_chart(profile)
    luck = get_luck_cycles(profile, chart)
    return chart, luck


def render() -> str:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    lines = [
        "# 用户五命例·统一四柱规则验收",
        "",
        "本文件由生产引擎和固定验收输入生成；客户摘要仅含批准的八项字段。",
        "",
    ]
    for case in cases:
        chart, _luck = build_case(case)
        pillars = " / ".join(
            chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
        )
        lines.extend([f"## {case['id']}", "", f"四柱：{pillars}", ""])
        for field in APPROVED_FIELDS:
            value = chart["public_summary"][field]
            if isinstance(value, list):
                value = "；".join(str(item) for item in value)
            lines.append(f"- {field}：{value}")
        if case.get("time_range_note"):
            lines.append(f"- 时间范围备注：{case['time_range_note']}")
        if case.get("boundary_note"):
            lines.append(f"- 边界备注：{case['boundary_note']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
