from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


REQUIRED_SECTIONS = {
    "calendar",
    "pillars",
    "dayun",
    "strength",
    "pattern",
    "wealth",
    "relationship",
    "safety",
}


def _write_pack(root: Path, rules: list[dict[str, object]]) -> None:
    payload = {"rules": rules}
    rule_path = root / "foundations.json"
    rule_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(rule_path.read_bytes()).hexdigest()
    manifest = {
        "version": "2.0.0",
        "files": [{"path": "foundations.json", "sha256": digest}],
        "citation_keys": ["bazi-skill:time-boundary"],
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _minimal_rules() -> list[dict[str, object]]:
    return [
        {
            "id": f"TEST-{section.upper()}",
            "section": section,
            "statement": f"{section} rule",
            "citations": ["bazi-skill:time-boundary"],
            "priority": 100,
        }
        for section in sorted(REQUIRED_SECTIONS)
    ]


def test_project_rulebook_has_all_normative_sections():
    from core.bazi_rulebook import load_rulebook

    book = load_rulebook()

    assert set(book.sections) == REQUIRED_SECTIONS
    assert book.version
    assert "version" not in book.public_basis()
    assert "算法版本" not in book.public_basis()


def test_rulebook_rejects_duplicate_rule_ids(tmp_path: Path):
    from core.bazi_rulebook import RuleBookError, load_rulebook

    rules = _minimal_rules()
    rules.append(dict(rules[0]))
    _write_pack(tmp_path, rules)

    with pytest.raises(RuleBookError, match="duplicate rule id"):
        load_rulebook(tmp_path)


def test_rulebook_rejects_unknown_citation(tmp_path: Path):
    from core.bazi_rulebook import RuleBookError, load_rulebook

    rules = _minimal_rules()
    rules[0]["citations"] = ["unknown:source"]
    _write_pack(tmp_path, rules)

    with pytest.raises(RuleBookError, match="unknown citation"):
        load_rulebook(tmp_path)


def test_rulebook_rejects_digest_mismatch(tmp_path: Path):
    from core.bazi_rulebook import RuleBookError, load_rulebook

    _write_pack(tmp_path, _minimal_rules())
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(RuleBookError, match="digest mismatch"):
        load_rulebook(tmp_path)
