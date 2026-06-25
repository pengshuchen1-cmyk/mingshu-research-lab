import os
import sys
import unittest


APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class RuleEngineTests(unittest.TestCase):
    def test_all_rule_files_load_with_required_fields(self):
        from core.rule_engine import load_rules

        rule_files = [
            "ten_god_rules.json",
            "five_element_rules.json",
            "useful_god_rules.json",
            "yearly_rules.json",
            "monthly_event_rules.json",
            "career_rules.json",
            "wealth_rules.json",
            "love_rules.json",
            "risk_rules.json",
            "advice_rules.json",
            "ziwei_rules.json",
        ]
        for file_name in rule_files:
            rules = load_rules(file_name)
            self.assertIn("rules", rules)
            for rule in rules["rules"]:
                if "trigger" in rule:
                    continue
                for key in ["id", "title", "condition", "text", "advice"]:
                    self.assertIn(key, rule)


if __name__ == "__main__":
    unittest.main()
