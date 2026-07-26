"""v1.0.4.2 medium-high frequency event evidence-chain expansion tests."""

from __future__ import annotations

import json
import os
import sys
import unittest
from collections import Counter


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

FORBIDDEN_HEALTH_WORDS = ["必得病", "严重疾病", "灾祸", "血光", "必有大病", "短命"]


class EventEvidenceChainV1042Tests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "rules", "monthly_event_ontology.json"), encoding="utf-8") as f:
            self.ontology = json.load(f)
        self.chain_events = {
            event_type: item
            for event_type, item in self.ontology.items()
            if CHAIN_FIELDS <= set(item)
        }

    def test_chain_event_count_expands_beyond_v1042_baseline_without_full_rewrite(self):
        self.assertGreaterEqual(len(self.chain_events), 80)
        self.assertLessEqual(len(self.chain_events), len(self.ontology))

    def test_priority_categories_have_medium_high_frequency_coverage(self):
        counts = Counter(item.get("category", "") for item in self.chain_events.values())
        self.assertGreaterEqual(counts["财务收入"] + counts["财务支出"], 22)
        self.assertGreaterEqual(counts["合同法务"], 9)
        self.assertGreaterEqual(counts["事业职场"], 12)
        self.assertGreaterEqual(counts["感情婚恋"], 12)
        self.assertGreaterEqual(counts["健康状态"], 12)

    def test_each_chain_event_has_traditional_and_structure_basis(self):
        for event_type, item in self.chain_events.items():
            trad = item.get("traditional_basis", {})
            struct = item.get("structure_basis", {})
            self.assertGreaterEqual(len(trad.get("ten_god_basis", [])), 1, event_type)
            self.assertGreaterEqual(len(struct.get("required_patterns", [])), 1, event_type)
            self.assertGreaterEqual(item.get("required_evidence_count", 0), 2, event_type)
            mapping = item.get("modern_mapping", {})
            self.assertGreaterEqual(len(mapping.get("positive_expression", [])), 2, event_type)
            self.assertGreaterEqual(len(mapping.get("neutral_expression", [])), 2, event_type)
            self.assertGreaterEqual(len(mapping.get("negative_expression", [])), 2, event_type)

    def test_finance_templates_distinguish_required_subtypes(self):
        finance_text = "\n".join(
            json.dumps(item.get("subtype_rules", {}), ensure_ascii=False)
            for item in self.chain_events.values()
            if item.get("category") in {"财务收入", "财务支出"}
        )
        for label in ["收入型", "延迟型", "支出型", "风险型", "分账型", "现金流型"]:
            self.assertIn(label, finance_text)

    def test_health_templates_are_life_state_not_medical_diagnosis(self):
        health_text = "\n".join(
            json.dumps({k: v for k, v in item.items() if k != "forbidden_expression"}, ensure_ascii=False)
            for item in self.chain_events.values()
            if item.get("category") == "健康状态"
        )
        for word in FORBIDDEN_HEALTH_WORDS:
            self.assertNotIn(word, health_text)
        self.assertIn("不做医学判断", health_text)
        self.assertIn("专业医生", health_text)

    def test_related_expense_contract_and_relationship_events_merge(self):
        from core.monthly_event_activation_bridge import merge_related_event_clusters

        events = [
            {"event_type": "wealth_outflow", "label": "支出增加", "category": "财务支出", "score": 70, "trigger_count": 4, "evidence": []},
            {"event_type": "vehicle_expense", "label": "车辆支出", "category": "交通车辆", "score": 68, "trigger_count": 3, "evidence": []},
            {"event_type": "home_repair", "label": "家中维修", "category": "房产居住", "score": 65, "trigger_count": 3, "evidence": []},
            {"event_type": "human_cost", "label": "人情破耗", "category": "财务支出", "score": 64, "trigger_count": 3, "evidence": []},
            {"event_type": "contract_document", "label": "合同文书", "category": "合同法务", "score": 63, "trigger_count": 3, "evidence": []},
            {"event_type": "cooperation_boundary", "label": "合作边界影响关系", "category": "感情婚恋", "score": 62, "trigger_count": 3, "evidence": []},
            {"event_type": "misunderstanding", "label": "误会解释", "category": "感情婚恋", "score": 61, "trigger_count": 3, "evidence": []},
            {"event_type": "family_pressure", "label": "家庭介入", "category": "感情婚恋", "score": 60, "trigger_count": 3, "evidence": []},
        ]
        merged = merge_related_event_clusters(events)
        labels = [item.get("label") for item in merged]
        types = [item.get("event_type") for item in merged]
        self.assertIn("现实支出压力增加", labels)
        self.assertIn("合作规则与边界需要重新确认", labels)
        self.assertIn("关系沟通与外部压力增加", labels)
        self.assertTrue(any(t.startswith("expense_") and t != "expense_pressure_cluster" for t in types))

    def test_source_specificity_participates_in_confidence_downgrade(self):
        from core.monthly_event_activation_bridge import _evaluate_event_confidence

        broad_registry = {
            "ming_li_tan_yuan": {
                "authority_weight": 0.72,
                "specificity": "broad",
                "domains": ["流月", "刑冲合害"],
                "broadness_penalty": 0.35,
            },
            "wu_xing_jing_ji": {
                "authority_weight": 0.7,
                "specificity": "broad",
                "domains": ["五行取象", "神煞资料"],
                "broadness_penalty": 0.35,
            },
            "specialized_event_reference": {
                "authority_weight": 0.78,
                "specificity": "case",
                "domains": ["财务支出", "感情婚恋", "社交人情"],
                "broadness_penalty": 0,
            },
        }
        ontology = {
            "category": "财务支出",
            "traditional_basis": {"ten_god_basis": ["财星受冲时支出信号增加。"]},
            "required_evidence_count": 2,
        }
        evidence = [
            {"type": "is_wealth_month", "source_ids": ["ming_li_tan_yuan"]},
            {"type": "element", "source_ids": ["wu_xing_jing_ji"]},
            {"type": "clash_day_branch", "source_ids": ["ming_li_tan_yuan"]},
            {"type": "group_count_at_least", "source_ids": ["wu_xing_jing_ji"]},
        ]
        broad_result = _evaluate_event_confidence(
            {
                "trigger_count": 4,
                "evidence": evidence,
                "source_ids": ["ming_li_tan_yuan", "wu_xing_jing_ji"],
            },
            ontology,
            source_registry=broad_registry,
        )
        specialized_result = _evaluate_event_confidence(
            {
                "trigger_count": 4,
                "evidence": evidence + [{"type": "month_index", "source_ids": ["specialized_event_reference"], "source_relevance": 0.95}],
                "source_ids": ["ming_li_tan_yuan", "wu_xing_jing_ji", "specialized_event_reference"],
            },
            ontology,
            source_registry=broad_registry,
        )
        low_relevance_specialized_result = _evaluate_event_confidence(
            {
                "trigger_count": 4,
                "evidence": evidence + [{"type": "month_index", "source_ids": ["specialized_event_reference"], "source_relevance": 0.2}],
                "source_ids": ["ming_li_tan_yuan", "wu_xing_jing_ji", "specialized_event_reference"],
            },
            ontology,
            source_registry=broad_registry,
        )

        self.assertEqual(broad_result["confidence_level"], "medium")
        self.assertIn("来源过于宽泛，不能支撑高置信事件。", broad_result["downgrade_reasons"])
        self.assertLess(
            broad_result["source_confidence_score"],
            specialized_result["source_confidence_score"],
        )
        self.assertLess(
            low_relevance_specialized_result["source_confidence_score"],
            specialized_result["source_confidence_score"],
        )
        self.assertEqual(specialized_result["confidence_level"], "high")


if __name__ == "__main__":
    unittest.main()
