"""v1.0.4 现实事件库扩容测试。"""

from __future__ import annotations

import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_FIELDS = {
    "event_type",
    "label",
    "category",
    "description",
    "possible_real_world_forms",
    "trigger_rules",
    "evidence_template",
    "variants",
    "source_ids",
    "basis",
    "forbidden_expression",
}


class EventPoolExpansion120Tests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "rules", "monthly_event_ontology.json"), encoding="utf-8") as f:
            self.ontology = json.load(f)
        with open(os.path.join(ROOT, "rules", "monthly_event_trigger_rules.json"), encoding="utf-8") as f:
            self.rules = json.load(f)
        with open(os.path.join(ROOT, "rules", "monthly_event_variants.json"), encoding="utf-8") as f:
            self.variants = json.load(f)

    def test_event_type_count_is_120_plus(self):
        self.assertGreaterEqual(len(self.ontology), 120)

    def test_event_type_count_expands_to_270_with_aligned_assets(self):
        self.assertGreaterEqual(len(self.ontology), 270)
        self.assertEqual(len(self.ontology), len(self.rules))
        self.assertEqual(len(self.ontology), len(self.variants))

    def test_priority_categories_expand_by_six_real_events_each(self):
        expected_counts = {
            "财务收入": 20,
            "财务支出": 20,
            "事业职场": 21,
            "创业经营": 18,
            "交通车辆": 18,
            "感情婚恋": 21,
            "学习证书": 14,
            "贵人与资源": 14,
        }
        self.assertGreaterEqual(len(self.ontology), 218)
        for category, expected in expected_counts.items():
            actual = sum(1 for item in self.ontology.values() if item.get("category") == category)
            self.assertGreaterEqual(actual, expected, category)

    def test_each_event_has_required_fields(self):
        for event_type, item in self.ontology.items():
            self.assertTrue(REQUIRED_FIELDS <= set(item), f"{event_type} 字段不完整")
            self.assertGreaterEqual(len(item.get("possible_real_world_forms", [])), 3)
            self.assertGreaterEqual(len(item.get("source_ids", [])), 2)
            self.assertIn(event_type, self.variants)
            self.assertGreaterEqual(len(self.variants[event_type]), 2)

    def test_each_event_has_trigger_rule(self):
        targets = {rule.get("target_event_type") for rule in self.rules}
        self.assertEqual(set(self.ontology), targets)
        for rule in self.rules:
            self.assertGreaterEqual(rule.get("min_trigger_count", 0), 2)
            self.assertGreaterEqual(len(rule.get("trigger_conditions", [])), 3)
            self.assertGreaterEqual(len(rule.get("source_ids", [])), 2)
            self.assertTrue(rule.get("basis", ""))

    def test_each_trigger_condition_has_source_relevance(self):
        for rule in self.rules:
            for cond in rule.get("trigger_conditions", []):
                self.assertIn("source_relevance", cond, rule.get("rule_id"))
                self.assertIsInstance(cond["source_relevance"], (int, float), rule.get("rule_id"))
                self.assertGreaterEqual(cond["source_relevance"], 0.1, rule.get("rule_id"))
                self.assertLessEqual(cond["source_relevance"], 1.0, rule.get("rule_id"))

    def test_finance_income_events_have_specific_source_ids(self):
        specific_prefixes = (
            "source_wealth_",
            "source_output_wealth_",
            "source_contract_payment_",
        )
        income_events = [
            item
            for item in self.ontology.values()
            if item.get("category") == "财务收入"
        ]
        self.assertGreaterEqual(len(income_events), 10)
        for item in income_events:
            source_ids = item.get("source_ids", [])
            self.assertTrue(
                any(str(sid).startswith(specific_prefixes) for sid in source_ids),
                item.get("event_type"),
            )

    def test_finance_expense_events_have_specific_source_ids(self):
        specific_prefixes = (
            "source_expense_",
            "source_peer_wealth_",
            "source_cashflow_",
        )
        expense_events = [
            item
            for item in self.ontology.values()
            if item.get("category") == "财务支出"
        ]
        self.assertGreaterEqual(len(expense_events), 10)
        for item in expense_events:
            source_ids = item.get("source_ids", [])
            self.assertTrue(
                any(str(sid).startswith(specific_prefixes) for sid in source_ids),
                item.get("event_type"),
            )

    def test_career_workplace_events_have_specific_source_ids(self):
        specific_prefixes = (
            "source_officer_career_",
            "source_resource_workflow_",
            "source_output_performance_",
        )
        career_events = [
            item
            for item in self.ontology.values()
            if item.get("category") == "事业职场"
        ]
        self.assertGreaterEqual(len(career_events), 12)
        for item in career_events:
            source_ids = item.get("source_ids", [])
            self.assertTrue(
                any(str(sid).startswith(specific_prefixes) for sid in source_ids),
                item.get("event_type"),
            )

    def test_romance_events_have_specific_source_ids(self):
        specific_prefixes = (
            "source_spouse_relationship_",
            "source_peach_blossom_social_",
            "source_relationship_pressure_",
        )
        romance_events = [
            item
            for item in self.ontology.values()
            if item.get("category") == "感情婚恋"
        ]
        self.assertGreaterEqual(len(romance_events), 12)
        for item in romance_events:
            source_ids = item.get("source_ids", [])
            self.assertTrue(
                any(str(sid).startswith(specific_prefixes) for sid in source_ids),
                item.get("event_type"),
            )

    def test_health_state_events_have_specific_source_ids(self):
        specific_prefixes = (
            "source_health_element_",
            "source_health_rest_",
            "source_health_checkup_",
        )
        health_events = [
            item
            for item in self.ontology.values()
            if item.get("category") == "健康状态"
        ]
        self.assertGreaterEqual(len(health_events), 12)
        for item in health_events:
            source_ids = item.get("source_ids", [])
            self.assertTrue(
                any(str(sid).startswith(specific_prefixes) for sid in source_ids),
                item.get("event_type"),
            )

    def test_expanded_business_traffic_learning_and_resource_events_have_specific_source_ids(self):
        category_prefixes = {
            "创业经营": ("source_business_operation_", "source_customer_growth_", "source_supply_pricing_"),
            "交通车辆": ("source_travel_mobility_", "source_vehicle_safety_", "source_route_document_"),
            "学习证书": ("source_learning_exam_", "source_certificate_training_", "source_skill_credential_"),
            "贵人与资源": ("source_noble_resource_", "source_referral_platform_", "source_mentor_support_"),
        }
        for category, prefixes in category_prefixes.items():
            events = [
                item
                for item in self.ontology.values()
                if item.get("category") == category
            ]
            self.assertGreaterEqual(len(events), 14 if category in {"学习证书", "贵人与资源"} else 18)
            for item in events:
                source_ids = item.get("source_ids", [])
                self.assertTrue(
                    any(str(sid).startswith(prefixes) for sid in source_ids),
                    item.get("event_type"),
                )

    def test_event_categories_are_rich(self):
        categories = {item.get("category") for item in self.ontology.values()}
        self.assertGreaterEqual(len(categories), 14)

    def test_event_categories_expand_to_24_with_source_support(self):
        expected_new_categories = {
            "证件手续",
            "客户销售",
            "平台线上",
            "供应库存",
            "车辆安全",
            "公共交通",
            "导师前辈",
        }
        categories = {item.get("category") for item in self.ontology.values()}
        self.assertGreaterEqual(len(categories), 24)
        self.assertTrue(expected_new_categories <= categories)

        with open(os.path.join(ROOT, "rules", "source_registry.json"), encoding="utf-8") as f:
            registry = json.load(f)
        source_domains = {
            sid: set(entry.get("domains", []))
            for sid, entry in registry.items()
        }
        for category in expected_new_categories:
            category_events = [
                item
                for item in self.ontology.values()
                if item.get("category") == category
            ]
            self.assertGreaterEqual(len(category_events), 1, category)
            for item in category_events:
                self.assertTrue(
                    any(category in source_domains.get(sid, set()) for sid in item.get("source_ids", [])),
                    item.get("event_type"),
                )


if __name__ == "__main__":
    unittest.main()
