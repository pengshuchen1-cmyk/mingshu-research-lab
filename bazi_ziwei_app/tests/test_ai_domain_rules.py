from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_extended_ai_domains_have_normative_rules():
    from core.bazi_rulebook import load_rulebook

    book = load_rulebook()
    required = {
        "career",
        "family",
        "health_advisory",
        "children",
        "education",
        "relocation",
        "property",
        "benefactor",
    }

    assert required <= set(book.sections)
    for section in required:
        assert len(book.sections[section]) >= 2
        assert all(rule.citations for rule in book.sections[section])


@pytest.mark.parametrize("category", ("子女养育", "教育学习", "贵人与资源"))
def test_ming_li_tan_yuan_extended_domains_reach_source_confidence_consumer(category: str):
    from core.monthly_event_activation_bridge import _evaluate_source_confidence

    registry_path = Path(__file__).resolve().parents[1] / "rules" / "source_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    confidence = _evaluate_source_confidence(
        {"source_ids": ["ming_li_tan_yuan"]},
        {"category": category},
        registry,
    )

    assert category in registry["ming_li_tan_yuan"]["domains"]
    assert confidence["source_has_category_match"] is True
