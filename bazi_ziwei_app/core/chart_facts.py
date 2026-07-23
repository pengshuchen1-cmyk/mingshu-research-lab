"""Immutable, serializable fact contract shared by reports and AI Q&A."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Mapping


@dataclass(frozen=True)
class ChartFacts:
    gender: str
    pillars: tuple[str, str, str, str]
    day_master: str
    hidden_stems: tuple[tuple[str, tuple[str, ...]], ...]
    ten_gods_json: str
    element_counts: tuple[tuple[str, float], ...]
    time_mode: str
    pillar_basis: str
    dayun_direction: str
    dayun_start: str
    strength: str
    strength_evidence: tuple[str, ...]
    favorable_elements: tuple[str, ...]
    unfavorable_elements: tuple[str, ...]
    pattern: str
    pattern_evidence: tuple[str, ...]
    wealth: str
    wealth_evidence: tuple[str, ...]
    relationship: str
    relationship_evidence: tuple[str, ...]
    internal_rule_version: str
    rule_ids: tuple[str, ...]
    relationship_stability_signals: tuple[tuple[str, str, str], ...] = ()
    current_context_json: str = "{}"

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ChartFacts":
        """Load an already attached canonical projection without consulting legacy fields."""
        pillars = tuple(str(item) for item in (value.get("pillars") or []))
        if len(pillars) != 4 or not all(pillars[:3]):
            raise ValueError("invalid attached ChartFacts pillars")
        hidden_raw = value.get("hidden_stems") or {}
        if not isinstance(hidden_raw, Mapping):
            raise ValueError("invalid attached ChartFacts hidden stems")
        hidden = tuple(
            (key, tuple(str(item) for item in (hidden_raw.get(key) or [])))
            for key in ("year", "month", "day", "hour")
        )
        strength = value.get("strength") or {}
        pattern = value.get("pattern") or {}
        wealth = value.get("wealth") or {}
        relationship = value.get("relationship") or {}
        dayun = value.get("dayun") or {}
        for name, item in (
            ("strength", strength), ("pattern", pattern), ("wealth", wealth),
            ("relationship", relationship), ("dayun", dayun),
        ):
            if not isinstance(item, Mapping):
                raise ValueError(f"invalid attached ChartFacts {name}")
        elements = value.get("element_counts") or {}
        if not isinstance(elements, Mapping):
            raise ValueError("invalid attached ChartFacts elements")
        return cls(
            gender=str(value.get("gender", "")),
            pillars=pillars,  # type: ignore[arg-type]
            day_master=str(value.get("day_master", "")),
            hidden_stems=hidden,
            ten_gods_json=json.dumps(value.get("ten_gods") or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            element_counts=tuple((str(key), float(item)) for key, item in sorted(elements.items())),
            time_mode=str(value.get("time_mode", "")),
            pillar_basis=str(value.get("pillar_basis", "")),
            dayun_direction=str(dayun.get("direction", "")),
            dayun_start=str(dayun.get("start", "")),
            strength=str(strength.get("classification", "")),
            strength_evidence=tuple(str(item) for item in (strength.get("evidence") or [])),
            favorable_elements=tuple(str(item) for item in (strength.get("favorable_elements") or [])),
            unfavorable_elements=tuple(str(item) for item in (strength.get("unfavorable_elements") or [])),
            pattern=str(pattern.get("classification", "")),
            pattern_evidence=tuple(str(item) for item in (pattern.get("evidence") or [])),
            wealth=str(wealth.get("summary", "")),
            wealth_evidence=tuple(str(item) for item in (wealth.get("evidence") or [])),
            relationship=str(relationship.get("summary", "")),
            relationship_evidence=tuple(str(item) for item in (relationship.get("evidence") or [])),
            internal_rule_version=str(value.get("internal_rule_version", "")),
            rule_ids=tuple(str(item) for item in (value.get("rule_ids") or [])),
            relationship_stability_signals=_relationship_stability_signals(
                relationship.get("stability_signals")
            ),
            current_context_json=json.dumps(value.get("current_context") or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "gender": self.gender,
            "pillars": list(self.pillars),
            "day_master": self.day_master,
            "hidden_stems": {
                key: list(values) for key, values in self.hidden_stems
            },
            "ten_gods": json.loads(self.ten_gods_json),
            "element_counts": dict(self.element_counts),
            "time_mode": self.time_mode,
            "pillar_basis": self.pillar_basis,
            "dayun": {
                "direction": self.dayun_direction,
                "start": self.dayun_start,
            },
            "strength": {
                "classification": self.strength,
                "evidence": list(self.strength_evidence),
                "favorable_elements": list(self.favorable_elements),
                "unfavorable_elements": list(self.unfavorable_elements),
            },
            "pattern": {
                "classification": self.pattern,
                "evidence": list(self.pattern_evidence),
            },
            "wealth": {
                "summary": self.wealth,
                "evidence": list(self.wealth_evidence),
            },
            "relationship": {
                "summary": self.relationship,
                "evidence": list(self.relationship_evidence),
                "stability_signals": [
                    {
                        "polarity": polarity,
                        "fact": fact,
                        "explanation": explanation,
                    }
                    for polarity, fact, explanation
                    in self.relationship_stability_signals
                ],
            },
            "internal_rule_version": self.internal_rule_version,
            "rule_ids": list(self.rule_ids),
            "current_context": json.loads(self.current_context_json),
        }

    def public_summary(self) -> dict[str, object]:
        return {
            "时间模式": self.time_mode,
            "四柱计算依据": self.pillar_basis,
            "起运方向": self.dayun_direction,
            "起运时间": self.dayun_start,
            "强弱证据": list(self.strength_evidence),
            "格局": self.pattern,
            "财运": self.wealth,
            "姻缘": self.relationship,
        }

    def with_current_context(self, value: Mapping[str, object]) -> "ChartFacts":
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return replace(self, current_context_json=encoded)

    def fingerprint(self) -> str:
        payload = self.to_dict()
        payload.pop("current_context", None)
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence_texts(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    texts: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            texts.append(item.strip())
        elif isinstance(item, dict):
            text = item.get("explanation") or item.get("text") or item.get("fact")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
    return tuple(texts)


def _relationship_stability_signals(
    value: object,
) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(value, list):
        return ()
    signals: list[tuple[str, str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        polarity = str(item.get("polarity") or "").strip()
        fact = str(item.get("fact") or "").strip()
        explanation = str(item.get("explanation") or "").strip()
        if polarity or fact or explanation:
            signals.append((polarity, fact, explanation))
    return tuple(signals)


def build_chart_facts(chart: dict) -> ChartFacts:
    pillars = chart.get("pillars", {})
    pillar_order = ("year", "month", "day", "hour")
    pillar_texts = tuple(str(pillars.get(key, {}).get("pillar", "")) for key in pillar_order)
    hidden = tuple(
        (
            key,
            tuple(
                str(item.get("gan", ""))
                for item in chart.get("hidden_stems", {}).get(key, [])
                if item.get("gan")
            ),
        )
        for key in pillar_order
    )
    strength = chart.get("day_master_strength", {})
    strength_evidence = tuple(
        str(strength.get(key, {}).get("text", ""))
        for key in ("de_ling", "de_di", "de_shi")
        if strength.get(key, {}).get("text")
    )
    if strength.get("evidence"):
        strength_evidence = _evidence_texts(strength.get("evidence"))

    pattern = chart.get("pattern_analysis", {})
    wealth = chart.get("wealth_analysis", {})
    relationship = chart.get("relationship_analysis", {})
    dayun = chart.get("dayun_basis", {})
    profile = chart.get("profile", {})
    gender = "female" if str(profile.get("gender", "")).lower() in {"女", "female", "f"} else "male"
    return ChartFacts(
        gender=gender,
        pillars=pillar_texts,
        day_master=str(chart.get("day_master", "")),
        hidden_stems=hidden,
        ten_gods_json=json.dumps(
            chart.get("ten_gods", {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        element_counts=tuple(
            (str(key), float(value))
            for key, value in sorted(chart.get("five_elements", {}).items())
        ),
        time_mode=str(chart.get("time_mode_label") or chart.get("time_mode", "")),
        pillar_basis=str(chart.get("pillar_evidence", {}).get("public_text", "")),
        dayun_direction=str(dayun.get("direction_label", "待计算")),
        dayun_start=str(dayun.get("start_text", "待计算")),
        strength=str(strength.get("strength", "暂无法判断")),
        strength_evidence=strength_evidence,
        favorable_elements=tuple(strength.get("favorable_elements", [])),
        unfavorable_elements=tuple(strength.get("unfavorable_elements", [])),
        pattern=str(pattern.get("plain_text") or pattern.get("pattern", "暂无法判断")),
        pattern_evidence=_evidence_texts(pattern.get("evidence", [])),
        wealth=str(wealth.get("public_text", "待分析")),
        wealth_evidence=_evidence_texts(wealth.get("evidence", [])),
        relationship=str(relationship.get("public_text", "待分析")),
        relationship_evidence=_evidence_texts(relationship.get("evidence", [])),
        internal_rule_version=str(chart.get("rule_version", "")),
        rule_ids=tuple(chart.get("pillar_evidence", {}).get("rule_ids", [])),
        relationship_stability_signals=_relationship_stability_signals(
            relationship.get("stability_signals")
        ),
        current_context_json=json.dumps(
            chart.get("current_context", {}),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


def attach_chart_facts(chart: dict) -> ChartFacts:
    facts = build_chart_facts(chart)
    chart["facts"] = facts.to_dict()
    chart["public_summary"] = facts.public_summary()
    chart["chart_fingerprint_v2"] = facts.fingerprint()
    return facts


def chart_facts_from_chart(chart: Mapping[str, object]) -> ChartFacts:
    """Require and load the attached normative facts for every downstream consumer."""
    raw = chart.get("facts")
    if not isinstance(raw, Mapping):
        raise ValueError("chart is missing canonical ChartFacts; rebuild it with the rule engine")
    return ChartFacts.from_dict(raw)
