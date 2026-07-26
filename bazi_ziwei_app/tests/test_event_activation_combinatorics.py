"""Event activation combinatorics coverage tests."""

from __future__ import annotations

import itertools
import math
import unittest


TEN_GOD_GROUPS = {
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "officer",
    "七杀": "officer",
    "食神": "output",
    "伤官": "output",
    "正印": "resource",
    "偏印": "resource",
    "比肩": "peer",
    "劫财": "peer",
}


def _base_context() -> dict:
    return {
        "month_gan": "戊",
        "month_zhi": "辰",
        "month_pillar": "戊辰",
        "month_index": 1,
        "target_year": 2026,
        "month_element": "土",
        "month_zhi_element": "土",
        "month_ten_god": "正财",
        "month_ten_god_group": "wealth",
        "is_wealth_month": True,
        "is_officer_month": True,
        "is_output_month": True,
        "is_resource_month": True,
        "is_peer_month": True,
        "favorable_relation": "喜用相关",
        "favorable_elements": ["木", "火", "土", "金", "水"],
        "unfavorable_elements": ["木", "火", "土", "金", "水"],
        "clash_year_branch": True,
        "clash_month_branch": True,
        "clash_day_branch": True,
        "clash_hour_branch": True,
        "clash_any": True,
        "activate_wealth_star": True,
        "activate_officer_star": True,
        "activate_output_star": True,
        "activate_resource_star": True,
        "activate_peer_star": True,
        "activate_spouse_palace": True,
        "activate_peach_blossom": True,
        "ten_god_counts": {
            "正财": 3,
            "偏财": 3,
            "正官": 3,
            "七杀": 3,
            "食神": 3,
            "伤官": 3,
            "正印": 3,
            "偏印": 3,
            "比肩": 3,
            "劫财": 3,
        },
        "group_counts": {
            "wealth": 6,
            "officer": 6,
            "output": 6,
            "resource": 6,
            "peer": 6,
        },
        "gender": "女",
        "day_master": "甲",
        "day_master_element": "木",
        "chart_pillars_year_month_day_hour": ["甲子", "丙寅", "甲午", "庚申"],
        "year_ten_god": "正官",
        "year_element": "金",
        "overstrong_elements": ["木", "火", "土", "金", "水"],
        "weak_elements": ["木", "火", "土", "金", "水"],
    }


def _first_value(condition: dict):
    value = condition.get("value", [])
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _context_for_rule(rule: dict) -> dict:
    ctx = _base_context()
    for condition in rule.get("trigger_conditions", []):
        ctype = condition.get("type", "")
        first = _first_value(condition)
        values = condition.get("value", [])
        if not isinstance(values, list):
            values = [values]

        if ctype == "ten_god" and first:
            ctx["month_ten_god"] = first
            ctx["month_ten_god_group"] = TEN_GOD_GROUPS.get(first, ctx["month_ten_god_group"])
        elif ctype == "ten_god_group" and first:
            ctx["month_ten_god_group"] = first
        elif ctype == "favorable_relation" and first:
            ctx["favorable_relation"] = first
        elif ctype == "month_index" and first is not None:
            ctx["month_index"] = int(first)
        elif ctype in {"element", "element_in"} and first:
            ctx["month_element"] = first
            ctx["month_zhi_element"] = first
        elif ctype == "branch_in" and first:
            ctx["month_zhi"] = first
        elif ctype == "group_count_at_least":
            for item in values:
                if isinstance(item, dict):
                    group = item.get("group")
                    if group:
                        ctx["group_counts"][group] = max(
                            float(ctx["group_counts"].get(group, 0)),
                            float(item.get("min", 0) or 0),
                        )
        elif ctype == "element_strength":
            if "overstrong" in values:
                ctx["overstrong_elements"] = list({*ctx["overstrong_elements"], ctx["month_element"]})
            if "weak" in values:
                ctx["weak_elements"] = list({*ctx["weak_elements"], ctx["month_zhi_element"]})
        elif ctype == "day_master_element" and first:
            ctx["day_master_element"] = first
        elif ctype == "gender" and first:
            ctx["gender"] = first
    return ctx


class TestEventActivationCombinatorics(unittest.TestCase):
    def test_current_event_pool_combination_counts_are_known(self):
        from core.monthly_event_activation_bridge import load_activation_assets

        event_count = len(load_activation_assets()["ontology"])
        self.assertEqual(event_count, 262)
        self.assertEqual(math.comb(event_count, 2), 34191)
        self.assertEqual(math.comb(event_count, 3), 2963220)
        self.assertEqual(event_count * (event_count - 1) * (event_count - 2), 17779320)

    def test_every_event_type_has_a_generated_context_that_activates_it(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets

        assets = load_activation_assets()
        ontology = assets["ontology"]
        rules_by_event = {rule["target_event_type"]: rule for rule in assets["trigger_rules"]}

        missing_rules = sorted(set(ontology) - set(rules_by_event))
        self.assertEqual([], missing_rules)

        unreachable = []
        for event_type in sorted(ontology):
            rule = rules_by_event[event_type]
            ctx = _context_for_rule(rule)
            candidates = activate_events_by_rules(ctx, assets)
            activated = {candidate["event_type"]: candidate for candidate in candidates}
            if event_type not in activated:
                unreachable.append(event_type)
                continue
            candidate = activated[event_type]
            self.assertGreaterEqual(
                candidate["trigger_count"],
                int(rule.get("min_trigger_count", 2) or 2),
                event_type,
            )
            self.assertGreaterEqual(len(candidate.get("evidence", [])), 2, event_type)
            self.assertGreater(len(candidate.get("source_ids", [])), 0, event_type)

        self.assertEqual([], unreachable)

    def test_reachable_events_can_cover_any_requested_example_count(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets

        assets = load_activation_assets()
        rules_by_event = {rule["target_event_type"]: rule for rule in assets["trigger_rules"]}
        event_types = sorted(assets["ontology"])

        for requested_count in [1, 2, 5, 24, len(event_types)]:
            target_events = event_types[:requested_count]
            covered = set()
            for event_type in target_events:
                candidates = activate_events_by_rules(_context_for_rule(rules_by_event[event_type]), assets)
                covered.update(candidate["event_type"] for candidate in candidates)
            self.assertTrue(set(target_events).issubset(covered), requested_count)

        for left, right in itertools.combinations(event_types[:24], 2):
            self.assertIn(left, rules_by_event)
            self.assertIn(right, rules_by_event)
