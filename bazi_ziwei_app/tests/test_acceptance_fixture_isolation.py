from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIRS = ("core", "services", "ui", "utils")
FORBIDDEN_CASE_MARKERS = (
    "1986-08",
    "1977-",
    "1974-",
    "1994-09-23",
    "1996-09-04",
    "1999-08-11",
    "user_five_bazi_cases.json",
    "lunar_1999_bazi_case.json",
)


def test_production_code_does_not_read_or_embed_acceptance_cases():
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for directory in PRODUCTION_DIRS
        for path in (ROOT / directory).rglob("*.py")
    )

    for marker in FORBIDDEN_CASE_MARKERS:
        assert marker not in production
