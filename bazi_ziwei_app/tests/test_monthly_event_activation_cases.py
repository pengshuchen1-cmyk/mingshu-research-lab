"""低频事件专门触发样例测试 — v1.0.3-D-Fix"""

from __future__ import annotations

import json, os, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "monthly_event_activation_cases.json")
BASE_CTX = {
    "month_ten_god": "正印", "month_element": "水", "month_zhi_element": "巳",
    "favorable_relation": "平稳观察",
    "is_wealth_month": False, "is_officer_month": False,
    "is_output_month": False, "is_resource_month": True, "is_peer_month": False,
    "clash_any": False, "clash_year_branch": False, "clash_month_branch": False,
    "clash_day_branch": False, "clash_hour_branch": False,
    "activate_wealth_star": False, "activate_officer_star": False,
    "activate_output_star": False, "activate_resource_star": True,
    "activate_peer_star": False, "activate_spouse_palace": False,
    "activate_peach_blossom": False,
    "year_ten_god": "", "year_element": "",
    "overstrong_elements": [], "weak_elements": [],
    "favorable_elements": ["水","木"], "unfavorable_elements": ["火","金"],
}


class TestMonthlyEventActivationCases(unittest.TestCase):

    def test_fixture_exists(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH))
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        self.assertIn("cases", data)
        self.assertGreater(len(data["cases"]), 0)

    def test_fixture_covers_9_events(self):
        targets = {"cooperation_money","digestion_issue","kidney_fatigue",
                   "legal_compliance","overwork","safety_attention",
                   "travel_traffic","vehicle_expense","wealth_outflow"}
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        found = {c["target_event_type"] for c in cases}
        missing = targets - found
        self.assertEqual(len(missing), 0, f"Missing cases: {missing}")

    def test_each_case_activates_target(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            et = case["target_event_type"]
            ctx = dict(BASE_CTX)
            ctx.update(case.get("context_overrides", {}))
            candidates = activate_events_by_rules(ctx, assets)
            activated = {c["event_type"] for c in candidates}
            self.assertIn(et, activated,
                f"{case['case_id']}: {et} 未在候选事件中 (ctx={case.get('context_overrides',{})})")

    def test_each_has_trigger_count_ge_2(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            et = case["target_event_type"]
            ctx = dict(BASE_CTX)
            ctx.update(case.get("context_overrides", {}))
            candidates = activate_events_by_rules(ctx, assets)
            cand = next((c for c in candidates if c["event_type"] == et), None)
            self.assertIsNotNone(cand, f"{et}: 未找到候选")
            self.assertGreaterEqual(cand["trigger_count"], case.get("expected_min_trigger_count", 2),
                f"{et}: trigger_count={cand['trigger_count']} < {case.get('expected_min_trigger_count', 2)}")

    def test_each_has_evidence(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            et = case["target_event_type"]
            ctx = dict(BASE_CTX)
            ctx.update(case.get("context_overrides", {}))
            candidates = activate_events_by_rules(ctx, assets)
            cand = next((c for c in candidates if c["event_type"] == et), None)
            self.assertIsNotNone(cand, f"{et}: 未找到候选")
            self.assertGreaterEqual(len(cand.get("evidence", [])), 2,
                f"{et}: evidence={len(cand.get('evidence',[]))} < 2")

    def test_each_has_source_ids(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            et = case["target_event_type"]
            ctx = dict(BASE_CTX)
            ctx.update(case.get("context_overrides", {}))
            candidates = activate_events_by_rules(ctx, assets)
            cand = next((c for c in candidates if c["event_type"] == et), None)
            self.assertIsNotNone(cand, f"{et}: 未找到候选")
            self.assertGreater(len(cand.get("source_ids", [])), 0,
                f"{et}: source_ids 为空")

    def test_no_forbidden_words_in_candidates(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        forbidden = ["必定","绝对","注定","一定发财","一定买房","必定破财",
                     "必有车祸","车祸","必有大病","大病","短命","必定离婚","有血光","灾祸"]
        with open(FIXTURE_PATH) as f:
            cases = json.load(f)["cases"]
        for case in cases:
            et = case["target_event_type"]
            ctx = dict(BASE_CTX)
            ctx.update(case.get("context_overrides", {}))
            candidates = activate_events_by_rules(ctx, assets)
            cand = next((c for c in candidates if c["event_type"] == et), None)
            if cand:
                text = str(cand)
                for w in forbidden:
                    self.assertNotIn(w, text, f"{et}: 包含禁用词 {w}")


if __name__ == "__main__":
    unittest.main()
