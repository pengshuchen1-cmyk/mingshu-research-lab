"""第三轮问真可观察结果对照与算法修改闸门验收测试。"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "acceptance_samples" / "wenzhen_observable_benchmark.md"
REFERENCE_CASES_PATH = ROOT / "tests" / "fixtures" / "bazi_reference_cases.json"

REQUIRED_SNAPSHOT_FIELDS = {
    "input",
    "pillars",
    "ten_god_counts",
    "hidden_stems",
    "five_elements",
    "day_master_strength",
    "relationship_signature",
}
ALLOWED_CLASSIFICATIONS = {
    "输入设置不同",
    "流派口径不同",
    "当前算法疑似错误",
    "无法核验",
}
REQUIRED_EXTERNAL_SETTINGS = {
    "app_version",
    "calendar_type",
    "use_solar_time",
    "timezone",
    "birth_place",
    "day_boundary_rule",
}
REQUIRED_EXTERNAL_OUTPUT = {
    "pillars",
    "ten_god_counts",
    "hidden_stems",
    "five_elements",
    "day_master_strength",
    "relationship_signature",
}
UNKNOWN_TEXT = {"", "unknown", "pending", "unverified", "null", "未提供", "待确认"}
PILLAR_KEYS = {"year", "month", "day", "hour"}
HEAVENLY_STEMS = "甲乙丙丁戊己庚辛壬癸"
EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
FIVE_ELEMENTS = {"木", "火", "土", "金", "水"}
ALLOWED_TEN_GODS = {"比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"}
ALLOWED_STRENGTHS = {"偏强", "身强", "从强", "从旺", "中和", "偏弱", "身弱", "从弱"}
ALLOWED_RELATIONSHIP_ROLES = {"喜用", "忌神", "中性"}
ALLOWED_SPOUSE_STAR_BASES = {"财星", "官杀", "配偶星口径未设定"}
ALLOWED_PEACH_POSITIONS = {"year", "month", "day", "hour"}
ALLOWED_ALGORITHM_TEST_NODES = {
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_solar_time_correction_beijing",
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_solar_time_correction_xinjiang",
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_solar_time_correction_tokyo",
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_detect_special_pattern_cong_wang",
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_detect_special_pattern_cong_ruo",
    "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_detect_special_pattern_none",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_each_case_generates_pillars",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_each_case_day_master",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_strength_engine_returns_fields",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_ten_gods_returns_counts",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_lichun_year_change",
    "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::test_zi_hour_correct_stem",
    "tests/test_jieqi_boundary_month_pillar.py::TestJieqiBoundaryMonthPillar::test_lichun_boundary_year_change",
    "tests/test_jieqi_boundary_month_pillar.py::TestJieqiBoundaryMonthPillar::test_verified_cases_match",
    "tests/test_lunar_leap_month.py::TestLunarLeapMonth::test_lunar_to_solar_conversion",
    "tests/test_lunar_leap_month.py::TestLunarLeapMonth::test_build_bazi_chart_converts_lunar_profile_before_pillars",
    "tests/test_true_solar_time_integration.py::TestTrueSolarTimeIntegration::test_default_standard_time",
    "tests/test_true_solar_time_integration.py::TestTrueSolarTimeIntegration::test_longitude_valid_standard_time_10_cases_unchanged",
    "tests/test_relationship_source_variation.py::test_ten_different_pillar_samples_expose_checkable_relationship_signatures",
    "tests/test_relationship_source_variation.py::test_signature_uses_gender_conditioned_spouse_star_and_proper_indirect_distribution",
    "tests/test_relationship_source_variation.py::test_signature_records_spouse_palace_clash_combination_peach_and_preferences",
}


def _load_benchmark() -> dict:
    text = BENCHMARK_PATH.read_text(encoding="utf-8")
    match = re.search(r"```json benchmark-data\n(.*?)\n```", text, re.DOTALL)
    assert match, "benchmark Markdown must contain a machine-readable benchmark-data JSON block"
    return json.loads(match.group(1))


def _has_meaningful_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in UNKNOWN_TEXT
    if isinstance(value, dict):
        return bool(value) and all(_has_meaningful_value(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return bool(value) and all(_has_meaningful_value(item) for item in value)
    return True


def _has_traceable_evidence(reference) -> bool:
    if not isinstance(reference, dict):
        return False
    if reference.get("kind") not in {"user_screenshot", "public_observation"}:
        return False
    location = reference.get("location")
    digest = reference.get("sha256")
    if not _has_meaningful_value(location) or not re.fullmatch(r"[0-9a-f]{64}", str(digest or "")):
        return False
    evidence_path = Path(location)
    if not evidence_path.is_absolute():
        evidence_path = ROOT / evidence_path
    if not evidence_path.is_file():
        return False
    return hashlib.sha256(evidence_path.read_bytes()).hexdigest() == digest


def _has_reproducible_settings(settings) -> bool:
    if not isinstance(settings, dict) or not REQUIRED_EXTERNAL_SETTINGS <= settings.keys():
        return False
    if settings["calendar_type"] not in {"solar", "lunar"}:
        return False
    if not isinstance(settings["use_solar_time"], bool):
        return False
    return all(
        _has_meaningful_value(settings[key])
        for key in REQUIRED_EXTERNAL_SETTINGS - {"use_solar_time"}
    )


def _is_nonnegative_finite_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _is_nonnegative_integer(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _has_valid_pillars(pillars) -> bool:
    if not isinstance(pillars, dict) or set(pillars) != PILLAR_KEYS:
        return False
    for pillar in pillars.values():
        if not isinstance(pillar, str) or len(pillar) != 2:
            return False
        stem, branch = pillar
        if stem not in HEAVENLY_STEMS or branch not in EARTHLY_BRANCHES:
            return False
        if (HEAVENLY_STEMS.index(stem) - EARTHLY_BRANCHES.index(branch)) % 2:
            return False
    return True


def _has_valid_ten_god_counts(counts) -> bool:
    return (
        isinstance(counts, dict)
        and bool(counts)
        and set(counts) <= ALLOWED_TEN_GODS
        and all(_is_nonnegative_integer(value) for value in counts.values())
        and any(value > 0 for value in counts.values())
    )


def _has_valid_hidden_stems(hidden_stems, pillars) -> bool:
    if not isinstance(hidden_stems, dict) or set(hidden_stems) != PILLAR_KEYS:
        return False
    if not isinstance(pillars, dict) or set(pillars) != PILLAR_KEYS:
        return False

    from core.bazi_constants import BRANCH_HIDDEN_STEMS

    for position in PILLAR_KEYS:
        stems = hidden_stems[position]
        pillar = pillars[position]
        if not isinstance(pillar, str) or len(pillar) != 2:
            return False
        branch_stems = set(BRANCH_HIDDEN_STEMS.get(pillar[1], []))
        if (
            not isinstance(stems, list)
            or not stems
            or len(stems) != len(set(stems))
            or not all(
                isinstance(stem, str) and stem in branch_stems
                for stem in stems
            )
        ):
            return False
    return True


def _has_valid_five_elements(five_elements) -> bool:
    return (
        isinstance(five_elements, dict)
        and set(five_elements) == FIVE_ELEMENTS
        and all(_is_nonnegative_finite_number(value) for value in five_elements.values())
        and any(value > 0 for value in five_elements.values())
    )


def _has_valid_relationship_signature(signature) -> bool:
    required = {
        "spouse_palace",
        "spouse_relations",
        "spouse_star",
        "ten_god_support",
        "peach_blossom",
        "strength_preference",
    }
    if not isinstance(signature, dict) or set(signature) != required:
        return False

    palace = signature["spouse_palace"]
    if not isinstance(palace, dict) or set(palace) != {"branch", "element", "role"}:
        return False
    branch = palace.get("branch")
    if not isinstance(branch, str) or branch not in EARTHLY_BRANCHES:
        return False
    if palace.get("element") not in FIVE_ELEMENTS:
        return False
    if palace.get("role") not in ALLOWED_RELATIONSHIP_ROLES:
        return False

    relations = signature["spouse_relations"]
    if not isinstance(relations, dict) or set(relations) != {"clashes", "combinations"}:
        return False
    for entries in relations.values():
        if not isinstance(entries, list) or not all(
            isinstance(entry, str) and _has_meaningful_value(entry) for entry in entries
        ):
            return False

    spouse_star = signature["spouse_star"]
    if (
        not isinstance(spouse_star, dict)
        or set(spouse_star) != {"basis", "total", "proper", "indirect"}
        or spouse_star.get("basis") not in ALLOWED_SPOUSE_STAR_BASES
    ):
        return False
    if not all(
        _is_nonnegative_integer(spouse_star.get(key))
        for key in ("total", "proper", "indirect")
    ):
        return False
    if spouse_star["total"] != spouse_star["proper"] + spouse_star["indirect"]:
        return False

    support = signature["ten_god_support"]
    if not isinstance(support, dict) or set(support) != {"output", "peer", "resource"}:
        return False
    if not all(_is_nonnegative_integer(value) for value in support.values()):
        return False

    peach = signature["peach_blossom"]
    if (
        not isinstance(peach, dict)
        or set(peach) != {"count", "positions"}
        or not _is_nonnegative_integer(peach.get("count"))
    ):
        return False
    if not isinstance(peach.get("positions"), list) or not all(
        position in ALLOWED_PEACH_POSITIONS for position in peach["positions"]
    ):
        return False
    if len(peach["positions"]) != len(set(peach["positions"])) or peach["count"] != len(
        peach["positions"]
    ):
        return False

    preference = signature["strength_preference"]
    return (
        isinstance(preference, dict)
        and set(preference) == {"strength"}
        and preference.get("strength") in ALLOWED_STRENGTHS
    )


def _has_actual_external_output(output) -> bool:
    return (
        isinstance(output, dict)
        and set(output) == REQUIRED_EXTERNAL_OUTPUT
        and _has_valid_pillars(output["pillars"])
        and _has_valid_ten_god_counts(output["ten_god_counts"])
        and _has_valid_hidden_stems(output["hidden_stems"], output["pillars"])
        and _has_valid_five_elements(output["five_elements"])
        and isinstance(output["day_master_strength"], str)
        and output["day_master_strength"] in ALLOWED_STRENGTHS
        and _has_valid_relationship_signature(output["relationship_signature"])
    )


def _resolve_reference_path(location) -> Path | None:
    if not _has_meaningful_value(location):
        return None
    path = Path(location)
    return path if path.is_absolute() else ROOT / path


def _is_allowed_algorithm_test_node(node_id) -> bool:
    if not isinstance(node_id, str) or node_id not in ALLOWED_ALGORITHM_TEST_NODES:
        return False
    parts = node_id.split("::")
    if len(parts) not in {2, 3} or not parts[-1].startswith("test_"):
        return False
    test_path_text = parts[0]
    if not re.fullmatch(r"tests/[A-Za-z0-9_./-]+\.py", test_path_text):
        return False
    test_path = ROOT / test_path_text
    if not test_path.is_file():
        return False
    tree = ast.parse(test_path.read_text(encoding="utf-8"))
    if len(parts) == 2:
        return any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[1]
            for node in tree.body
        )
    test_class = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == parts[1]),
        None,
    )
    return test_class is not None and any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[2]
        for node in test_class.body
    )


def _reject_nonstandard_json_constant(value: str):
    raise ValueError(f"non-standard JSON constant: {value}")


def _has_concrete_json_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return _has_meaningful_value(value)
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(value)
    if isinstance(value, list):
        return bool(value) and all(_has_concrete_json_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(
            _has_meaningful_value(key) and _has_concrete_json_value(item)
            for key, item in value.items()
        )
    return False


def _has_real_red_test_evidence(reference, case_id: str, external_evidence_reference: dict) -> bool:
    if not isinstance(reference, dict) or set(reference) != {"location", "sha256"}:
        return False
    if not isinstance(external_evidence_reference, dict):
        return False
    package_path = _resolve_reference_path(reference.get("location"))
    evidence_path = _resolve_reference_path(external_evidence_reference.get("location"))
    if package_path is None or evidence_path is None or package_path.resolve() == evidence_path.resolve():
        return False
    package_digest = reference.get("sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(package_digest or "")):
        return False
    if not package_path.is_file() or hashlib.sha256(package_path.read_bytes()).hexdigest() != package_digest:
        return False
    try:
        payload = json.loads(
            package_path.read_text(encoding="utf-8"),
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return False
    required = {
        "schema_version",
        "case_id",
        "external_evidence_sha256",
        "algorithm_test_node_id",
        "exit_code",
        "red_command",
        "failure_output",
        "expected",
        "actual",
        "captured_at",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        return False
    if payload["schema_version"] != "1.0" or payload["case_id"] != case_id:
        return False
    external_digest = payload["external_evidence_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", str(external_digest or "")):
        return False
    if external_digest != external_evidence_reference.get("sha256"):
        return False
    node_id = payload["algorithm_test_node_id"]
    if not _is_allowed_algorithm_test_node(node_id):
        return False
    exit_code = payload["exit_code"]
    if not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code == 0:
        return False
    command = payload["red_command"]
    failure_output = payload["failure_output"]
    if not all(_has_meaningful_value(value) for value in (command, failure_output)):
        return False
    if command != f".venv/bin/python -m pytest {node_id} -q":
        return False
    if not re.search(rf"(?m)^FAILED\s+{re.escape(node_id)}(?:\s|$)", failure_output):
        return False
    if not _has_concrete_json_value(payload["expected"]) or not _has_concrete_json_value(payload["actual"]):
        return False
    if payload["expected"] == payload["actual"]:
        return False
    captured_at = payload["captured_at"]
    if not isinstance(captured_at, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        captured_at,
    ):
        return False
    try:
        timestamp = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return timestamp.tzinfo is not None


def _gate_expected(comparison: dict, case_id: str | None = None) -> bool:
    observation = comparison.get("external_observation", {})
    return (
        _has_meaningful_value(case_id)
        and observation.get("status") == "observed"
        and observation.get("verification") == "verified"
        and _has_traceable_evidence(observation.get("evidence_reference"))
        and _has_reproducible_settings(observation.get("settings"))
        and _has_actual_external_output(observation.get("external_output"))
        and comparison.get("difference_classification") == "当前算法疑似错误"
        and _has_real_red_test_evidence(
            comparison.get("red_evidence_package"),
            case_id,
            observation.get("evidence_reference"),
        )
    )


def _normalized_engine_profile(reference: dict) -> dict:
    profile = reference["profile"]
    return {
        "name": profile["name"],
        "gender": "男" if profile["gender"].startswith("男") else "女",
        "birth_date": profile["birth_date"],
        "birth_hour": profile["birth_hour"],
        "birth_minute": profile.get("birth_minute") or 0,
        "birth_place": "" if profile.get("birth_place") == "未提供" else profile.get("birth_place", ""),
        "use_solar_time": False,
    }


def _synthetic_unverified_comparison(tmp_path: Path) -> dict:
    evidence_path = tmp_path / "wenzhen-observation.png"
    evidence_path.write_bytes(b"synthetic gate-contract evidence")
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    node_id = (
        "tests/test_round_three_algorithm_benchmarks.py::"
        "test_gate_requires_complete_reproducible_external_observation"
    )
    return {
        "external_observation": {
            "provider": "问真",
            "status": "observed",
            "verification": "verified",
            "evidence_reference": {
                "kind": "user_screenshot",
                "location": str(evidence_path),
                "sha256": digest,
            },
            "settings": {
                "app_version": "9.9.9-test",
                "calendar_type": "solar",
                "use_solar_time": False,
                "timezone": "Asia/Shanghai",
                "birth_place": "上海市",
                "day_boundary_rule": "00:00换日",
            },
            "external_output": {
                "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
                "ten_god_counts": {"比肩": 1},
                "hidden_stems": {"year": ["癸"], "month": ["己", "癸", "辛"], "day": ["甲", "丙", "戊"], "hour": ["乙"]},
                "five_elements": {"木": 1.0, "火": 1.0, "土": 1.0, "金": 1.0, "水": 1.0},
                "day_master_strength": "身强",
                "relationship_signature": {
                    "spouse_palace": {"branch": "寅", "element": "木", "role": "喜用"},
                    "spouse_relations": {"clashes": [], "combinations": []},
                    "spouse_star": {"basis": "财星", "total": 1, "proper": 1, "indirect": 0},
                    "ten_god_support": {"output": 1, "peer": 1, "resource": 1},
                    "peach_blossom": {"count": 0, "positions": []},
                    "strength_preference": {"strength": "身强"},
                },
            },
        },
        "difference_classification": "当前算法疑似错误",
        "red_evidence_package": None,
        "failing_test": {
            "node_id": node_id,
            "red_command": f".venv/bin/python -m pytest {node_id} -q",
            "failure_output": f"FAILED {node_id} - AssertionError: observable difference",
        },
        "algorithm_change_allowed": False,
    }


def _forged_red_package_reference(
    tmp_path: Path,
    flaw: str,
    *,
    case_id: str,
    external_evidence_reference: dict,
) -> dict:
    algorithm_node = (
        "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::"
        "test_detect_special_pattern_cong_ruo"
    )
    payload = {
        "schema_version": "1.0",
        "case_id": case_id,
        "external_evidence_sha256": external_evidence_reference["sha256"],
        "algorithm_test_node_id": algorithm_node,
        "exit_code": 1,
        "red_command": f".venv/bin/python -m pytest {algorithm_node} -q",
        "failure_output": f"FAILED {algorithm_node} - expected 壬子, actual 癸丑",
        "expected": {"day": "壬子"},
        "actual": {"day": "癸丑"},
        "captured_at": "2026-07-15T12:00:00+08:00",
    }
    if flaw == "case_id_mismatch":
        payload["case_id"] = "different_case"
    elif flaw == "external_hash_mismatch":
        payload["external_evidence_sha256"] = "0" * 64
    elif flaw == "forbidden_gate_node":
        payload["algorithm_test_node_id"] = (
            "tests/test_round_three_algorithm_benchmarks.py::"
            "test_gate_never_opens_for_a_synthetic_observation"
        )
    elif flaw == "fake_algorithm_node":
        payload["algorithm_test_node_id"] = (
            "tests/test_algorithm_boundaries.py::AlgorithmBoundaryTests::test_not_real"
        )
    elif flaw == "unrelated_algorithm_file_node":
        unrelated_node = (
            "tests/test_bazi_algorithm_accuracy.py::TestBaziAlgorithmAccuracy::"
            "test_fixture_exists"
        )
        payload["algorithm_test_node_id"] = unrelated_node
        payload["red_command"] = f".venv/bin/python -m pytest {unrelated_node} -q"
        payload["failure_output"] = f"FAILED {unrelated_node} - fixture missing"
    elif flaw == "exit_zero":
        payload["exit_code"] = 0
    elif flaw == "red_command_empty":
        payload["red_command"] = ""
    elif flaw == "red_command_mismatch":
        payload["red_command"] = ".venv/bin/python -m pytest tests/test_core_behaviors.py -q"
    elif flaw == "red_command_shell_chain":
        payload["red_command"] += "; echo forged"
    elif flaw == "failure_output_negated":
        payload["failure_output"] = f"NOT FAILED {algorithm_node} - synthetic text only"
    elif flaw == "expected_none":
        payload["expected"] = None
    elif flaw == "actual_none":
        payload["actual"] = None
    elif flaw == "expected_equals_actual":
        payload["actual"] = copy.deepcopy(payload["expected"])
    elif flaw == "expected_nan":
        payload["expected"] = math.nan
    elif flaw == "expected_nested_none":
        payload["expected"] = {"day": None}
    elif flaw == "captured_at_invalid":
        payload["captured_at"] = "yesterday"
    elif flaw == "package_extra_none":
        payload["unbound_extra"] = None

    package_path = tmp_path / f"red-package-{flaw}.json"
    package_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
    reference = {
        "location": str(package_path),
        "sha256": "f" * 64 if flaw == "package_hash_mismatch" else digest,
    }
    if flaw == "not_independent":
        reference["location"] = external_evidence_reference["location"]
        reference["sha256"] = external_evidence_reference["sha256"]
    return reference


def _call_red_package_validator(reference: dict, case_id: str, evidence_reference: dict) -> bool:
    return _has_real_red_test_evidence(reference, case_id, evidence_reference)


def test_benchmark_file_exists_and_declares_non_imitation_boundary():
    assert BENCHMARK_PATH.is_file()
    text = BENCHMARK_PATH.read_text(encoding="utf-8")
    assert "不声称复制问真专有算法" in text
    assert "不得把不同流派口径直接当成程序错误" in text
    assert "当前闸门关闭；未来只有真实独立证据包才能打开" in text


def test_benchmark_contains_six_traceable_internal_snapshots():
    benchmark = _load_benchmark()
    snapshots = benchmark["cases"]
    assert len(snapshots) == 6
    assert set(benchmark["field_sources"]) == REQUIRED_SNAPSHOT_FIELDS

    reference_data = json.loads(REFERENCE_CASES_PATH.read_text(encoding="utf-8"))
    references = {case["case_id"]: case for case in reference_data["cases"]}

    from core.bazi_constants import BRANCH_HIDDEN_STEMS
    from core.bazi_engine import build_bazi_chart
    from core.life_overview_engine import analyze_life_overview

    for item in snapshots:
        assert item["source_case_id"] in references
        reference = references[item["source_case_id"]]
        snapshot = item["internal_snapshot"]
        assert REQUIRED_SNAPSHOT_FIELDS <= snapshot.keys()
        assert snapshot["input"]["source_profile"] == reference["profile"]
        assert snapshot["input"]["engine_profile"] == _normalized_engine_profile(reference)

        chart = build_bazi_chart(snapshot["input"]["engine_profile"])
        life_overview = analyze_life_overview(chart)
        engine_pillars = {
            key: chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
        }
        reference_chart = reference["standard_time_chart"]

        assert snapshot["pillars"] == reference_chart["pillars"] == engine_pillars
        assert snapshot["ten_god_counts"] == reference_chart["ten_god_counts"]
        assert snapshot["ten_god_counts"] == chart["ten_god_counts"]

        engine_hidden_stems = {
            key: [entry["gan"] for entry in chart["hidden_stems"][key]]
            for key in ("year", "month", "day", "hour")
        }
        mapping_hidden_stems = {
            key: BRANCH_HIDDEN_STEMS[chart["pillars"][key]["zhi"]]
            for key in ("year", "month", "day", "hour")
        }
        assert snapshot["hidden_stems"] == engine_hidden_stems == mapping_hidden_stems

        assert snapshot["five_elements"] == reference_chart["five_elements"]
        assert snapshot["five_elements"] == chart["five_elements"]
        assert snapshot["day_master_strength"] == reference_chart["day_master_strength"]
        assert snapshot["day_master_strength"] == chart["day_master_strength"]["strength"]
        assert snapshot["relationship_signature"] == life_overview["romance_overview"][
            "relationship_signature"
        ]


def test_every_external_result_is_explicitly_pending_and_unverified():
    for item in _load_benchmark()["cases"]:
        observation = item["comparison"]["external_observation"]
        assert observation["provider"] == "问真"
        assert observation["status"] == "pending"
        assert observation["verification"] == "unverified"
        assert observation["version"] == "unknown"
        assert observation["evidence_reference"] is None
        assert all(value == "unknown" for value in observation["settings"].values())
        assert set(observation["settings"]) == REQUIRED_EXTERNAL_SETTINGS
        assert set(observation["external_output"]) == REQUIRED_EXTERNAL_OUTPUT
        assert all(value is None for value in observation["external_output"].values())


def test_each_difference_uses_an_allowed_classification():
    for item in _load_benchmark()["cases"]:
        comparison = item["comparison"]
        assert comparison["difference_classification"] in ALLOWED_CLASSIFICATIONS
        assert comparison["comparison_order"] == ["四柱", "十神", "强弱", "关系解释"]


def test_algorithm_change_gate_is_derived_and_pending_never_allows_change():
    benchmark = _load_benchmark()
    assert benchmark["algorithm_change_gate"]["required_conditions"] == [
        "status_observed",
        "verification_verified",
        "traceable_evidence_reference",
        "complete_reproducible_settings",
        "nonempty_external_output",
        "difference_classified_as_current_algorithm_suspected_error",
        "independent_hashed_red_evidence_package",
    ]

    for item in benchmark["cases"]:
        comparison = item["comparison"]
        assert comparison["red_evidence_package"] is None
        assert "failing_test" not in comparison
        assert comparison["algorithm_change_allowed"] is _gate_expected(
            comparison, item["source_case_id"]
        )
        assert comparison["algorithm_change_allowed"] is False


def test_gate_truth_table_allows_only_fully_evidenced_suspected_error():
    truth_table = _load_benchmark()["algorithm_change_gate"]["truth_table"]
    assert len(truth_table) >= 8
    for row in truth_table:
        expected = (
            row["status_observed"]
            and row["verification_verified"]
            and row["traceable_evidence_reference"]
            and row["complete_reproducible_settings"]
            and row["nonempty_external_output"]
            and row["difference_classification"] == "当前算法疑似错误"
            and row["independent_hashed_red_evidence_package"]
        )
        assert row["algorithm_change_allowed"] is expected
    assert sum(row["algorithm_change_allowed"] for row in truth_table) == 0


def test_gate_never_opens_for_a_synthetic_observation(tmp_path):
    comparison = _synthetic_unverified_comparison(tmp_path)
    assert _gate_expected(comparison, "synthetic_case") is False


def test_gate_rejects_inline_red_evidence_even_when_strings_look_complete(tmp_path):
    comparison = _synthetic_unverified_comparison(tmp_path)
    observation = comparison["external_observation"]
    assert _has_real_red_test_evidence(
        comparison["failing_test"],
        "synthetic_case",
        observation["evidence_reference"],
    ) is False


def test_external_output_accepts_complete_schema_with_semantic_empty_lists(tmp_path):
    output = _synthetic_unverified_comparison(tmp_path)["external_observation"]["external_output"]
    assert output["relationship_signature"]["spouse_relations"]["clashes"] == []
    assert output["relationship_signature"]["peach_blossom"]["positions"] == []
    assert _has_actual_external_output(output) is True


@pytest.mark.parametrize(
    "flaw",
    [
        "package_hash_mismatch",
        "case_id_mismatch",
        "external_hash_mismatch",
        "forbidden_gate_node",
        "fake_algorithm_node",
        "unrelated_algorithm_file_node",
        "exit_zero",
        "red_command_empty",
        "red_command_mismatch",
        "red_command_shell_chain",
        "failure_output_negated",
        "expected_none",
        "actual_none",
        "expected_equals_actual",
        "expected_nan",
        "expected_nested_none",
        "captured_at_invalid",
        "package_extra_none",
        "not_independent",
    ],
)
def test_red_evidence_package_rejects_forged_or_unbound_artifacts(tmp_path, flaw):
    case_id = "bazi_ref_tang_rui_1997_2026"
    evidence_path = tmp_path / "external-observation.png"
    evidence_path.write_bytes(b"unverified external observation fixture")
    evidence_reference = {
        "kind": "user_screenshot",
        "location": str(evidence_path),
        "sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
    }
    package_reference = _forged_red_package_reference(
        tmp_path,
        flaw,
        case_id=case_id,
        external_evidence_reference=evidence_reference,
    )

    assert _call_red_package_validator(package_reference, case_id, evidence_reference) is False


@pytest.mark.parametrize(
    ("case_id", "mutate"),
    [
        pytest.param("pillars_missing_hour", lambda output: output["pillars"].pop("hour"), id="pillars-missing-hour"),
        pytest.param("pillars_nested_none", lambda output: output["pillars"].update(hour=None), id="pillars-nested-none"),
        pytest.param("pillars_illegal_value", lambda output: output["pillars"].update(hour="甲A"), id="pillars-illegal-value"),
        pytest.param("pillars_wrong_type", lambda output: output.update(pillars=["甲子"]), id="pillars-wrong-type"),
        pytest.param("ten_god_unknown_key", lambda output: output["ten_god_counts"].update(未知十神=1), id="ten-god-unknown-key"),
        pytest.param("ten_god_negative", lambda output: output["ten_god_counts"].update(比肩=-1), id="ten-god-negative"),
        pytest.param("ten_god_nan", lambda output: output["ten_god_counts"].update(比肩=math.nan), id="ten-god-nan"),
        pytest.param("ten_god_fractional", lambda output: output["ten_god_counts"].update(比肩=0.5), id="ten-god-fractional"),
        pytest.param("ten_god_all_zero", lambda output: output.update(ten_god_counts={"比肩": 0}), id="ten-god-all-zero"),
        pytest.param("ten_god_wrong_type", lambda output: output.update(ten_god_counts="比肩1"), id="ten-god-wrong-type"),
        pytest.param("hidden_stems_missing_hour", lambda output: output["hidden_stems"].pop("hour"), id="hidden-missing-hour"),
        pytest.param("hidden_stems_nested_none", lambda output: output["hidden_stems"].update(hour=None), id="hidden-nested-none"),
        pytest.param("hidden_stems_illegal_stem", lambda output: output["hidden_stems"].update(hour=["A"]), id="hidden-illegal-stem"),
        pytest.param("hidden_stems_all_empty", lambda output: output.update(hidden_stems={key: [] for key in PILLAR_KEYS}), id="hidden-all-empty"),
        pytest.param("hidden_stems_branch_mismatch", lambda output: output["hidden_stems"].update(year=["甲"]), id="hidden-branch-mismatch"),
        pytest.param("hidden_stems_wrong_type", lambda output: output["hidden_stems"].update(hour="乙"), id="hidden-wrong-type"),
        pytest.param("five_elements_missing_water", lambda output: output["five_elements"].pop("水"), id="five-elements-missing-water"),
        pytest.param("five_elements_negative", lambda output: output["five_elements"].update(水=-0.1), id="five-elements-negative"),
        pytest.param("five_elements_nan", lambda output: output["five_elements"].update(水=math.nan), id="five-elements-nan"),
        pytest.param("five_elements_infinity", lambda output: output["five_elements"].update(水=math.inf), id="five-elements-infinity"),
        pytest.param("five_elements_all_zero", lambda output: output.update(five_elements={element: 0 for element in FIVE_ELEMENTS}), id="five-elements-all-zero"),
        pytest.param("five_elements_wrong_type", lambda output: output["five_elements"].update(水="1.0"), id="five-elements-wrong-type"),
        pytest.param("strength_none", lambda output: output.update(day_master_strength=None), id="strength-none"),
        pytest.param("strength_empty", lambda output: output.update(day_master_strength=""), id="strength-empty"),
        pytest.param("strength_nonstandard", lambda output: output.update(day_master_strength="超级强"), id="strength-nonstandard"),
        pytest.param("relationship_missing_spouse_star", lambda output: output["relationship_signature"].pop("spouse_star", None), id="relationship-missing-spouse-star"),
        pytest.param("external_output_extra_none", lambda output: output.update(unbound_extra=None), id="external-output-extra-none"),
        pytest.param("relationship_extra_none", lambda output: output["relationship_signature"].update(unbound_extra=None), id="relationship-extra-none"),
        pytest.param("relationship_nested_none", lambda output: output["relationship_signature"]["spouse_palace"].update(branch=None), id="relationship-nested-none"),
        pytest.param("relationship_palace_extra_none", lambda output: output["relationship_signature"]["spouse_palace"].update(unbound_extra=None), id="relationship-palace-extra-none"),
        pytest.param("relationship_illegal_role", lambda output: output["relationship_signature"]["spouse_palace"].update(role="绕过值"), id="relationship-illegal-role"),
        pytest.param("relationship_relations_wrong_type", lambda output: output["relationship_signature"].update(spouse_relations=[]), id="relationship-relations-wrong-type"),
        pytest.param("relationship_relation_numeric_leaf", lambda output: output["relationship_signature"]["spouse_relations"].update(clashes=[0]), id="relationship-relation-numeric-leaf"),
        pytest.param("relationship_spouse_basis_numeric", lambda output: output["relationship_signature"]["spouse_star"].update(basis=0), id="relationship-spouse-basis-numeric"),
        pytest.param("relationship_spouse_star_extra_none", lambda output: output["relationship_signature"]["spouse_star"].update(unbound_extra=None), id="relationship-spouse-star-extra-none"),
        pytest.param("relationship_negative_count", lambda output: output["relationship_signature"]["peach_blossom"].update(count=-1), id="relationship-negative-count"),
        pytest.param("relationship_peach_numeric_position", lambda output: output["relationship_signature"]["peach_blossom"].update(positions=[0]), id="relationship-peach-numeric-position"),
        pytest.param("relationship_peach_count_mismatch", lambda output: output["relationship_signature"]["peach_blossom"].update(count=1), id="relationship-peach-count-mismatch"),
        pytest.param("relationship_preference_extra_none", lambda output: output["relationship_signature"]["strength_preference"].update(unbound_extra=None), id="relationship-preference-extra-none"),
    ],
)
def test_external_output_rejects_invalid_nested_values(tmp_path, case_id, mutate):
    output = copy.deepcopy(
        _synthetic_unverified_comparison(tmp_path)["external_observation"]["external_output"]
    )
    mutate(output)
    assert _has_actual_external_output(output) is False, case_id
