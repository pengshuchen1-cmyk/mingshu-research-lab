"""流月事件资产覆盖测试 — v1.3-A3"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_TYPES_COUNT = 120

class TestMonthlyEventAssetCoverage(unittest.TestCase):

    def test_ontology_exists(self):
        """monthly_event_ontology.json 存在且可加载。"""
        path = os.path.join(ROOT, "rules", "monthly_event_ontology.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)

    def test_ontology_120_plus_types(self):
        """ontology 至少包含 120 个 event_type。"""
        path = os.path.join(ROOT, "rules", "monthly_event_ontology.json")
        with open(path) as f:
            data = json.load(f)
        self.assertGreaterEqual(len(data), EVENT_TYPES_COUNT)

    def test_ontology_required_fields(self):
        """每个 ontology 条目包含必需字段。"""
        path = os.path.join(ROOT, "rules", "monthly_event_ontology.json")
        with open(path) as f:
            data = json.load(f)
        required = [
            "event_type", "label", "category", "description",
            "possible_real_world_forms", "trigger_rules", "evidence_template",
            "variants", "source_ids", "basis", "forbidden_expression",
        ]
        for et, entry in data.items():
            for field in required:
                self.assertIn(field, entry, f"{et} 缺少 {field}")

    def test_trigger_rules_exist(self):
        """monthly_event_trigger_rules.json 存在且可加载。"""
        path = os.path.join(ROOT, "rules", "monthly_event_trigger_rules.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_trigger_rules_have_source_ids(self):
        """每条 trigger_rule 有 source_ids 和 basis。"""
        path = os.path.join(ROOT, "rules", "monthly_event_trigger_rules.json")
        with open(path) as f:
            data = json.load(f)
        for rule in data:
            self.assertIn("source_ids", rule, f"{rule.get('rule_id','?')} 缺 source_ids")
            self.assertIn("basis", rule, f"{rule.get('rule_id','?')} 缺 basis")

    def test_variants_covers_all_types(self):
        """variants.json 覆盖全部 event_type。"""
        path = os.path.join(ROOT, "rules", "monthly_event_variants.json")
        with open(path) as f:
            data = json.load(f)
        with open(os.path.join(ROOT, "rules", "monthly_event_ontology.json")) as f:
            ontology = json.load(f)
        self.assertEqual(set(data), set(ontology))

    def test_variants_has_two_per_type(self):
        """每个 event_type 至少 2 个变体。"""
        path = os.path.join(ROOT, "rules", "monthly_event_variants.json")
        with open(path) as f:
            data = json.load(f)
        for et, variants in data.items():
            self.assertGreaterEqual(len(variants), 2, f"{et} 少于 2 个变体")

    def test_variant_required_fields(self):
        """每个变体包含必需字段。"""
        path = os.path.join(ROOT, "rules", "monthly_event_variants.json")
        with open(path) as f:
            data = json.load(f)
        required = ["variant_id", "one_line", "real_world_signals", "risk_points", "advice"]
        for et, variants in data.items():
            for v in variants:
                for field in required:
                    self.assertIn(field, v, f"{et}/{v.get('variant_id','?')} 缺 {field}")

    def test_specific_event_rules_exist(self):
        """monthly_specific_event_rules.json 存在且可加载。"""
        path = os.path.join(ROOT, "rules", "monthly_specific_event_rules.json")
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertIsInstance(data, list)

    def test_monthly_event_rules_exist(self):
        """monthly_event_rules.json 可加载。"""
        path = os.path.join(ROOT, "rules", "monthly_event_rules.json")
        with open(path) as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_ontology_source_ids_in_registry(self):
        """ontology 的 source_ids 能在 source_registry.json 找到。"""
        reg_path = os.path.join(ROOT, "rules", "source_registry.json")
        ont_path = os.path.join(ROOT, "rules", "monthly_event_ontology.json")
        with open(reg_path) as f:
            registry = json.load(f)
        with open(ont_path) as f:
            ontology = json.load(f)
        registry_keys = set(registry.keys())
        for et, entry in ontology.items():
            for sid in entry.get("source_ids", []):
                self.assertIn(sid, registry_keys, f"{et} 的 source_id {sid} 不在 registry")

    def test_evidence_chain_in_top_events(self):
        """Top 事件有证据链（trigger_count >= 2）。"""
        from core.monthly_engine import analyze_monthly_fortune
        from core.monthly_event_inference_engine import infer_monthly_likely_events_enhanced
        chart = {
            "day_master": "甲",
            "pillars": {"year": {"gan": "甲", "zhi": "子"}, "month": {"gan": "丙", "zhi": "寅"}, "day": {"gan": "甲", "zhi": "午"}, "hour": {"gan": "庚", "zhi": "申"}},
            "day_master_strength": {"strength": "偏弱", "favorable_elements": ["水", "木"], "unfavorable_elements": ["火", "金"]},
            "ten_god_counts": {"正财": 1, "偏财": 2, "正官": 1, "比肩": 1, "劫财": 1, "食神": 1, "伤官": 1, "正印": 1, "偏印": 0},
            "five_elements": {"木": 8, "火": 5, "土": 3, "金": 4, "水": 6},
        }
        monthly_data = analyze_monthly_fortune(chart, 2026)
        for item in monthly_data:
            result = infer_monthly_likely_events_enhanced(chart, item)
            for e in result.get("top_events", []):
                self.assertGreaterEqual(e.get("trigger_count", 0), 2,
                    f"{e.get('label','')} 证据链不足")


if __name__ == "__main__":
    unittest.main()
