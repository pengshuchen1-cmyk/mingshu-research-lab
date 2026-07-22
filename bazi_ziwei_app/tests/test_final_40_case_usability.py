"""40 组虚构命例完整链路的可用性闸门。"""

from __future__ import annotations

import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "final_40_bazi_cases.json"


def test_single_case_bundle_covers_every_delivery_surface_and_is_json_safe():
    from core.diversity_audit import build_case_bundle
    from scripts.build_final_40_case_matrix import load_frozen_matrix

    case = load_frozen_matrix(FIXTURE)[0]
    bundle = build_case_bundle(case, target_year=2026)

    assert bundle["case_id"] == "样例-001"
    assert len(bundle["chart"]["pillars"]) == 4
    assert len(bundle["public_view"]["five_dimensions"]) == 5
    assert len(bundle["monthly"]) == 12
    assert len(bundle["monthly_events"]) == 12
    assert all(month["top_events"] for month in bundle["monthly_events"])
    assert all(bundle["texts"][key].strip() for key in bundle["texts"])
    assert json.loads(json.dumps(bundle["delivery_snapshot"], ensure_ascii=False)) == bundle["delivery_snapshot"]


def test_full_matrix_usability_audit_has_no_crashes_and_is_deterministic():
    from core.diversity_audit import audit_case_usability
    from scripts.build_final_40_case_matrix import load_frozen_matrix

    cases = load_frozen_matrix(FIXTURE)
    result = audit_case_usability(cases, target_year=2026, verify_determinism=True)

    assert result["case_count"] == 40
    assert result["passed_count"] == 40
    assert result["failed_count"] == 0
    assert result["deterministic_count"] == 40
    assert result["json_safe_count"] == 40
    assert result["core_p95_seconds"] <= 0.5
    assert result["full_p95_seconds"] <= 5.0
    assert all(not case["errors"] for case in result["cases"])


def test_full_chain_timing_excludes_the_second_determinism_run(monkeypatch):
    import core.diversity_audit as audit

    snapshot = {"stable": True}
    fake_bundle = {
        "core_seconds": 0.001,
        "chart": {"pillars": {key: {"pillar": key} for key in ("year", "month", "day", "hour")}},
        "public_view": {"five_dimensions": [{}, {}, {}, {}, {}]},
        "career": {"ok": True},
        "wealth": {"ok": True},
        "relationship": {"ok": True},
        "yearly": {"ok": True},
        "monthly": [{} for _ in range(12)],
        "monthly_events": [{"top_events": [{"event_type": "x"}]} for _ in range(12)],
        "texts": {key: "有内容" for key in audit.SECTION_KEYS},
        "delivery_snapshot": snapshot,
    }

    def delayed_bundle(*_args, **_kwargs):
        time.sleep(0.06)
        return fake_bundle

    monkeypatch.setattr(audit, "build_case_bundle", delayed_bundle)
    result = audit.audit_case_usability([{"case_id": "样例-001"}], verify_determinism=True)

    assert result["cases"][0]["full_seconds"] < 0.09
    assert result["deterministic_count"] == 1
