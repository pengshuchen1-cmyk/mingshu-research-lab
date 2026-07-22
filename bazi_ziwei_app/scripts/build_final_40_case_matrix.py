"""生成并校验最终收口使用的 40 组完全虚构八字命例。"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from core.bazi_constants import STEM_ELEMENTS
from core.bazi_engine import build_bazi_chart
from core.chart_fingerprint import build_chart_fingerprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "tests" / "fixtures" / "final_40_bazi_cases.json"
STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")
BRANCH_HOURS = dict(zip(BRANCHES, (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)))


BOUNDARY_SEEDS: tuple[dict[str, Any], ...] = (
    {"birth_date": "2024-02-03", "birth_hour": 23, "birth_minute": 30, "boundary_tags": ["立春前", "子时边界"]},
    {"birth_date": "2024-02-04", "birth_hour": 20, "birth_minute": 30, "boundary_tags": ["立春后"]},
    {"birth_date": "2024-03-05", "birth_hour": 10, "birth_minute": 0, "boundary_tags": ["惊蛰交接日"]},
    {"birth_date": "2024-04-04", "birth_hour": 16, "birth_minute": 0, "boundary_tags": ["清明交接日"]},
    {"birth_date": "2024-05-05", "birth_hour": 8, "birth_minute": 0, "boundary_tags": ["立夏交接日"]},
    {"birth_date": "2024-06-05", "birth_hour": 12, "birth_minute": 0, "boundary_tags": ["芒种交接日"]},
    {
        "birth_date": "1991-07-19", "birth_hour": 11, "birth_minute": 10,
        "use_true_solar_time": True, "birth_longitude": 100.0,
        "boundary_tags": ["真太阳时跨午巳"],
    },
    {
        "birth_date": "2001-11-09", "birth_hour": 23, "birth_minute": 10,
        "use_true_solar_time": True, "birth_longitude": 105.0,
        "boundary_tags": ["真太阳时跨子亥", "子时边界"],
    },
)


def _strength_bucket(value: str) -> str:
    if value in {"身强", "从旺"}:
        return "身强"
    if value in {"身弱", "从弱"}:
        return "身弱"
    return "中和"


def _pillar_key(chart: dict) -> str:
    return "|".join(chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour"))


def _fingerprint_key(chart: dict) -> str:
    fingerprint = build_chart_fingerprint(chart)
    personalized = {
        key: fingerprint.get(key)
        for key in (
            "day_master", "strength", "top_elements", "top_ten_gods",
            "wealth_star_count", "officer_star_count", "output_star_count",
            "resource_star_count", "peer_star_count", "day_branch",
            "career_pattern_tags", "wealth_pattern_tags", "love_pattern_tags",
        )
    }
    payload = json.dumps(personalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _make_profile(seed: dict[str, Any], case_id: str, gender: str) -> dict[str, Any]:
    return {
        "name": case_id,
        "gender": gender,
        "birth_date": seed["birth_date"],
        "birth_hour": seed["birth_hour"],
        "birth_minute": seed.get("birth_minute", 0),
        "calendar_type": "solar",
        "use_true_solar_time": bool(seed.get("use_true_solar_time", False)),
        **(
            {"birth_longitude": float(seed["birth_longitude"])}
            if seed.get("use_true_solar_time")
            else {}
        ),
    }


def _case_from_seed(seed: dict[str, Any], index: int) -> dict[str, Any]:
    case_id = f"样例-{index:03d}"
    profile = _make_profile(seed, case_id, "男" if index % 2 else "女")
    chart = build_bazi_chart(profile)
    if chart.get("error"):
        raise RuntimeError(f"{case_id} 排盘失败：{chart['error']}")
    strength = str(chart["day_master_strength"]["strength"])
    return {
        "case_id": case_id,
        "synthetic": True,
        "boundary_tags": list(seed.get("boundary_tags", [])),
        "profile": profile,
        "expected": {
            "pillars": _pillar_key(chart),
            "day_master": chart["day_master"],
            "day_master_element": STEM_ELEMENTS[chart["day_master"]],
            "hour_branch": chart["pillars"]["hour"]["zhi"],
            "strength": strength,
            "strength_bucket": _strength_bucket(strength),
            "fingerprint": _fingerprint_key(chart),
        },
    }


def _fill_requirements(boundary_cases: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    stem_counts = Counter(case["expected"]["day_master"] for case in boundary_cases)
    branch_counts = Counter(case["expected"]["hour_branch"] for case in boundary_cases)
    strength_counts = Counter(case["expected"]["strength_bucket"] for case in boundary_cases)

    stems = [stem for stem in STEMS for _ in range(4 - stem_counts[stem])]
    branches = [branch for branch in BRANCHES for _ in range(max(0, 3 - branch_counts[branch]))]
    branches.extend(("子", "丑", "寅", "卯")[: 32 - len(branches)])

    target_strengths = {"身强": 13, "身弱": 13, "中和": 14}
    strengths: list[str] = []
    for bucket in ("中和", "身弱", "身强"):
        strengths.extend([bucket] * (target_strengths[bucket] - strength_counts[bucket]))

    # 固定步长打散，不依赖随机数；避免相邻样例集中在同一类强弱或时辰。
    branches = branches[::5] + branches[1::5] + branches[2::5] + branches[3::5] + branches[4::5]
    strengths = strengths[::3] + strengths[1::3] + strengths[2::3]
    if not (len(stems) == len(branches) == len(strengths) == 32):
        raise RuntimeError("40 命例补全约束数量异常。")
    return list(zip(stems, branches, strengths))


def _find_seed(
    target_stem: str,
    target_branch: str,
    target_strength: str,
    slot: int,
    used_pillars: set[str],
    used_fingerprints: set[str],
) -> dict[str, Any]:
    start = date(1984, 1, 1)
    days = (date(2023, 12, 31) - start).days + 1
    offset = (slot * 397) % days
    for step in range(days):
        candidate_date = start + timedelta(days=(offset + step) % days)
        seed = {
            "birth_date": candidate_date.isoformat(),
            "birth_hour": BRANCH_HOURS[target_branch],
            "birth_minute": 0,
        }
        chart = build_bazi_chart(_make_profile(seed, "候选", "男"))
        if chart.get("error") or chart.get("day_master") != target_stem:
            continue
        if chart["pillars"]["hour"]["zhi"] != target_branch:
            continue
        if _strength_bucket(str(chart["day_master_strength"]["strength"])) != target_strength:
            continue
        pillar_key = _pillar_key(chart)
        fingerprint_key = _fingerprint_key(chart)
        if pillar_key in used_pillars or fingerprint_key in used_fingerprints:
            continue
        return seed
    raise RuntimeError(f"无法找到满足 {target_stem}/{target_branch}/{target_strength} 的虚构样例。")


def build_case_matrix() -> list[dict[str, Any]]:
    """确定性搜索 40 个样例；结果应与冻结 JSON 完全一致。"""
    cases = [_case_from_seed(seed, index) for index, seed in enumerate(BOUNDARY_SEEDS, start=1)]
    used_pillars = {case["expected"]["pillars"] for case in cases}
    used_fingerprints = {case["expected"]["fingerprint"] for case in cases}
    for slot, (stem, branch, strength) in enumerate(_fill_requirements(cases), start=1):
        seed = _find_seed(stem, branch, strength, slot, used_pillars, used_fingerprints)
        case = _case_from_seed(seed, len(cases) + 1)
        cases.append(case)
        used_pillars.add(case["expected"]["pillars"])
        used_fingerprints.add(case["expected"]["fingerprint"])
    return cases


def load_frozen_matrix(path: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_case_matrix(cases: list[dict[str, Any]], *, recalculate: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    actual_cases: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        if recalculate:
            rebuilt = _case_from_seed(
                {**case["profile"], "boundary_tags": case.get("boundary_tags", [])}, index
            )
            if rebuilt != case:
                errors.append(f"{case.get('case_id', index)} 与当前算法重算结果不一致")
        actual_cases.append(case)

    stems = Counter(case["expected"]["day_master"] for case in actual_cases)
    branches = Counter(case["expected"]["hour_branch"] for case in actual_cases)
    genders = Counter(case["profile"]["gender"] for case in actual_cases)
    strengths = Counter(case["expected"]["strength_bucket"] for case in actual_cases)
    themes = Counter(case["expected"]["day_master_element"] for case in actual_cases)
    pillars = {case["expected"]["pillars"] for case in actual_cases}
    fingerprints = {case["expected"]["fingerprint"] for case in actual_cases}

    if len(actual_cases) != 40:
        errors.append("样例数量不是 40")
    if stems != Counter({stem: 4 for stem in STEMS}):
        errors.append(f"十日主覆盖不均：{dict(stems)}")
    if set(branches) != set(BRANCHES) or min(branches.values(), default=0) < 3:
        errors.append(f"十二时辰覆盖不足：{dict(branches)}")
    if genders != Counter({"男": 20, "女": 20}):
        errors.append(f"性别覆盖不均：{dict(genders)}")
    if any(strengths[bucket] < 10 for bucket in ("身强", "身弱", "中和")):
        errors.append(f"强弱覆盖不足：{dict(strengths)}")
    if any(themes[element] < 6 for element in "木火土金水"):
        errors.append(f"五行主题覆盖不足：{dict(themes)}")
    if len(pillars) != len(actual_cases):
        errors.append("四柱发生重复")
    if len(fingerprints) != len(actual_cases):
        errors.append("核心指纹发生重复")

    return {
        "case_count": len(actual_cases),
        "unique_pillars": len(pillars),
        "unique_fingerprints": len(fingerprints),
        "boundary_case_count": sum(bool(case.get("boundary_tags")) for case in actual_cases),
        "day_masters": dict(stems),
        "hour_branches": dict(branches),
        "genders": dict(genders),
        "strength_buckets": dict(strengths),
        "element_themes": dict(themes),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cases = build_case_matrix()
    if args.check:
        frozen = load_frozen_matrix(args.output)
        if frozen != cases:
            raise SystemExit("冻结矩阵与确定性重建结果不一致。")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = validate_case_matrix(cases)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
