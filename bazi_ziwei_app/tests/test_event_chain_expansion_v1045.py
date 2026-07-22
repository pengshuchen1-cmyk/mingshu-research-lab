"""v1.0.4.5 targeted event-chain expansion tests."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHAIN_FIELDS = {
    "traditional_basis",
    "structure_basis",
    "palace_basis",
    "modern_mapping",
    "confidence_basis",
    "anti_triggers",
    "user_visible_basis",
    "required_evidence_count",
    "subtype_rules",
}

PRIORITY_EVENTS = {
    # 创业经营
    "store_operation",
    "customer_growth",
    "customer_complaint",
    "supplier_issue",
    "inventory_pressure",
    "pricing_adjustment",
    "marketing_exposure",
    "content_traffic",
    "account_growth",
    "business_partnership",
    "business_negotiation",
    "operation_cost",
    # 家庭长辈
    "family_issue",
    "elder_issue",
    "family_discussion",
    "family_asset_discussion",
    "household_repair",
    "sibling_relative_issue",
    "parent_health_attention",
    "family_responsibility",
    # 风险损耗
    "minor_loss",
    "delayed_issue",
    "misunderstanding_risk",
    "rule_penalty",
    "impulsive_decision",
    "overcommitment",
    "hidden_cost",
    "emotional_spending",
    "equipment_fault",
    "document_missing",
}

EXTRA_TARGET_EVENTS = {
    # 交通、房产和社交是流月断事最常被用户问到的现实场景。
    "travel_delay",
    "business_trip",
    "vehicle_safety",
    "safety_attention",
    "traffic_ticket",
    "parking_insurance",
    "route_change",
    "long_distance_travel",
    "travel_document",
    "house_viewing",
    "renovation_equipment",
    "appliance_issue",
    "family_asset",
    "landlord_tenant",
    "property_contract",
    "living_environment_change",
    "friend_request",
    "reputation_attention",
    "gossip_dispute",
    "gift_expense",
    "banquet_party",
    "old_friend_contact",
    # 真实师傅样本新增现实词，需要从近似事件升级为独立证据链事件。
    "sudden_change_warning",
    "trapped_commitment",
    "short_term_cooperation",
    "female_friend_social",
    "business_procedure_handling",
    "child_family_responsibility",
    "partner_tolerance",
}


class EventChainExpansionV1045Tests(unittest.TestCase):
    def setUp(self):
        with (ROOT / "rules" / "monthly_event_ontology.json").open(encoding="utf-8") as f:
            self.ontology = json.load(f)
        with (ROOT / "rules" / "monthly_event_trigger_rules.json").open(encoding="utf-8") as f:
            self.trigger_rules = json.load(f)
        self.rule_index = {
            rule.get("target_event_type"): rule
            for rule in self.trigger_rules
            if rule.get("target_event_type")
        }

    def test_event_count_reaches_150_and_can_absorb_master_case_events(self):
        chain_events = [event_type for event_type, item in self.ontology.items() if CHAIN_FIELDS <= set(item)]
        self.assertGreaterEqual(len(self.ontology), 163)
        self.assertGreaterEqual(len(chain_events), 151)
        self.assertLessEqual(len(chain_events), len(self.ontology))

    def test_priority_three_blocks_are_fully_evidence_chain_events(self):
        for event_type in sorted(PRIORITY_EVENTS):
            self.assertIn(event_type, self.ontology)
            item = self.ontology[event_type]
            self.assertTrue(CHAIN_FIELDS <= set(item), event_type)

    def test_extra_target_events_are_evidence_chain_events(self):
        for event_type in sorted(EXTRA_TARGET_EVENTS):
            self.assertIn(event_type, self.ontology)
            item = self.ontology[event_type]
            self.assertTrue(CHAIN_FIELDS <= set(item), event_type)

    def test_new_chain_events_have_basis_mapping_confidence_and_trigger_rules(self):
        for event_type in sorted(PRIORITY_EVENTS | EXTRA_TARGET_EVENTS):
            item = self.ontology[event_type]
            traditional = item.get("traditional_basis", {})
            structure = item.get("structure_basis", {})
            mapping = item.get("modern_mapping", {})
            confidence = item.get("confidence_basis", {})
            self.assertTrue(traditional.get("source_ids"), event_type)
            self.assertTrue(
                traditional.get("ten_god_basis")
                or traditional.get("element_basis")
                or traditional.get("branch_relation_basis")
                or traditional.get("shensha_basis"),
                event_type,
            )
            self.assertTrue(structure.get("required_patterns"), event_type)
            self.assertTrue(mapping.get("positive_expression"), event_type)
            self.assertTrue(mapping.get("neutral_expression"), event_type)
            self.assertTrue(mapping.get("negative_expression"), event_type)
            self.assertTrue(confidence.get("high") and confidence.get("downgrade_reasons"), event_type)
            self.assertGreaterEqual(item.get("required_evidence_count", 0), 2, event_type)

            rule = self.rule_index.get(event_type)
            self.assertIsNotNone(rule, event_type)
            self.assertGreaterEqual(len(rule.get("trigger_conditions", [])), 3, event_type)
            self.assertTrue(rule.get("source_ids"), event_type)
            self.assertTrue(rule.get("basis"), event_type)

    def test_quality_gate_supports_expansion(self):
        from tools.validate_event_chain_quality import validate_event_chain_quality

        report = validate_event_chain_quality(ROOT)
        self.assertTrue(report["basic_passed"], report["priority_fix_events"][:10])
        self.assertGreaterEqual(report["chain_event_count"], 150)
        self.assertEqual([], report["not_allowed_top_events"])


if __name__ == "__main__":
    unittest.main()
