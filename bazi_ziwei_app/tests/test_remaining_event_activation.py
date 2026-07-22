"""流月事件激活覆盖测试 — v1.0.4"""
import json, os, unittest
from core.monthly_engine import analyze_monthly_fortune
from core.monthly_event_activation_bridge import infer_monthly_likely_events_full, load_activation_assets

class TestRemainingEventActivation(unittest.TestCase):
    def test_representative_events_can_activate(self):
        charts = [
            {"day_master":"甲","pillars":{"year":{"gan":"甲","zhi":"子"},"month":{"gan":"丙","zhi":"寅"},"day":{"gan":"甲","zhi":"午"},"hour":{"gan":"庚","zhi":"申"}},
             "day_master_strength":{"strength":"偏弱","favorable_elements":["水","木"],"unfavorable_elements":["火","金"]},
             "ten_god_counts":{"正财":1,"偏财":2,"正官":1,"比肩":1,"劫财":1,"食神":1,"伤官":1,"正印":1,"偏印":0},
             "five_elements":{"木":8,"火":5,"土":3,"金":4,"水":6}},
            {"day_master":"庚","pillars":{"year":{"gan":"庚","zhi":"申"},"month":{"gan":"辛","zhi":"巳"},"day":{"gan":"庚","zhi":"午"},"hour":{"gan":"甲","zhi":"戌"}},
             "day_master_strength":{"strength":"偏强","favorable_elements":["土","金"],"unfavorable_elements":["木","火"]},
             "ten_god_counts":{"正财":2,"偏财":1,"正官":1,"七杀":1,"比肩":2,"食神":1,"正印":1},
             "five_elements":{"木":2,"火":3,"土":8,"金":7,"水":2}},
        ]
        from core.monthly_event_inference_engine import EVENT_TYPES
        activated = set()
        for chart in charts:
            monthly_data = analyze_monthly_fortune(chart, 2026)
            for item in monthly_data:
                result = infer_monthly_likely_events_full(chart, item)
                for e in result.get("top_events",[]):
                    activated.add(e.get("event_type",""))
        representative = {
            "client_payment", "project_income", "wealth_outflow", "contract_document",
            "vehicle_safety", "property_housing", "social_drinking", "relationship_progress",
            "health_fluctuation", "nobleman_help", "rule_penalty", "study_exam",
        }
        self.assertTrue(representative & activated, "代表性事件未能进入 Top 事件")
        self.assertGreaterEqual(len(EVENT_TYPES), 120)

    def test_coverage_is_120_plus(self):
        from core.monthly_event_inference_engine import EVENT_TYPES
        self.assertGreaterEqual(len(EVENT_TYPES), 120)
        self.assertEqual(len([e for e in EVENT_TYPES if e]), len(EVENT_TYPES))

    def test_no_fixed_source_ids(self):
        from core.monthly_event_activation_bridge import activate_events_by_rules, load_activation_assets
        assets = load_activation_assets()
        chart = {"day_master":"甲","pillars":{"year":{"gan":"甲","zhi":"子"},"month":{"gan":"丙","zhi":"寅"},"day":{"gan":"甲","zhi":"午"},"hour":{"gan":"庚","zhi":"申"}},
                 "day_master_strength":{"strength":"偏弱","favorable_elements":["水","木"],"unfavorable_elements":["火","金"]},
                 "ten_god_counts":{"正财":1,"偏财":2,"正官":1,"比肩":1,"劫财":1,"食神":1,"伤官":1,"正印":1,"偏印":0},
                 "five_elements":{"木":8,"火":5,"土":3,"金":4,"水":6}}
        monthly_data = analyze_monthly_fortune(chart, 2026)
        from core.monthly_event_activation_bridge import build_month_context
        ctx = build_month_context(chart, monthly_data[0])
        candidates = activate_events_by_rules(ctx, assets)
        for c in candidates:
            sids = c.get("source_ids", [])
            self.assertGreater(len(sids), 0, f"{c.get('event_type')}: source_ids 为空")

if __name__ == "__main__":
    unittest.main()
