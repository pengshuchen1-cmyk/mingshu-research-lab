"""命盘总体结论差异化测试 - v1.1-A2。"""

import json
import os
import sys
import unittest
from difflib import SequenceMatcher

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

FORBIDDEN_PATTERNS = [
    "必定", "绝对", "注定", "一定发财", "一定没钱", "一定贫穷",
    "必定离婚", "必定长寿", "寿命短", "活不长", "必有大病", "一定有灾",
    "必定婚姻不好", "无法改变",
]

SOURCE_REGISTRY_PATH = os.path.join(APP_DIR, "rules", "source_registry.json")


def _make_chart(day_master: str, year_g: str, year_z: str, month_g: str, month_z: str,
                day_g: str, day_z: str, hour_g: str, hour_z: str,
                gender: str = "男",
                five_elem=None, ten_god_c=None, strength_info=None) -> dict:
    """创建测试用 chart 字典。"""
    counts = ten_god_c or {"正财": 1, "偏财": 1, "食神": 1, "伤官": 0,
                           "正官": 1, "七杀": 0, "正印": 1, "偏印": 0,
                           "比肩": 2, "劫财": 1}
    fe = five_elem or {"木": 2, "火": 2, "土": 2, "金": 2, "水": 2}
    st_info = strength_info or {
        "strength": "中和", "net_score": 0,
        "favorable_elements": ["金", "水"],
        "unfavorable_elements": ["木", "火"],
    }
    return {
        "day_master": day_master,
        "pillars": {
            "year": {"gan": year_g, "zhi": year_z, "pillar": f"{year_g}{year_z}", "name": "年柱"},
            "month": {"gan": month_g, "zhi": month_z, "pillar": f"{month_g}{month_z}", "name": "月柱"},
            "day": {"gan": day_g, "zhi": day_z, "pillar": f"{day_g}{day_z}", "name": "日柱"},
            "hour": {"gan": hour_g, "zhi": hour_z, "pillar": f"{hour_g}{hour_z}", "name": "时柱"},
        },
        "ten_god_counts": counts,
        "ten_gods": {
            "year": {"gan": "比肩" if year_g == day_master else "正财"},
            "month": {"gan": "食神" if day_master in ("丙", "丁") else "正官"},
            "day": {"gan": day_master},
            "hour": {"gan": "正财" if day_master in ("甲", "乙") else "正印"},
        },
        "five_elements": fe,
        "day_master_strength": st_info,
        "profile": {"gender": gender},
        "hidden_stems": {
            "year": [{"gan": "癸", "ten_god": "正印"}],
            "month": [{"gan": "丙", "ten_god": "食神"}],
            "day": [{"gan": "丁", "ten_god": "伤官"}],
            "hour": [{"gan": "戊", "ten_god": "偏财"}],
        },
    }


CHARTS = [
    _make_chart("甲", "甲", "子", "丙", "寅", "甲", "午", "戊", "辰",
                gender="男",
                five_elem={"木": 3, "火": 3, "土": 2, "金": 0.5, "水": 1.5},
                ten_god_c={"正财": 2, "偏财": 1, "食神": 2, "伤官": 1,
                           "正官": 1, "七杀": 0, "正印": 1, "偏印": 0,
                           "比肩": 1, "劫财": 1},
                strength_info={"strength": "身强", "net_score": 12,
                               "favorable_elements": ["金", "土"],
                               "unfavorable_elements": ["木", "水"]}),
    _make_chart("丙", "丙", "午", "甲", "午", "丙", "子", "戊", "子",
                gender="女", five_elem={"火": 4, "木": 2, "土": 1.5, "金": 1, "水": 1.5},
                ten_god_c={"正财": 0, "偏财": 1, "食神": 2, "伤官": 1,
                           "正官": 2, "七杀": 1, "正印": 1, "偏印": 0,
                           "比肩": 0, "劫财": 0},
                strength_info={"strength": "身强", "net_score": 18,
                               "favorable_elements": ["金", "水"],
                               "unfavorable_elements": ["木", "火"]}),
    _make_chart("庚", "庚", "申", "甲", "申", "庚", "午", "丙", "戌",
                gender="男",
                five_elem={"金": 4, "木": 1.5, "火": 1.5, "土": 2, "水": 1},
                ten_god_c={"正财": 1, "偏财": 1, "食神": 0, "伤官": 1,
                           "正官": 1, "七杀": 2, "正印": 1, "偏印": 1,
                           "比肩": 0, "劫财": 0},
                strength_info={"strength": "身强", "net_score": 15,
                               "favorable_elements": ["水", "木"],
                               "unfavorable_elements": ["土", "金"]}),
    _make_chart("癸", "癸", "亥", "乙", "卯", "癸", "酉", "辛", "酉",
                gender="女", five_elem={"水": 3, "木": 2, "金": 3, "火": 1, "土": 1},
                ten_god_c={"正财": 1, "偏财": 0, "食神": 0, "伤官": 1,
                           "正官": 0, "七杀": 0, "正印": 2, "偏印": 1,
                           "比肩": 2, "劫财": 1},
                strength_info={"strength": "中和", "net_score": 5,
                               "favorable_elements": ["火", "土"],
                               "unfavorable_elements": ["金", "水"]}),
    _make_chart("戊", "戊", "辰", "丙", "辰", "戊", "戌", "壬", "子",
                gender="男",
                five_elem={"土": 5, "火": 2, "木": 1, "金": 0.5, "水": 1.5},
                ten_god_c={"正财": 1, "偏财": 1, "食神": 0, "伤官": 0,
                           "正官": 0, "七杀": 0, "正印": 2, "偏印": 1,
                           "比肩": 2, "劫财": 1},
                strength_info={"strength": "身强", "net_score": 22,
                               "favorable_elements": ["金", "水"],
                               "unfavorable_elements": ["火", "木"]}),
]


class LifeOverviewDiffTests(unittest.TestCase):
    """命盘总体结论差异化测试。"""

    def setUp(self):
        from core.life_overview_engine import analyze_life_overview
        self.results = {}
        for i, chart in enumerate(CHARTS):
            try:
                self.results[i] = analyze_life_overview(chart)
            except Exception as e:
                self.results[i] = {"error": str(e)}

    def test_all_charts_generate_overview(self):
        """至少生成 5 个不同命盘的 life_overview。"""
        self.assertEqual(len(CHARTS), 5)
        for i, r in self.results.items():
            self.assertNotIn("error", r, f"Chart {i} failed: {r.get('error', '')}")

    def test_all_have_required_keys(self):
        """每个 life_overview 包含 wealth/romance/health/career/evidence/source_ids。"""
        for i, r in self.results.items():
            with self.subTest(chart=i):
                self.assertIn("wealth_overview", r, f"Chart {i} missing wealth_overview")
                self.assertIn("romance_overview", r, f"Chart {i} missing romance_overview")
                self.assertIn("health_overview", r, f"Chart {i} missing health_overview")
                self.assertIn("career_overview", r, f"Chart {i} missing career_overview")
                self.assertIn("evidence", r, f"Chart {i} missing evidence")
                self.assertIn("source_ids", r, f"Chart {i} missing source_ids")
                self.assertGreater(len(r["evidence"]), 0, f"Chart {i} has empty evidence")
                self.assertGreater(len(r["source_ids"]), 0, f"Chart {i} has empty source_ids")

    def test_health_has_disclaimer(self):
        """健康总览必须包含 medical_disclaimer。"""
        for i, r in self.results.items():
            with self.subTest(chart=i):
                health = r.get("health_overview", {})
                disclaimer = health.get("medical_disclaimer", "")
                self.assertTrue(
                    len(disclaimer) > 10 and "不构成医学诊断" in disclaimer,
                    f"Chart {i} missing or invalid disclaimer: {disclaimer[:30]}"
                )

    def test_no_forbidden_words(self):
        """不得出现禁用词。"""
        for i, r in self.results.items():
            text = str(r)
            for word in FORBIDDEN_PATTERNS:
                self.assertNotIn(word, text, f"Chart {i} contains forbidden: '{word}'")

    def test_wealth_diversity(self):
        """不同命盘的财富总览不能全部相同。"""
        summaries = set()
        for r in self.results.values():
            w = r.get("wealth_overview", {})
            s = w.get("wealth_summary", "")
            summaries.add(s[:40])
        self.assertGreater(len(summaries), 1, "Wealth summaries are too similar across charts")

    def test_romance_diversity(self):
        """不同命盘的桃花感情总览不能全部相同。"""
        summaries = set()
        for r in self.results.values():
            rm = r.get("romance_overview", {})
            s = rm.get("romance_summary", "")
            summaries.add(s[:40])
        self.assertGreater(len(summaries), 1, "Romance summaries are too similar across charts")

    def test_health_diversity(self):
        """不同命盘的健康总览不能全部相同。"""
        summaries = set()
        for r in self.results.values():
            h = r.get("health_overview", {})
            s = h.get("health_summary", "")
            summaries.add(s[:40])
        self.assertGreater(len(summaries), 1, "Health summaries are too similar across charts")

    def test_career_diversity(self):
        """不同命盘的事业总览不能全部相同。"""
        types_set = set()
        for r in self.results.values():
            c = r.get("career_overview", {})
            t = c.get("career_type", "")
            types_set.add(t)
        self.assertGreater(len(types_set), 1, "Career types are too similar across charts")

    def test_similarity_lower_than_threshold(self):
        """不同命盘 life_overview 相似度不得过高。"""
        summaries = []
        for r in self.results.values():
            s = (
                r.get("wealth_overview", {}).get("wealth_summary", "")
                + r.get("romance_overview", {}).get("romance_summary", "")
                + r.get("health_overview", {}).get("health_summary", "")
            )
            summaries.append(s)

        similarities = []
        for i in range(len(summaries)):
            for j in range(i + 1, len(summaries)):
                sim = SequenceMatcher(None, summaries[i], summaries[j]).ratio()
                similarities.append(sim)

        if similarities:
            max_sim = max(similarities)
            self.assertLess(max_sim, 0.85,
                            f"Cross-chart similarity too high: {max_sim:.3f}")

    def test_scores_present(self):
        """必须包含 scores 字典。"""
        for i, r in self.results.items():
            with self.subTest(chart=i):
                scores = r.get("scores", {})
                self.assertIn("wealth", scores)
                self.assertIn("romance", scores)
                self.assertIn("health_stability", scores)
                self.assertIn("career", scores)
                self.assertIn("overall_balance", scores)

    def test_all_source_ids_in_registry(self):
        """source_ids 必须在 source_registry.json 中有对应条目。"""
        with open(SOURCE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)
        for i, r in self.results.items():
            for sid in r.get("source_ids", []):
                self.assertIn(sid, registry, f"Chart {i} has unknown source_id: {sid}")


if __name__ == "__main__":
    unittest.main()
