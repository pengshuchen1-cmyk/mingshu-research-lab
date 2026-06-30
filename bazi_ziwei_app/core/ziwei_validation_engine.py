"""紫微盘例校验引擎。

用于把“算法盘面校验”和“现实反馈校验”分开展示。
没有真实反馈的案例只标记为待补充，不把解释包装成已验证结论。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.ziwei_engine import build_ziwei_chart
from core.ziwei_readable_engine import build_ziwei_plain_guide
from core.ziwei_sihua_engine import apply_sihua_to_chart, get_sihua_by_year_gan
from core.ziwei_star_engine import get_year_gan_from_profile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_PATH = PROJECT_ROOT / "data" / "ziwei_validation_cases.json"
BOUNDARY_TEXT = "校验结果用于盘例复核，不把待验证内容当成已验证结论。"


def load_ziwei_validation_cases(path: str | Path | None = None) -> list[dict]:
    """加载紫微盘例校验数据。"""
    case_path = Path(path) if path else DEFAULT_CASE_PATH
    try:
        data = json.loads(case_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("cases", [])


def _stars_equal(left: list[str], right: list[str]) -> bool:
    return sorted(left or []) == sorted(right or [])


def _add_check(checks: list[dict], item: str, expected: Any, actual: Any, passed: bool) -> None:
    checks.append({
        "item": item,
        "expected": expected,
        "actual": actual,
        "passed": bool(passed),
        "status": "通过" if passed else "需复核",
    })


def _build_chart_checks(case: dict, chart: dict) -> list[dict]:
    expected = case.get("expected") or {}
    profile = case.get("profile", {})
    checks: list[dict] = []

    if "year_gan" in expected:
        actual = get_year_gan_from_profile(profile)
        _add_check(checks, "年干", expected.get("year_gan"), actual, actual == expected.get("year_gan"))
    if "life_palace" in expected:
        actual = chart.get("life_palace", "")
        _add_check(checks, "命宫地支", expected.get("life_palace"), actual, actual == expected.get("life_palace"))
    if "body_palace" in expected:
        actual = chart.get("body_palace", "")
        _add_check(checks, "身宫地支", expected.get("body_palace"), actual, actual == expected.get("body_palace"))
    if "five_element_bureau" in expected:
        actual = chart.get("five_element_bureau", "")
        _add_check(checks, "五行局", expected.get("five_element_bureau"), actual, actual == expected.get("five_element_bureau"))

    expected_stars = expected.get("main_stars_by_palace", {})
    actual_stars = chart.get("main_stars_by_palace", {})
    for palace, stars in expected_stars.items():
        actual = actual_stars.get(palace, [])
        _add_check(checks, f"{palace}主星", stars, actual, _stars_equal(stars, actual))

    return checks


def _build_feedback_checks(case: dict, guide: dict) -> list[dict]:
    feedback_items = case.get("real_feedback") or []
    if not feedback_items:
        return []

    guide_text = json.dumps(guide.get("focus_cards", []), ensure_ascii=False)
    checks = []
    for item in feedback_items:
        label = item.get("label", "")
        keywords = item.get("keywords", [])
        matched = [keyword for keyword in keywords if keyword and keyword in guide_text]
        checks.append({
            "label": label,
            "keywords": keywords,
            "matched_keywords": matched,
            "passed": bool(matched),
            "status": "可参考" if matched else "需人工复核",
            "note": item.get("note", ""),
        })
    return checks


def _focus_card_rows(guide: dict) -> list[dict]:
    rows = []
    for card in guide.get("focus_cards", []):
        rows.append({
            "宫位": card.get("palace_name", ""),
            "主星": "、".join(card.get("main_stars", [])) or "未见十四主星",
            "一句话": card.get("one_sentence", ""),
            "星曜组合": card.get("star_combination_text", ""),
            "落宫解释数": len(card.get("star_palace_explanations", [])),
        })
    return rows


def validate_ziwei_case(case: dict) -> dict:
    """校验单个紫微盘例。"""
    profile = case.get("profile", {})
    chart = build_ziwei_chart(profile)
    year_gan = get_year_gan_from_profile(profile)
    sihua_data = apply_sihua_to_chart(chart, get_sihua_by_year_gan(year_gan))
    guide = build_ziwei_plain_guide(chart, sihua_data.get("sihua_by_palace", {}))

    chart_checks = _build_chart_checks(case, chart)
    failed_checks = [item for item in chart_checks if not item.get("passed")]
    feedback_checks = _build_feedback_checks(case, guide)
    failed_feedback = [item for item in feedback_checks if not item.get("passed")]

    if not chart_checks:
        chart_status = "无外部盘面预期"
    elif failed_checks:
        chart_status = "盘面需复核"
    else:
        chart_status = "盘面校验通过"

    if not case.get("real_feedback"):
        feedback_status = "待补充真实反馈"
    elif failed_feedback:
        feedback_status = "反馈需人工复核"
    else:
        feedback_status = "反馈可参考"

    return {
        "case_id": case.get("case_id", ""),
        "name": case.get("name", ""),
        "profile": profile,
        "validation_scope": case.get("validation_scope", []),
        "chart": chart,
        "guide": guide,
        "chart_checks": chart_checks,
        "feedback_checks": feedback_checks,
        "focus_card_rows": _focus_card_rows(guide),
        "chart_status": chart_status,
        "feedback_status": feedback_status,
        "source_note": case.get("source_note", ""),
        "feedback_prompt": case.get("feedback_prompt", []),
        "summary": {
            "total_checks": len(chart_checks),
            "passed_checks": len(chart_checks) - len(failed_checks),
            "failed_checks": len(failed_checks),
            "feedback_checks": len(feedback_checks),
            "failed_feedback": len(failed_feedback),
        },
        "boundary": BOUNDARY_TEXT,
    }


def validate_ziwei_cases(cases: list[dict] | None = None) -> dict:
    """校验全部紫微盘例并返回汇总。"""
    case_list = cases if cases is not None else load_ziwei_validation_cases()
    results = [validate_ziwei_case(case) for case in case_list]
    known_chart_cases = [item for item in results if item.get("chart_checks")]
    chart_passed = [item for item in known_chart_cases if item.get("chart_status") == "盘面校验通过"]
    pending_feedback = [item for item in results if item.get("feedback_status") == "待补充真实反馈"]

    return {
        "summary": {
            "total_cases": len(results),
            "known_chart_cases": len(known_chart_cases),
            "chart_passed_cases": len(chart_passed),
            "chart_review_cases": len(known_chart_cases) - len(chart_passed),
            "pending_feedback_cases": len(pending_feedback),
            "next_action": "请补充现实反馈/真实反馈，用事业、财帛、夫妻等重点宫位逐项校验解释是否贴近现实。",
        },
        "cases": results,
        "boundary": BOUNDARY_TEXT,
    }
