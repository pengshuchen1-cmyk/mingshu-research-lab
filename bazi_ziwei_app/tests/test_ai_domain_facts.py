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


def test_equal_five_element_counts_do_not_claim_the_same_element_is_high_and_low():
    from core.ai_domain_facts import domain_fact_items

    text = " ".join(
        item.text
        for item in domain_fact_items(
            {"five_elements": {"木": 1, "火": 1, "土": 1, "金": 1, "水": 1}},
            "health_advisory",
        )
    )

    assert "本地五行计数为木1、火1、土1、金1、水1" in text
    assert "无唯一偏盛或偏弱元素" in text
    assert "相对偏盛为" not in text
    assert "相对偏弱为" not in text


def test_partial_five_element_ties_are_listed_without_false_extremum_claims():
    from core.ai_domain_facts import domain_fact_items

    high_tie = " ".join(
        item.text
        for item in domain_fact_items(
            {"five_elements": {"木": 3, "火": 3, "土": 2, "水": 1}},
            "health_advisory",
        )
    )
    low_tie = " ".join(
        item.text
        for item in domain_fact_items(
            {"five_elements": {"木": 3, "火": 1, "土": 2, "水": 1}},
            "health_advisory",
        )
    )

    assert "最高值并列为木、火，无唯一偏盛元素" in high_tie
    assert "相对偏弱为水" in high_tie
    assert "相对偏盛为木" in low_tie
    assert "最低值并列为火、水，无唯一偏弱元素" in low_tie


@pytest.mark.parametrize(
    ("domain", "expected_id", "expected_text"),
    (
        ("health_advisory", "domain.health_advisory.status_limit", "现实健康状态未知"),
        ("children", "domain.children.status_limit", "现实生育及子女状态未知"),
    ),
)
def test_unknown_reality_state_boundary_survives_missing_structure(
    domain,
    expected_id,
    expected_text,
):
    from core.ai_domain_facts import domain_fact_items

    items = domain_fact_items({}, domain)

    assert [item.id for item in items] == [expected_id]
    assert expected_text in items[0].text
