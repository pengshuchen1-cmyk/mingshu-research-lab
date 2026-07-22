"""低频事件精准性测试 — v1.0.3-D-Fix"""
import unittest
from core.monthly_engine import analyze_monthly_fortune
from core.monthly_event_activation_bridge import infer_monthly_likely_events_full

class TestLowFrequencyEventPrecision(unittest.TestCase):
    def setUp(self):
        self.chart = {
            "day_master": "甲",
            "pillars": {"year":{"gan":"甲","zhi":"子"},"month":{"gan":"丙","zhi":"寅"},"day":{"gan":"甲","zhi":"午"},"hour":{"gan":"庚","zhi":"申"}},
            "day_master_strength": {"strength":"偏弱","favorable_elements":["水","木"],"unfavorable_elements":["火","金"]},
            "ten_god_counts": {"正财":1,"偏财":2,"正官":1,"比肩":1,"劫财":1,"食神":1,"伤官":1,"正印":1,"偏印":0},
            "five_elements": {"木":8,"火":5,"土":3,"金":4,"水":6},
        }
        self.monthly_data = analyze_monthly_fortune(self.chart, 2026)
        self.results = []
        for item in self.monthly_data:
            self.results.append(infer_monthly_likely_events_full(self.chart, item))

    def test_health_max_one_per_month(self):
        for i, r in enumerate(self.results):
            health_count = sum(1 for e in r.get("top_events",[])
                              if e.get("category")=="健康身体")
            self.assertLessEqual(health_count, 1,
                f"月{i+1}: 健康类事件 {health_count} > 1")

    def test_traffic_max_one_per_month(self):
        for i, r in enumerate(self.results):
            traffic_count = sum(1 for e in r.get("top_events",[])
                               if e.get("category")=="交通车辆")
            self.assertLessEqual(traffic_count, 1,
                f"月{i+1}: 交通类事件 {traffic_count} > 1")

    def test_low_freq_not_flooding(self):
        all_events = []
        for r in self.results:
            for e in r.get("top_events",[]):
                all_events.append(e.get("event_type",""))
        low_freq = ["safety_attention","legal_compliance","wealth_outflow",
                    "overwork","cooperation_money"]
        for lf in low_freq:
            count = all_events.count(lf)
            self.assertLessEqual(count, 5,
                f"低频事件{lf} 出现{count}/12月 > 5")

    def test_top_3_category_diversity(self):
        for i, r in enumerate(self.results):
            top3 = r.get("top_events", [])[:3]
            cats = [e.get("category","") for e in top3 if e.get("category")]
            if len(set(cats)) == 1 and len(cats) >= 2:
                self.fail(f"月{i+1}: Top 3 全部同一分类 {cats[0]}")

    def test_each_event_has_trigger_count(self):
        for r in self.results:
            for e in r.get("top_events",[]):
                tc = e.get("trigger_count", 0) or e.get("score", 0)
                self.assertGreaterEqual(tc, 1, f"{e.get('event_type')} 无有效trigger_count")

if __name__ == "__main__":
    unittest.main()
