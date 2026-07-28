from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "domain",
    (
        "career",
        "family",
        "health_advisory",
        "children",
        "education",
        "relocation",
        "property",
        "benefactor",
    ),
)
def test_each_extended_domain_has_local_fact_items(domain):
    from core.ai_domain_facts import domain_fact_items
    from tests.bazi_ai_fixtures import synthetic_chart

    items = domain_fact_items(synthetic_chart(), domain)

    assert len(items) >= 2
    assert all(item.source == "domain" for item in items)
    text = " ".join(item.text for item in items)
    if domain == "health_advisory":
        assert all(term not in text for term in ("确诊", "疾病", "治疗"))
    if domain == "children":
        assert all(term not in text for term in ("已有孩子", "子女数量", "必定生育"))


def test_missing_domain_fields_are_skipped_without_placeholder_conclusions():
    from core.ai_domain_facts import domain_fact_items

    assert domain_fact_items({}, "career") == []
    assert domain_fact_items({"pillars": {}}, "family") == []


def test_health_and_children_state_limits_are_explicit():
    from core.ai_domain_facts import domain_fact_items
    from tests.bazi_ai_fixtures import synthetic_chart

    chart = synthetic_chart()
    health = " ".join(item.text for item in domain_fact_items(chart, "health_advisory"))
    children = " ".join(item.text for item in domain_fact_items(chart, "children"))

    assert "现实健康状态未知" in health
    assert "现实生育及子女状态未知" in children
