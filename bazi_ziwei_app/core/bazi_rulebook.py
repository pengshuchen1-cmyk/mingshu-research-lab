"""Project-local normative rules for four-pillar calculation and interpretation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


RULE_DIR = Path(__file__).resolve().parents[1] / "rules" / "bazi_skill"
SOURCE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "rules" / "source_registry.json"
REQUIRED_SECTIONS = frozenset(
    {
        "calendar",
        "pillars",
        "dayun",
        "strength",
        "pattern",
        "wealth",
        "relationship",
        "safety",
    }
)


class RuleBookError(ValueError):
    """Raised when the local rule pack is incomplete or has been altered."""


@dataclass(frozen=True)
class Rule:
    id: str
    section: str
    statement: str
    citations: tuple[str, ...]
    priority: int


@dataclass(frozen=True)
class RuleBook:
    version: str
    rules: tuple[Rule, ...]
    sections: Mapping[str, tuple[Rule, ...]]

    def by_id(self, rule_id: str) -> Rule:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        raise KeyError(rule_id)

    def public_basis(self) -> dict[str, str]:
        pillar_ids = (
            "CAL-YEAR-LICHUN",
            "CAL-MONTH-JIE",
            "CAL-DAY-ZI23",
            "PILLAR-MONTH-FIVETIGER",
            "PILLAR-HOUR-FIVERAT",
        )
        return {
            "时间模式": self.by_id("CAL-TIME-CST").statement,
            "四柱计算依据": "；".join(self.by_id(rule_id).statement for rule_id in pillar_ids),
            "起运方向": self.by_id("DAYUN-DIRECTION").statement,
            "起运时间": self.by_id("DAYUN-START-DIV3").statement,
        }


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleBookError(f"cannot load rule file: {path.name}") from exc


def _known_citations(manifest: dict[str, object]) -> set[str]:
    declared = manifest.get("citation_keys")
    if not isinstance(declared, list) or not all(isinstance(item, str) for item in declared):
        raise RuleBookError("manifest citation_keys must be a string list")
    source_registry = _read_json(SOURCE_REGISTRY_PATH)
    if not isinstance(source_registry, dict):
        raise RuleBookError("source registry must be an object")
    external = {item for item in declared if not item.startswith("bazi-skill:")}
    missing = external - set(source_registry)
    if missing:
        raise RuleBookError(f"unknown citation in manifest: {sorted(missing)[0]}")
    return set(declared)


@lru_cache(maxsize=8)
def load_rulebook(rule_dir: Path | None = None) -> RuleBook:
    root = Path(rule_dir or RULE_DIR).resolve()
    manifest = _read_json(root / "manifest.json")
    if not isinstance(manifest, dict):
        raise RuleBookError("manifest must be an object")

    version = manifest.get("version")
    file_entries = manifest.get("files")
    if not isinstance(version, str) or not version.strip():
        raise RuleBookError("manifest version is required")
    if not isinstance(file_entries, list) or not file_entries:
        raise RuleBookError("manifest files are required")

    allowed_citations = _known_citations(manifest)
    seen_ids: set[str] = set()
    rules: list[Rule] = []
    sections: dict[str, list[Rule]] = {name: [] for name in REQUIRED_SECTIONS}

    for entry in file_entries:
        if not isinstance(entry, dict):
            raise RuleBookError("manifest file entry must be an object")
        relative_path = entry.get("path")
        expected_digest = entry.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(expected_digest, str):
            raise RuleBookError("manifest file path and sha256 are required")
        path = (root / relative_path).resolve()
        if root not in path.parents:
            raise RuleBookError("rule file must stay inside rule directory")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise RuleBookError(f"cannot load rule file: {relative_path}") from exc
        actual_digest = hashlib.sha256(raw).hexdigest()
        if actual_digest != expected_digest:
            raise RuleBookError(f"digest mismatch: {relative_path}")
        payload = _read_json(path)
        if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
            raise RuleBookError(f"rules list is required: {relative_path}")

        for item in payload["rules"]:
            if not isinstance(item, dict):
                raise RuleBookError("rule must be an object")
            rule_id = item.get("id")
            section = item.get("section")
            statement = item.get("statement")
            citations = item.get("citations")
            priority = item.get("priority")
            if not isinstance(rule_id, str) or not rule_id:
                raise RuleBookError("rule id is required")
            if rule_id in seen_ids:
                raise RuleBookError(f"duplicate rule id: {rule_id}")
            if section not in REQUIRED_SECTIONS:
                raise RuleBookError(f"invalid section: {section}")
            if not isinstance(statement, str) or not statement.strip():
                raise RuleBookError(f"statement is required: {rule_id}")
            if not isinstance(citations, list) or not citations:
                raise RuleBookError(f"citations are required: {rule_id}")
            if not all(isinstance(citation, str) for citation in citations):
                raise RuleBookError(f"invalid citation: {rule_id}")
            unknown = set(citations) - allowed_citations
            if unknown:
                raise RuleBookError(f"unknown citation: {sorted(unknown)[0]}")
            if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
                raise RuleBookError(f"invalid priority: {rule_id}")
            rule = Rule(rule_id, section, statement.strip(), tuple(citations), priority)
            seen_ids.add(rule_id)
            rules.append(rule)
            sections[section].append(rule)

    missing_sections = {name for name, values in sections.items() if not values}
    if missing_sections:
        raise RuleBookError(f"missing section: {sorted(missing_sections)[0]}")

    ordered_rules = tuple(sorted(rules, key=lambda rule: (-rule.priority, rule.id)))
    frozen_sections = MappingProxyType(
        {
            name: tuple(sorted(values, key=lambda rule: (-rule.priority, rule.id)))
            for name, values in sorted(sections.items())
        }
    )
    return RuleBook(version=version, rules=ordered_rules, sections=frozen_sections)
