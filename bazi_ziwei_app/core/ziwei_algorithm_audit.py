"""紫微算法复核摘要。

复核范围：五行局、十四主星、辅星/煞星、大限。
这里输出的是工程校验与规则链路说明，不替代真实盘例校验。
"""

from __future__ import annotations

from core.ziwei_engine import build_ziwei_chart
from core.ziwei_validation_engine import load_ziwei_validation_cases, validate_ziwei_case


BOUNDARY = "当前为算法链路复核，仍需真实盘例继续校验。"


def _failed_checks(result: dict, keyword: str | None = None) -> list[dict]:
    checks = [item for item in result.get("chart_checks", []) if not item.get("passed")]
    if keyword:
        checks = [item for item in checks if keyword in item.get("item", "")]
    return checks


def _five_element_trace(case: dict, result: dict) -> dict:
    chart = result.get("chart", {})
    expected = (case.get("expected") or {}).get("five_element_bureau", "")
    return {
        "case_id": case.get("case_id", ""),
        "name": case.get("name", ""),
        "expected": expected,
        "actual": chart.get("five_element_bureau", ""),
        "life_palace": chart.get("life_palace", ""),
        "life_palace_evidence": "；".join(chart.get("algorithm_evidence", [])),
        "status": "通过" if expected and expected == chart.get("five_element_bureau", "") else "需复核" if expected else "无预期",
    }


def audit_ziwei_algorithms() -> dict:
    """生成紫微算法复核报告。"""
    cases = load_ziwei_validation_cases()
    results = [validate_ziwei_case(case) for case in cases]
    known_results = [item for item in results if item.get("chart_checks")]
    chart_passed = [item for item in known_results if item.get("chart_status") == "盘面校验通过"]

    five_element_traces = [
        _five_element_trace(case, result)
        for case, result in zip(cases, results)
        if (case.get("expected") or {}).get("five_element_bureau")
    ]
    five_element_review_status = "通过" if all(item["status"] == "通过" for item in five_element_traces) else "需复核"

    full_star_cases = [
        result for case, result in zip(cases, results)
        if (case.get("expected") or {}).get("main_stars_by_palace")
    ]
    main_star_failed = []
    for result in full_star_cases:
        main_star_failed.extend(_failed_checks(result, "主星"))

    sample_profile = {
        "name": "算法复核样例",
        "gender": "女",
        "birth_date": "2000-06-15",
        "birth_hour": 14,
        "birth_minute": 30,
    }
    sample_chart = build_ziwei_chart(sample_profile)

    resolved_issues = []
    for case in cases:
        correction_note = case.get("correction_note", "")
        if correction_note:
            resolved_issues.append(f"{case.get('name', '')}：{correction_note}")

    return {
        "summary": {
            "known_cases": len(known_results),
            "chart_passed_cases": len(chart_passed),
            "chart_review_cases": len(known_results) - len(chart_passed),
            "resolved_issues": resolved_issues,
            "boundary": BOUNDARY,
        },
        "five_element_review": {
            "status": five_element_review_status,
            "method": "年干经五虎遁定命宫天干，再以命宫干支纳音定五行局。",
            "traces": five_element_traces,
            "boundary": BOUNDARY,
        },
        "main_star_review": {
            "status": "通过" if full_star_cases and not main_star_failed else "需更多盘例",
            "checked_cases": len(full_star_cases),
            "failed_checks": main_star_failed,
            "method": "以五行局和农历生日定紫微星，再排紫微系与天府系十四主星。",
            "boundary": BOUNDARY,
        },
        "minor_fierce_review": {
            "status": "结构通过，需盘例继续校验",
            "minor_ready": sample_chart.get("minor_stars_ready", False),
            "fierce_ready": sample_chart.get("fierce_stars_ready", False),
            "year_gan": sample_chart.get("year_gan", ""),
            "year_branch": sample_chart.get("year_branch", ""),
            "note": "辅星、煞星已使用出生年份年支，不再由年干粗略推算年支；仍需真实盘例继续校验。",
            "boundary": BOUNDARY,
        },
        "daxian_review": {
            "status": "基础结构通过，需盘例继续校验",
            "daxian_ready": sample_chart.get("daxian", {}).get("daxian_ready", False),
            "start_age": sample_chart.get("daxian", {}).get("start_age", ""),
            "stage_count": len(sample_chart.get("daxian", {}).get("stages", [])),
            "note": "大限已按五行局数字起限并生成 12 阶段；复杂飞化断事仍未接入，仍需真实盘例继续校验。",
            "boundary": BOUNDARY,
        },
    }
