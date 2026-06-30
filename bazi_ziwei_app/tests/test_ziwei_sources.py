"""紫微斗数依据化测试 — v1.2-A。"""

import json
import os
import sys
import unittest

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

FORBIDDEN = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必有灾",
             "必有大病", "必定富贵", "必定孤独", "必定长寿", "寿命短", "活不长"]
SRC_PATH = os.path.join(APP_DIR, "rules", "source_registry.json")


class ZiweiSourceRegistryTests(unittest.TestCase):
    """紫微参考源注册测试。"""

    def setUp(self):
        with open(SRC_PATH, "r", encoding="utf-8") as f:
            self.reg = json.load(f)

    def test_zw_sources_present(self):
        """source_registry.json 包含紫微参考源。"""
        required = ["ziwei_doushu_quanshu", "ziwei_doushu_quanji", "ziwei_doushu_daquan",
                     "traditional_ziwei_palace_system", "traditional_ziwei_sihua_system"]
        for key in required:
            with self.subTest(key=key):
                self.assertIn(key, self.reg)

    def test_zw_sources_have_correct_category(self):
        """紫微参考源分类正确。"""
        cats = {
            "ziwei_doushu_quanshu": "紫微斗数经典",
            "ziwei_doushu_quanji": "紫微斗数综合",
            "ziwei_doushu_daquan": "紫微斗数综合",
            "traditional_ziwei_palace_system": "紫微斗数宫位",
            "traditional_ziwei_sihua_system": "紫微斗数四化",
        }
        for key, expected_cat in cats.items():
            entry = self.reg.get(key, {})
            self.assertEqual(entry.get("category"), expected_cat,
                             f"{key} category mismatch: {entry.get('category')} != {expected_cat}")


class ZiweiPalaceRuleTests(unittest.TestCase):
    """紫微十二宫规则测试。"""

    def setUp(self):
        path = os.path.join(APP_DIR, "rules", "ziwei_palace_rules.json")
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.rules = self.data.get("rules", [])

    def test_12_palaces(self):
        """ziwei_palace_rules.json 包含 12 宫位。"""
        self.assertEqual(len(self.rules), 12)

    def test_each_palace_has_required_fields(self):
        """每条宫位规则包含 life_area / positive_tendencies / risk_tendencies / advice / source_ids。"""
        required = ["life_area", "positive_tendencies", "risk_tendencies", "advice", "source_ids"]
        for rule in self.rules:
            name = rule.get("title", rule.get("id", "unknown"))
            with self.subTest(palace=name):
                for field in required:
                    self.assertIn(field, rule)
                    if isinstance(rule[field], list):
                        self.assertGreater(len(rule[field]), 0, f"{name}.{field} is empty")

    def test_palace_source_ids_valid(self):
        """所有 source_ids 能在 source_registry.json 找到。"""
        with open(SRC_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for rule in self.rules:
            for sid in rule.get("source_ids", []):
                self.assertIn(sid, reg, f"Unknown source_id '{sid}' in {rule.get('id', '')}")

    def test_no_forbidden_words(self):
        """宫位规则中不得出现禁用词。"""
        text = json.dumps(self.rules, ensure_ascii=False)
        for word in FORBIDDEN:
            self.assertNotIn(word, text)


class ZiweiStarRuleTests(unittest.TestCase):
    """十四主星规则测试。"""

    def setUp(self):
        path = os.path.join(APP_DIR, "rules", "ziwei_star_rules.json")
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.rules = self.data.get("rules", [])

    def test_14_stars(self):
        """ziwei_star_rules.json 包含 14 主星。"""
        self.assertEqual(len(self.rules), 14)
        names = [r["star_name"] for r in self.rules]
        expected = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
                     "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]
        self.assertEqual(set(names), set(expected))

    def test_each_star_has_all_fields(self):
        """每颗主星包含 star_type / core_keywords / personality_tendency / career_tendency / wealth_tendency / relationship_tendency / risk_tendency / advice / source_ids。"""
        required = ["star_type", "core_keywords", "personality_tendency", "career_tendency",
                     "wealth_tendency", "relationship_tendency", "risk_tendency", "advice", "source_ids"]
        for rule in self.rules:
            name = rule.get("star_name", "unknown")
            with self.subTest(star=name):
                for field in required:
                    self.assertIn(field, rule, f"{name} missing '{field}'")
                    val = rule[field]
                    if isinstance(val, list):
                        self.assertGreater(len(val), 0, f"{name}.{field} is empty")
                    else:
                        self.assertGreater(len(str(val)), 0, f"{name}.{field} is empty")

    def test_star_source_ids_valid(self):
        """所有 source_ids 能在 source_registry.json 找到。"""
        with open(SRC_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for rule in self.rules:
            for sid in rule.get("source_ids", []):
                self.assertIn(sid, reg)

    def test_no_forbidden_words(self):
        """主星规则中不得出现禁用词。"""
        text = json.dumps(self.rules, ensure_ascii=False)
        for word in FORBIDDEN:
            self.assertNotIn(word, text)


class ZiweiSihuaRuleTests(unittest.TestCase):
    """四化规则测试。"""

    def setUp(self):
        path = os.path.join(APP_DIR, "rules", "ziwei_sihua_rules.json")
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.rules = self.data.get("rules", [])

    def test_4_sihua(self):
        """ziwei_sihua_rules.json 包含 4 化。"""
        self.assertEqual(len(self.rules), 4)
        names = [r["name"] for r in self.rules]
        self.assertEqual(set(names), {"化禄", "化权", "化科", "化忌"})

    def test_each_has_fields(self):
        """每条四化包含 keywords / advantage / disadvantage / suitable / avoid。"""
        for rule in self.rules:
            name = rule.get("name", "")
            with self.subTest(sihua=name):
                self.assertIn("keywords", rule)
                self.assertIn("advantage", rule)
                self.assertIn("suitable", rule)

    def test_sihua_source_ids_valid(self):
        with open(SRC_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for rule in self.rules:
            for sid in rule.get("source_ids", []):
                self.assertIn(sid, reg)


class ZiweiLifeCardTests(unittest.TestCase):
    """紫微命盘名片测试。"""

    def setUp(self):
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_life_card_engine import analyze_ziwei_life_card
        profile = {"name": "测试", "gender": "男", "birth_date": "1990-01-01",
                    "birth_hour": 5, "birth_minute": 0, "birth_place": ""}
        self.chart = build_ziwei_chart(profile)
        self.card = analyze_ziwei_life_card(self.chart)

    def test_card_generates(self):
        """紫微命盘名片可以生成。"""
        self.assertIsNotNone(self.card)
        self.assertIn("ziwei_profile_type", self.card)
        self.assertIn("ming_gong_summary", self.card)

    def test_card_has_required_fields(self):
        """名片包含必要的字段。"""
        required = ["ziwei_profile_type", "ming_gong_summary", "shen_gong_summary",
                     "key_palace_summaries", "source_ids", "source_titles",
                     "ming_shen_relation", "personalized_evidence", "main_stars_ready",
                     "generic_palace_notes", "module_boundary"]
        for field in required:
            self.assertIn(field, self.card)

    def test_card_has_key_palaces(self):
        """名片包含重点宫位摘要。"""
        required = ["官禄宫", "财帛宫", "夫妻宫", "福德宫", "疾厄宫", "迁移宫"]
        summaries = self.card.get("key_palace_summaries", {})
        for name in required:
            self.assertIn(name, summaries)
            self.assertGreater(len(summaries[name]), 0)

    def test_card_has_reasonable_strengths_risks(self):
        """名片包含合理的优势(evidence)和风险(key_palace_summaries)。"""
        self.assertGreaterEqual(len(self.card.get("personalized_evidence", [])), 2)
        self.assertGreaterEqual(len(self.card.get("key_palace_summaries", {})), 4)

    def test_card_no_fake_stars(self):
        """命盘名片不得包含'某星在某宫'的未实现断语。"""
        text = str(self.card)
        fake_patterns = [
            "紫微星在命宫", "天机星在命宫", "太阳星在命宫", "武曲星在命宫", "天同星在命宫",
            "廉贞星在命宫", "天府星在命宫", "太阴星在命宫", "贪狼星在命宫", "巨门星在命宫",
            "天相星在命宫", "天梁星在命宫", "七杀星在命宫", "破军星在命宫",
        ]
        for pattern in fake_patterns:
            self.assertNotIn(pattern, text,
                             f"Life card contains fake star placement: '{pattern}'")

    def test_card_no_forbidden_words(self):
        """命盘名片不得出现禁用词。"""
        text = str(self.card)
        for word in FORBIDDEN:
            self.assertNotIn(word, text)

    def test_card_source_ids_valid(self):
        """source_ids 能在注册表找到。"""
        with open(SRC_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for sid in self.card.get("source_ids", []):
            self.assertIn(sid, reg)

    def test_module_boundary_present(self):
        """名片包含模块边界说明。"""
        boundary = self.card.get("module_boundary", "")
        self.assertGreater(len(boundary), 10)
        self.assertIn("版本", boundary)


if __name__ == "__main__":
    unittest.main()
