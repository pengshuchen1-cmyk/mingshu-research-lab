import json
import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

VALID_CATEGORIES = {"八字经典", "八字综合", "格局用神", "调候五行", "旺衰体用", "命理整理", "命例参考", "紫微斗数基础", "紫微斗数经典", "紫微斗数综合", "紫微斗数宫位", "紫微斗数四化"}
FORBIDDEN_PATTERNS = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财"]
SOURCE_REGISTRY_PATH = os.path.join(APP_DIR, "rules", "source_registry.json")
MONTHLY_EVENT_RULES_PATH = os.path.join(APP_DIR, "rules", "monthly_event_rules.json")


class SourceRegistryTests(unittest.TestCase):
    """参考书注册表测试。"""

    def setUp(self):
        with open(SOURCE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def test_registry_can_load(self):
        """source_registry.json 可以加载为字典。"""
        self.assertIsInstance(self.registry, dict)
        self.assertGreater(len(self.registry), 0)

    def test_each_entry_has_required_fields(self):
        """每条注册记录必须有 title / category / used_for / note。"""
        for key, entry in self.registry.items():
            with self.subTest(key=key):
                self.assertIn("title", entry)
                self.assertIn("category", entry)
                self.assertIn("used_for", entry)
                self.assertIn("note", entry)
                self.assertIsInstance(entry["used_for"], list)
                self.assertGreater(len(entry["used_for"]), 0)
                self.assertIn(entry["category"], VALID_CATEGORIES,
                              f"Invalid category '{entry['category']}' in {key}")

    def test_known_sources_present(self):
        """必须包含七本核心参考书。"""
        required = ["yuan_hai_zi_ping", "san_ming_tong_hui", "zi_ping_zhen_quan",
                     "qiong_tong_bao_jian", "di_tian_sui_chan_wei", "ming_li_tan_yuan",
                     "shen_feng_tong_kao"]
        for key in required:
            with self.subTest(key=key):
                self.assertIn(key, self.registry)

    def test_monthly_rules_have_source_ids(self):
        """monthly_event_rules.json 每条规则必须有 source_ids。"""
        with open(MONTHLY_EVENT_RULES_PATH, "r", encoding="utf-8") as f:
            rules = json.load(f)
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
        for rule in rules:
            with self.subTest(rule_id=rule.get("id", "unknown")):
                self.assertIn("source_ids", rule)
                self.assertGreater(len(rule["source_ids"]), 0)

    def test_source_ids_exist_in_registry(self):
        """monthly_event_rules.json 的 source_ids 必须在 source_registry.json 中找到对应条目。"""
        with open(MONTHLY_EVENT_RULES_PATH, "r", encoding="utf-8") as f:
            rules = json.load(f)
        for rule in rules:
            for sid in rule.get("source_ids", []):
                with self.subTest(rule_id=rule.get("id", "unknown"), source_id=sid):
                    self.assertIn(sid, self.registry,
                                  f"source_id '{sid}' not found in source_registry.json")

    def test_monthly_rules_have_basis(self):
        """monthly_event_rules.json 每条规则必须有 basis。"""
        with open(MONTHLY_EVENT_RULES_PATH, "r", encoding="utf-8") as f:
            rules = json.load(f)
        for rule in rules:
            with self.subTest(rule_id=rule.get("id", "unknown")):
                self.assertIn("basis", rule)
                self.assertGreater(len(rule["basis"]), 0)

    def test_all_rule_files_have_source_ids(self):
        """所有 rules/*.json 规则文件必须包含 source_ids（ziwei_rules.json 除外）。"""
        skipped = {"ziwei_rules.json"}
        rule_dir = os.path.join(APP_DIR, "rules")
        for fname in os.listdir(rule_dir):
            if fname in skipped or fname == "source_registry.json" or not fname.endswith(".json"):
                continue
            with self.subTest(file=fname):
                with open(os.path.join(rule_dir, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                rules_list = data if isinstance(data, list) else data.get("rules", [])
                if not rules_list:
                    continue
                for rule in rules_list:
                    self.assertIn("source_ids", rule,
                                  f"Rule '{rule.get('id', 'unknown')}' in {fname} missing source_ids")
                    self.assertGreater(len(rule["source_ids"]), 0)

    def test_no_forbidden_absolute_patterns(self):
        """规则文案中不得出现绝对化判断词。"""
        rule_dir = os.path.join(APP_DIR, "rules")
        for fname in os.listdir(rule_dir):
            if not fname.endswith(".json") or fname == "source_registry.json":
                continue
            with self.subTest(file=fname):
                with open(os.path.join(rule_dir, fname), "r", encoding="utf-8") as f:
                    text = f.read()
                for pattern in FORBIDDEN_PATTERNS:
                    self.assertNotIn(pattern, text,
                                     f"Found forbidden pattern '{pattern}' in {fname}")


class MonthlySourceTests(unittest.TestCase):
    """流月分析参考来源测试。"""

    def setUp(self):
        self.chart = {
            "day_master": "甲",
            "pillars": {
                "year": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
                "month": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
                "day": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
                "hour": {"gan": "甲", "zhi": "子", "pillar": "甲子"},
            },
            "day_master_strength": {
                "strength": "旺",
                "net_score": 30,
                "favorable_elements": ["金", "土"],
                "unfavorable_elements": ["木", "水"],
            },
        }
        from core.monthly_engine import analyze_monthly_fortune
        self.monthly_data = analyze_monthly_fortune(self.chart, 2026)

    def test_monthly_returns_basis(self):
        """analyze_monthly_fortune 返回的每个月必须包含 basis。"""
        for item in self.monthly_data:
            with self.subTest(month=item.get("month_name", "")):
                self.assertIn("basis", item)

    def test_monthly_returns_source_ids(self):
        """analyze_monthly_fortune 返回的每个月必须包含 source_ids。"""
        for item in self.monthly_data:
            with self.subTest(month=item.get("month_name", "")):
                self.assertIn("source_ids", item)
                self.assertIsInstance(item["source_ids"], list)

    def test_monthly_returns_source_titles(self):
        """analyze_monthly_fortune 返回的每个月必须包含 source_titles。"""
        for item in self.monthly_data:
            with self.subTest(month=item.get("month_name", "")):
                self.assertIn("source_titles", item)
                self.assertIsInstance(item["source_titles"], list)

    def test_monthly_source_ids_exist_in_registry(self):
        """返回的 source_ids 必须在 source_registry.json 中有对应条目。"""
        with open(SOURCE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)
        for item in self.monthly_data:
            for sid in item.get("source_ids", []):
                with self.subTest(month=item.get("month_name", ""), source_id=sid):
                    self.assertIn(sid, registry)

    def test_monthly_12_months_have_month_name(self):
        """返回列表应包含 12 个月的流月分析。"""
        self.assertEqual(len(self.monthly_data), 12)
        names = [item.get("month_name", "") for item in self.monthly_data]
        expected = [f"{i}月" for i in range(1, 13)]
        self.assertEqual(names, expected)


if __name__ == "__main__":
    unittest.main()
