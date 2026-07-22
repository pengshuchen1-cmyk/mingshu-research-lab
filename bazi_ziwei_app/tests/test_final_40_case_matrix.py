"""最终收口 40 组虚构命例覆盖矩阵。"""

from __future__ import annotations

from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "final_40_bazi_cases.json"


def test_frozen_matrix_satisfies_all_coverage_gates():
    from scripts.build_final_40_case_matrix import load_frozen_matrix, validate_case_matrix

    cases = load_frozen_matrix(FIXTURE)
    result = validate_case_matrix(cases, recalculate=True)

    assert result["case_count"] == 40
    assert result["errors"] == []
    assert result["unique_pillars"] == 40
    assert result["unique_fingerprints"] == 40
    assert result["boundary_case_count"] >= 8


def test_frozen_matrix_is_balanced_and_contains_no_real_identity_fields():
    from scripts.build_final_40_case_matrix import load_frozen_matrix

    cases = load_frozen_matrix(FIXTURE)
    day_masters = Counter(case["expected"]["day_master"] for case in cases)
    hour_branches = Counter(case["expected"]["hour_branch"] for case in cases)
    genders = Counter(case["profile"]["gender"] for case in cases)
    strengths = Counter(case["expected"]["strength_bucket"] for case in cases)
    themes = Counter(case["expected"]["day_master_element"] for case in cases)

    assert day_masters == {stem: 4 for stem in "甲乙丙丁戊己庚辛壬癸"}
    assert set(hour_branches) == set("子丑寅卯辰巳午未申酉戌亥")
    assert min(hour_branches.values()) >= 3
    assert genders == {"男": 20, "女": 20}
    assert all(strengths[bucket] >= 10 for bucket in ("身强", "身弱", "中和"))
    assert all(themes[element] >= 6 for element in "木火土金水")

    for index, case in enumerate(cases, start=1):
        profile = case["profile"]
        assert case["case_id"] == f"样例-{index:03d}"
        assert profile["name"] == case["case_id"]
        assert not any(key in profile for key in ("phone", "email", "address", "real_name"))


def test_frozen_matrix_rebuild_is_deterministic():
    from scripts.build_final_40_case_matrix import build_case_matrix, load_frozen_matrix

    assert build_case_matrix() == load_frozen_matrix(FIXTURE)
