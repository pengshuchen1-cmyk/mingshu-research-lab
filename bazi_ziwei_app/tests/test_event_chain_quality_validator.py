"""Event evidence-chain quality gate tests.

These tests keep future event-pool expansion from becoming plain event names
and repeated copy. The validator is intentionally independent from Streamlit.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class EventChainQualityValidatorTests(unittest.TestCase):
    def test_current_event_chain_pool_passes_basic_quality_gate(self):
        from tools.validate_event_chain_quality import (
            format_quality_report,
            validate_event_chain_quality,
        )

        report = validate_event_chain_quality(ROOT)

        self.assertGreaterEqual(report["total_event_count"], 120)
        self.assertGreaterEqual(report["chain_event_count"], 80)
        self.assertTrue(report["basic_passed"], report["priority_fix_events"][:10])
        self.assertEqual([], report["missing_field_events"])
        self.assertEqual([], report["source_ids_missing_events"])
        self.assertGreater(report["passed_count"], 0)

        text = format_quality_report(report)
        for label in [
            "总事件数",
            "证据链事件数",
            "完整通过数量",
            "缺字段事件列表",
            "trigger_rules 过弱事件列表",
            "不允许进入 Top 事件的事件列表",
            "建议优先修复的事件列表",
        ]:
            self.assertIn(label, text)

    def test_validator_detects_incomplete_chain_event(self):
        from tools.validate_event_chain_quality import validate_event_chain_quality

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules_dir = root / "rules"
            rules_dir.mkdir()

            ontology = {
                "thin_event": {
                    "event_type": "thin_event",
                    "label": "薄弱事件",
                    "category": "财务支出",
                    "description": "只有名字和文案，没有完整证据链。",
                    "traditional_basis": {"ten_god_basis": [], "source_ids": []},
                    "structure_basis": {"required_patterns": []},
                    "modern_mapping": {"positive_expression": [], "neutral_expression": [], "negative_expression": []},
                    "confidence_basis": {"high": "", "medium": "", "low": "", "downgrade_reasons": []},
                    "anti_triggers": [],
                    "user_visible_basis": "财星 官杀 冲克 喜用 忌神",
                    "required_evidence_count": 1,
                    "subtype_rules": {},
                    "source_ids": [],
                }
            }
            trigger_rules = [
                {
                    "rule_id": "thin_rule",
                    "target_event_type": "thin_event",
                    "trigger_conditions": [{"type": "category", "value": "财务"}],
                    "source_ids": [],
                    "basis": "",
                }
            ]
            variants = {"thin_event": [{"variant_id": "thin_1", "one_line": "泛化提醒。"}]}

            (rules_dir / "monthly_event_ontology.json").write_text(
                json.dumps(ontology, ensure_ascii=False),
                encoding="utf-8",
            )
            (rules_dir / "monthly_event_trigger_rules.json").write_text(
                json.dumps(trigger_rules, ensure_ascii=False),
                encoding="utf-8",
            )
            (rules_dir / "monthly_event_variants.json").write_text(
                json.dumps(variants, ensure_ascii=False),
                encoding="utf-8",
            )

            report = validate_event_chain_quality(root)

        self.assertFalse(report["basic_passed"])
        self.assertIn("thin_event", report["source_ids_missing_events"])
        self.assertIn("thin_event", report["not_allowed_top_events"])
        self.assertTrue(any(item["event_type"] == "thin_event" for item in report["weak_trigger_rule_events"]))
        self.assertTrue(any(item["event_type"] == "thin_event" for item in report["empty_field_events"]))


if __name__ == "__main__":
    unittest.main()
