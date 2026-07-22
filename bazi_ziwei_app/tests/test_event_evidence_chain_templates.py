"""v1.0.4.1 high-frequency event evidence-chain template tests."""

from __future__ import annotations

import json
import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


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

TEMPLATE_EVENT_TYPES = {
    "nobleman_help",
    "client_payment",
    "delayed_payment_arrival",
    "wealth_outflow",
    "asset_purchase",
    "vehicle_repair",
    "home_repair",
    "rental_move",
    "contract_document",
    "social_drinking",
    "relationship_progress",
    "medical_attention",
    "project_breakthrough",
    "project_delay",
}

NOBLEMAN_SUBTYPES = {
    "长辈贵人",
    "同辈贵人",
    "客户贵人",
    "上级贵人",
    "专业人士贵人",
    "旧关系贵人",
    "平台贵人",
    "家庭贵人",
    "伴侣/合作贵人",
    "暗中贵人",
}


class EventEvidenceChainTemplateTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "rules", "monthly_event_ontology.json"), encoding="utf-8") as f:
            self.ontology = json.load(f)

    def test_high_frequency_templates_have_full_evidence_chain_fields(self):
        missing_events = TEMPLATE_EVENT_TYPES - set(self.ontology)
        self.assertFalse(missing_events, f"样板事件不存在：{missing_events}")
        for event_type in TEMPLATE_EVENT_TYPES:
            item = self.ontology[event_type]
            self.assertTrue(CHAIN_FIELDS <= set(item), f"{event_type} 缺少证据链字段")
            mapping = item.get("modern_mapping", {})
            for key in ("positive_expression", "neutral_expression", "negative_expression"):
                self.assertGreaterEqual(len(mapping.get(key, [])), 2, f"{event_type} 缺少{key}")
            self.assertGreaterEqual(item.get("required_evidence_count", 0), 2)

    def test_nobleman_help_has_source_subtypes(self):
        subtypes = set(self.ontology["nobleman_help"].get("subtype_rules", {}))
        self.assertTrue(NOBLEMAN_SUBTYPES <= subtypes)

    def test_enrichment_keeps_old_events_safe_and_adds_chain_fields(self):
        from core.monthly_event_activation_bridge import _enrich_candidate

        old_style_ontology = {
            "plain_event": {
                "label": "旧事件",
                "category": "测试",
                "basis": "旧字段依据",
                "possible_real_world_forms": ["观察事项", "现实反馈", "行动线索"],
                "risk_points": ["边界不清"],
                "safe_expression": "旧事件可以继续显示。",
            }
        }
        event = _enrich_candidate(
            {
                "event_type": "plain_event",
                "score": 40,
                "trigger_count": 2,
                "evidence": [{"type": "ten_god_group", "detail": "十神组匹配"}],
                "source_ids": [],
            },
            old_style_ontology,
            None,
            {},
        )
        self.assertEqual(event["label"], "旧事件")
        self.assertEqual(event["traditional_basis"], {})
        self.assertEqual(event["confidence_level"], "low")

    def test_nobleman_subtype_changes_with_trigger_context(self):
        from core.monthly_event_activation_bridge import _enrich_candidate

        evidence = [
            {"type": "is_resource_month", "detail": "印星流月"},
            {"type": "favorable_relation", "detail": "喜用相关"},
            {"type": "group_count_at_least", "detail": "原局印星不弱"},
            {"type": "clash_month_branch", "detail": "事业宫位被引动"},
        ]
        event = _enrich_candidate(
            {
                "event_type": "nobleman_help",
                "score": 70,
                "trigger_count": 4,
                "evidence": evidence,
                "source_ids": ["yuan_hai_zi_ping"],
            },
            self.ontology,
            None,
            {},
            ctx={
                "is_resource_month": True,
                "is_peer_month": False,
                "is_wealth_month": False,
                "is_officer_month": False,
                "is_output_month": False,
                "clash_month_branch": True,
                "clash_year_branch": False,
                "clash_day_branch": False,
                "favorable_relation": "喜用相关",
                "group_counts": {"resource": 2, "peer": 0, "wealth": 0, "officer": 0, "output": 0},
            },
        )
        self.assertIn(event["subtype_label"], {"专业人士贵人", "上级贵人", "平台贵人"})
        self.assertIn("user_visible_basis", event)
        self.assertIn(event["confidence_level"], {"medium", "high"})
        self.assertIn(event["subtype_label"], event["one_line"])
        self.assertIn("边界", event["advice"])

    def test_related_social_resource_events_can_be_merged(self):
        from core.monthly_event_activation_bridge import merge_related_event_clusters

        events = [
            {"event_type": "social_drinking", "label": "酒局应酬", "category": "社交人情", "score": 70, "trigger_count": 4, "evidence": []},
            {"event_type": "resource_connection", "label": "资源连接", "category": "贵人与资源", "score": 68, "trigger_count": 3, "evidence": []},
            {"event_type": "referral_opportunity", "label": "转介绍机会", "category": "贵人与资源", "score": 66, "trigger_count": 3, "evidence": []},
            {"event_type": "vehicle_repair", "label": "车辆维修", "category": "交通车辆", "score": 50, "trigger_count": 2, "evidence": []},
        ]
        merged = merge_related_event_clusters(events)
        labels = [item.get("label") for item in merged]
        self.assertIn("同辈圈层或社交场景带来资源线索", labels)
        self.assertNotIn("酒局应酬", labels)
        self.assertIn("车辆维修", labels)


if __name__ == "__main__":
    unittest.main()
