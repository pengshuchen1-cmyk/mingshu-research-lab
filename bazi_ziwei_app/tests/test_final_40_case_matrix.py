"""The former synthetic 40-case gate was explicitly replaced by five user cases."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_authoritative_acceptance_set_is_the_five_user_cases():
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json").read_text(encoding="utf-8")
    )["cases"]

    assert [case["id"] for case in cases] == ["U01", "U02", "U03", "U04", "U05"]
    assert all(case["expected_pillars"] for case in cases)


def test_five_case_acceptance_artifact_exists():
    target = ROOT / "acceptance_samples" / "user_five_bazi_acceptance.md"

    assert target.exists()
    assert target.read_text(encoding="utf-8").count("## U0") == 5
