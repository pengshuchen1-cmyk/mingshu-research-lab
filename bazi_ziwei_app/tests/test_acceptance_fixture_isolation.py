from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TEXT_FILE_ENDINGS = (
    ".py",
    ".json",
    ".md",
    ".txt",
    ".toml",
    ".toml.example",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".jinja",
    ".jinja2",
    ".j2",
    ".tmpl",
    ".template",
    ".csv",
    ".sh",
    ".command",
    ".ini",
    ".cfg",
)
ALLOWED_ACCEPTANCE_ROOTS = (
    ("tests",),
    ("acceptance_samples",),
    ("docs", "superpowers"),
)
ALLOWED_ACCEPTANCE_SCRIPTS = {
    Path("scripts/run_user_five_ai_acceptance.py"),
    Path("scripts/render_lunar_1999_acceptance.py"),
    Path("scripts/render_user_five_bazi_acceptance.py"),
}
IGNORED_TOOLING_DIR_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".superpowers",
    "__pycache__",
    "node_modules",
}
ACCEPTANCE_FIXTURES = (
    ROOT / "tests" / "fixtures" / "user_five_bazi_cases.json",
    ROOT / "tests" / "fixtures" / "lunar_1999_bazi_case.json",
)
LEGACY_CASE_MARKERS = (
    "陈芃澍",
    "周惠敏",
    "任昱洁",
    "chen_pengshu",
    "zhou_huimin",
    "master_case_references.json",
    "master_case_combination_weights.json",
    "activate_master_case",
    "from_master_case",
    "master_case",
)


def _case_markers_from_fixtures() -> tuple[str, ...]:
    cases: list[dict] = []
    for path in ACCEPTANCE_FIXTURES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_cases = payload.get("cases") if isinstance(payload, dict) else None
        if isinstance(raw_cases, list):
            cases.extend(item for item in raw_cases if isinstance(item, dict))
        elif isinstance(payload, dict):
            cases.append(payload)

    markers = {path.name for path in ACCEPTANCE_FIXTURES}
    for case in cases:
        for key in ("id", "case_id", "legacy_id", "name", "asset_path"):
            value = str(case.get(key) or "").strip()
            if value:
                markers.add(value)
        raw_date = str(case.get("date") or "").strip()
        solar_date = str(case.get("expected_solar_date") or "").strip()
        exact_time = str(case.get("time") or "").strip()
        markers.update(value for value in (raw_date, solar_date) if value)
        if exact_time:
            markers.update(
                {
                    f'"time": "{exact_time}"',
                    f'"time":"{exact_time}"',
                }
            )
        for date_value in (raw_date, solar_date):
            if date_value and exact_time:
                markers.update(
                    {
                        f"{date_value} {exact_time}",
                        f"{date_value}T{exact_time}",
                    }
                )
        pillars = case.get("expected_pillars")
        if isinstance(pillars, list) and pillars:
            normalized = [str(value) for value in pillars]
            pillar_markers = {
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(
                    normalized,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                repr(tuple(normalized)),
                " / ".join(normalized),
                "/".join(normalized),
            }
            for position, pillar in zip(
                ("year", "month", "day", "hour"),
                normalized,
            ):
                pillar_markers.update(
                    {
                        f'"{position}": "{pillar}"',
                        f'"{position}":"{pillar}"',
                    }
                )
            markers.update(pillar_markers)
    return tuple(sorted(markers, key=lambda value: (-len(value), value)))


FORBIDDEN_CASE_MARKERS = (
    *_case_markers_from_fixtures(),
    *LEGACY_CASE_MARKERS,
)


def _is_allowed_acceptance_path(relative_path: Path) -> bool:
    if relative_path in ALLOWED_ACCEPTANCE_SCRIPTS:
        return True
    return any(
        relative_path.parts[: len(prefix)] == prefix
        for prefix in ALLOWED_ACCEPTANCE_ROOTS
    )


def _find_forbidden_case_leaks(root: Path) -> list[tuple[Path, str]]:
    leaks: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if any(part in IGNORED_TOOLING_DIR_NAMES for part in relative_path.parts):
            continue
        if _is_allowed_acceptance_path(relative_path):
            continue
        if not path.name.endswith(TEXT_FILE_ENDINGS):
            continue
        text = path.read_text(encoding="utf-8")
        leaks.extend(
            (relative_path, marker)
            for marker in FORBIDDEN_CASE_MARKERS
            if marker in text
        )
    return leaks


def test_production_code_does_not_read_or_embed_acceptance_cases():
    leaks = _find_forbidden_case_leaks(ROOT)

    assert leaks == [], "\n".join(
        f"{marker!r} leaked into production asset {path}"
        for path, marker in leaks
    )


def test_reference_cases_are_test_fixtures_not_runtime_assets():
    assert (ROOT / "tests" / "fixtures" / "bazi_reference_cases.json").is_file()
    assert not (ROOT / "data" / "bazi_reference_cases.json").exists()
    assert not (ROOT / "rules" / "master_case_references.json").exists()
    assert not (ROOT / "rules" / "master_case_combination_weights.json").exists()


def test_scanner_catches_a_forbidden_marker_in_a_new_production_directory(
    tmp_path,
):
    template = tmp_path / "new_feature" / "templates" / "customer_prompt.j2"
    template.parent.mkdir(parents=True)
    template.write_text("runtime case: 1999-08-11", encoding="utf-8")

    assert _find_forbidden_case_leaks(tmp_path) == [
        (Path("new_feature/templates/customer_prompt.j2"), "1999-08-11")
    ]


@pytest.mark.parametrize("raw_lunar_date", ("1986-07-10", "1999-07-01"))
def test_scanner_catches_raw_lunar_date_in_arbitrary_new_production_directory(
    tmp_path,
    raw_lunar_date,
):
    target = tmp_path / "brand_new_runtime" / "prompts" / "answer.md"
    target.parent.mkdir(parents=True)
    target.write_text(f"hidden calibration: {raw_lunar_date}", encoding="utf-8")

    leaks = _find_forbidden_case_leaks(tmp_path)

    assert (Path("brand_new_runtime/prompts/answer.md"), raw_lunar_date) in leaks
