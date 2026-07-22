"""Focused tests for finance-income event trigger differentiation."""

from __future__ import annotations

import difflib
import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TARGET_EVENTS = {
    "client_payment": ["回款", "尾款", "账期", "合作方"],
    "sales_conversion": ["成交", "报价", "询盘", "客户"],
    "salary_bonus": ["奖金", "考核", "上级", "组织"],
    "commission_income": ["提成", "销售", "分成", "业绩"],
    "side_income": ["副业", "技能", "业余", "额外"],
    "business_cash_in": ["经营", "现金流", "门店", "周转"],
}


def _load_json(name: str):
    with (ROOT / "rules" / name).open(encoding="utf-8") as f:
        return json.load(f)


def _rule_for(event_type: str, rules: list[dict]) -> dict:
    for rule in rules:
        if rule.get("target_event_type") == event_type:
            return rule
    raise AssertionError(f"缺少触发规则: {event_type}")


def _condition_signature(rule: dict) -> str:
    parts = []
    for condition in rule.get("trigger_conditions", []):
        value = condition.get("value", "")
        if isinstance(value, list):
            value_text = ",".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value)
        else:
            value_text = str(value)
        parts.append(f"{condition.get('type')}={value_text}")
    return " | ".join(sorted(parts))


class FinanceIncomeTriggerDifferentiationTests(unittest.TestCase):
    def setUp(self):
        self.ontology = _load_json("monthly_event_ontology.json")
        self.rules = _load_json("monthly_event_trigger_rules.json")

    def test_income_events_have_distinct_trigger_signatures(self):
        signatures = {
            event_type: _condition_signature(_rule_for(event_type, self.rules))
            for event_type in TARGET_EVENTS
        }
        for left, left_sig in signatures.items():
            for right, right_sig in signatures.items():
                if left >= right:
                    continue
                similarity = difflib.SequenceMatcher(None, left_sig, right_sig).ratio()
                self.assertLess(
                    similarity,
                    0.88,
                    f"{left} 与 {right} 的触发链仍然过像: {similarity:.3f}\n{left_sig}\n---\n{right_sig}",
                )

    def test_each_income_event_has_user_visible_real_world_scene(self):
        for event_type, keywords in TARGET_EVENTS.items():
            item = self.ontology[event_type]
            text = json.dumps(
                {
                    "structure_basis": item.get("structure_basis", {}),
                    "modern_mapping": item.get("modern_mapping", {}),
                    "user_visible_basis": item.get("user_visible_basis", ""),
                    "subtype_rules": item.get("subtype_rules", {}),
                },
                ensure_ascii=False,
            )
            self.assertTrue(
                any(keyword in text for keyword in keywords),
                f"{event_type} 缺少现实场景关键词: {keywords}",
            )

    def test_income_events_use_different_structural_anchors(self):
        expected_anchor_types = {
            "client_payment": {"is_wealth_month", "clash_day_branch", "element"},
            "sales_conversion": {"is_output_month", "activate_peach_blossom", "branch_in"},
            "salary_bonus": {"is_officer_month", "is_resource_month", "clash_month_branch"},
            "commission_income": {"is_output_month", "group_count_at_least", "month_index"},
            "side_income": {"is_output_month", "clash_hour_branch", "day_master_element"},
            "business_cash_in": {"is_wealth_month", "clash_month_branch", "branch_in"},
        }
        for event_type, expected in expected_anchor_types.items():
            rule = _rule_for(event_type, self.rules)
            condition_types = {condition.get("type") for condition in rule.get("trigger_conditions", [])}
            self.assertTrue(expected <= condition_types, f"{event_type} 缺少专属锚点: {expected - condition_types}")


if __name__ == "__main__":
    unittest.main()
