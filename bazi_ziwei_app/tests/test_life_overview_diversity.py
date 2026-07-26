"""v1.0.4 命局总论类型差异化测试。"""

from __future__ import annotations

import json
import os
import sys
import unittest
from difflib import SequenceMatcher


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


PROFILES = [
    {"name": "男命样例", "gender": "男", "birth_date": "1990-01-01", "birth_hour": 10, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "女命样例", "gender": "女", "birth_date": "1992-12-26", "birth_hour": 0, "birth_minute": 0, "birth_place": "北京", "use_solar_time": False},
    {"name": "身强样例", "gender": "男", "birth_date": "1997-07-16", "birth_hour": 9, "birth_minute": 0, "birth_place": "广州", "use_solar_time": False},
    {"name": "身弱样例", "gender": "女", "birth_date": "1988-07-26", "birth_hour": 12, "birth_minute": 0, "birth_place": "成都", "use_solar_time": False},
    {"name": "喜忌差异样例", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False},
]


BROAD_DIVERSITY_PROFILES = [
    {"name": "批量样例01", "gender": "男", "birth_date": "1984-02-29", "birth_hour": 1, "birth_minute": 0, "birth_place": "上海", "use_solar_time": False},
    {"name": "批量样例02", "gender": "女", "birth_date": "1986-06-18", "birth_hour": 3, "birth_minute": 20, "birth_place": "北京", "use_solar_time": False},
    {"name": "批量样例03", "gender": "男", "birth_date": "1988-11-07", "birth_hour": 5, "birth_minute": 40, "birth_place": "成都", "use_solar_time": False},
    {"name": "批量样例04", "gender": "女", "birth_date": "1990-01-23", "birth_hour": 7, "birth_minute": 10, "birth_place": "杭州", "use_solar_time": False},
    {"name": "批量样例05", "gender": "男", "birth_date": "1992-04-15", "birth_hour": 9, "birth_minute": 30, "birth_place": "广州", "use_solar_time": False},
    {"name": "批量样例06", "gender": "女", "birth_date": "1994-09-09", "birth_hour": 11, "birth_minute": 50, "birth_place": "深圳", "use_solar_time": False},
    {"name": "批量样例07", "gender": "男", "birth_date": "1996-08-28", "birth_hour": 16, "birth_minute": 0, "birth_place": "昆明", "use_solar_time": False},
    {"name": "批量样例08", "gender": "女", "birth_date": "1997-07-17", "birth_hour": 9, "birth_minute": 20, "birth_place": "昆明", "use_solar_time": False},
    {"name": "批量样例09", "gender": "男", "birth_date": "1998-12-31", "birth_hour": 23, "birth_minute": 10, "birth_place": "南京", "use_solar_time": False},
    {"name": "批量样例10", "gender": "女", "birth_date": "2000-08-10", "birth_hour": 16, "birth_minute": 20, "birth_place": "西安", "use_solar_time": False},
    {"name": "批量样例11", "gender": "男", "birth_date": "2002-03-05", "birth_hour": 14, "birth_minute": 45, "birth_place": "武汉", "use_solar_time": False},
    {"name": "批量样例12", "gender": "女", "birth_date": "2004-10-21", "birth_hour": 18, "birth_minute": 5, "birth_place": "厦门", "use_solar_time": False},
]


class LifeOverviewDiversityV104Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from core.bazi_engine import build_bazi_chart
        from core.life_overview_engine import analyze_life_overview

        cls.results = [analyze_life_overview(build_bazi_chart(profile)) for profile in PROFILES]

    def test_archetype_pool_has_required_types(self):
        with open(os.path.join(ROOT, "rules", "life_overview_event_pool.json"), encoding="utf-8") as f:
            pool = json.load(f)
        self.assertGreaterEqual(len(pool["wealth"]), 8)
        self.assertGreaterEqual(len(pool["romance"]), 8)
        self.assertGreaterEqual(len(pool["health"]), 8)
        self.assertGreaterEqual(len(pool["career"]), 8)

    def test_overview_types_are_not_all_same(self):
        wealth_types = {r["wealth_overview"]["wealth_type"] for r in self.results}
        romance_types = {r["romance_overview"]["romance_type"] for r in self.results}
        health_types = {r["health_overview"].get("health_type", "") for r in self.results}
        career_types = {r["career_overview"]["career_type"] for r in self.results}
        self.assertGreaterEqual(len(wealth_types), 3)
        self.assertGreaterEqual(len(romance_types), 3)
        self.assertGreaterEqual(len(health_types), 3)
        self.assertGreaterEqual(len(career_types), 3)

    def test_cross_chart_overview_similarity_is_controlled(self):
        texts = []
        signals = []
        for item in self.results:
            texts.append("\n".join([
                item["wealth_overview"]["wealth_summary"],
                item["romance_overview"]["romance_summary"],
                item["health_overview"]["health_summary"],
                item["career_overview"]["career_summary"],
                "；".join(item.get("evidence", [])),
            ]))
            signals.append("|".join([
                item["wealth_overview"]["wealth_type"],
                item["romance_overview"]["romance_type"],
                item["health_overview"].get("health_type", ""),
                item["career_overview"]["career_type"],
                str(item.get("scores", {})),
            ]))
        max_similarity = 0
        max_signal_overlap = 0
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                max_similarity = max(max_similarity, SequenceMatcher(None, texts[i], texts[j]).ratio())
                left = {x for x in signals[i].split("|") if x}
                right = {x for x in signals[j].split("|") if x}
                max_signal_overlap = max(max_signal_overlap, len(left & right) / max(1, len(left | right)))
        self.assertLessEqual(max_similarity, 0.78)
        self.assertLessEqual(max_signal_overlap, 0.55)

    def test_reference_case_visible_summaries_are_personalized(self):
        from core.bazi_engine import build_bazi_chart
        from core.life_overview_engine import analyze_life_overview

        with open(
            os.path.join(ROOT, "tests", "fixtures", "bazi_reference_cases.json"),
            encoding="utf-8",
        ) as f:
            cases = json.load(f)["cases"]

        visible = {"wealth": set(), "romance": set(), "health": set()}
        for case in cases:
            profile = dict(case["profile"])
            profile["use_solar_time"] = False
            if profile.get("birth_minute") is None:
                profile["birth_minute"] = 0
            overview = analyze_life_overview(build_bazi_chart(profile))
            visible["wealth"].add(overview["wealth_overview"]["wealth_summary"][:48])
            visible["romance"].add(overview["romance_overview"]["romance_summary"][:48])
            visible["health"].add(overview["health_overview"]["health_summary"][:48])

        for dimension, snippets in visible.items():
            self.assertEqual(
                len(snippets),
                len(cases),
                f"{dimension} visible summaries are duplicated: {snippets}",
            )

    def test_broad_different_charts_have_different_visible_summaries(self):
        from core.bazi_engine import build_bazi_chart
        from core.life_overview_engine import analyze_life_overview

        seen_signatures = set()
        visible = {"wealth": {}, "health": {}}
        romance_by_signature = {}
        for profile in BROAD_DIVERSITY_PROFILES:
            chart = build_bazi_chart(profile)
            signature = " ".join(chart["pillars"][pos]["pillar"] for pos in ("year", "month", "day", "hour"))
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            overview = analyze_life_overview(chart)
            visible["wealth"][signature] = overview["wealth_overview"]["wealth_summary"][:64]
            visible["health"][signature] = overview["health_overview"]["health_summary"][:64]
            romance = overview["romance_overview"]
            relationship_signature = json.dumps(
                romance["relationship_signature"], ensure_ascii=False, sort_keys=True
            )
            visible_conclusion = (
                romance["core_portrait"],
                romance["primary_relationship_focus"],
            )
            if relationship_signature in romance_by_signature:
                self.assertEqual(
                    romance_by_signature[relationship_signature],
                    visible_conclusion,
                    "相同关系事实签名应允许复用同一结论",
                )
            romance_by_signature[relationship_signature] = visible_conclusion

        self.assertGreaterEqual(len(seen_signatures), 10)
        for dimension, snippets_by_signature in visible.items():
            snippets = list(snippets_by_signature.values())
            self.assertEqual(
                len(set(snippets)),
                len(snippets),
                f"{dimension} summaries must differ for different charts: {snippets_by_signature}",
            )
        self.assertGreaterEqual(len(romance_by_signature), 4)
        self.assertGreaterEqual(len(set(romance_by_signature.values())), 3)

    def test_same_scores_but_different_pillars_still_have_different_visible_summaries(self):
        from core.life_overview_engine import analyze_life_overview

        def chart(pillars: dict) -> dict:
            return {
                "day_master": "甲",
                "pillars": {
                    key: {"gan": value[0], "zhi": value[1], "pillar": value}
                    for key, value in pillars.items()
                },
                "ten_god_counts": {
                    "正财": 2, "偏财": 1, "食神": 2, "伤官": 1,
                    "正官": 1, "七杀": 0, "正印": 1, "偏印": 0,
                    "比肩": 1, "劫财": 1,
                },
                "five_elements": {"木": 3, "火": 3, "土": 2, "金": 0.5, "水": 1.5},
                "day_master_strength": {
                    "strength": "身强",
                    "net_score": 12,
                    "favorable_elements": ["金", "土"],
                    "unfavorable_elements": ["木", "水"],
                },
                "profile": {"gender": "男"},
                "hidden_stems": {
                    "year": [{"gan": "癸", "ten_god": "正印"}],
                    "month": [{"gan": "丙", "ten_god": "食神"}],
                    "day": [{"gan": "丁", "ten_god": "伤官"}],
                    "hour": [{"gan": "戊", "ten_god": "偏财"}],
                },
            }

        left = analyze_life_overview(chart({"year": "甲子", "month": "丙寅", "day": "甲午", "hour": "戊辰"}))
        right = analyze_life_overview(chart({"year": "乙丑", "month": "丁卯", "day": "甲午", "hour": "己巳"}))

        for dimension, key in [("wealth", "wealth_summary"), ("romance", "romance_summary"), ("health", "health_summary")]:
            left_text = left[f"{dimension}_overview"][key][:64]
            right_text = right[f"{dimension}_overview"][key][:64]
            self.assertNotEqual(left_text, right_text, f"{dimension} visible summary ignored pillar differences")


if __name__ == "__main__":
    unittest.main()
