import unittest


class SixtyJiaziKnowledgeTests(unittest.TestCase):
    def test_lookup_known_years_and_nayin(self):
        from core.sixty_jiazi import get_jiazi_by_year

        self.assertEqual(get_jiazi_by_year(1984)["pillar"], "甲子")
        self.assertEqual(get_jiazi_by_year(1984)["nayin"], "海中金")
        self.assertEqual(get_jiazi_by_year(2024)["pillar"], "甲辰")
        self.assertEqual(get_jiazi_by_year(2026)["pillar"], "丙午")

    def test_entry_contains_user_visible_knowledge_fields(self):
        from core.sixty_jiazi import get_jiazi_by_year

        entry = get_jiazi_by_year(2026)
        for field in [
            "gan",
            "zhi",
            "gan_element",
            "zhi_element",
            "nayin",
            "sample_years",
            "plain_explanation",
            "lichun_boundary_note",
        ]:
            self.assertIn(field, entry)
        self.assertIn("立春", entry["lichun_boundary_note"])
        self.assertIn(2026, entry["sample_years"])

    def test_all_entries_have_plain_reality_mapping_and_advice(self):
        from core.sixty_jiazi import load_sixty_jiazi

        rows = load_sixty_jiazi()
        self.assertEqual(len(rows), 60)
        for row in rows:
            with self.subTest(pillar=row["pillar"]):
                self.assertIn("symbolic_keywords", row)
                self.assertIn("reality_mapping", row)
                self.assertIn("user_advice", row)
                self.assertGreaterEqual(len(row["symbolic_keywords"]), 2)
                self.assertIn("现实", row["reality_mapping"])
                self.assertNotIn("必定", row["user_advice"])

    def test_page_is_registered_and_mentions_not_core_prediction(self):
        from app import get_pages

        self.assertIn("六十甲子", get_pages())
        import ui.sixty_jiazi_page as page

        page_text = page.__doc__ or ""
        self.assertIn("知识层", page_text)
        self.assertIn("不作为断事核心", page_text)

    def test_build_four_pillar_jiazi_cards_from_chart(self):
        from report.sixty_jiazi_report import build_four_pillar_jiazi_cards

        chart = {
            "pillars": {
                "year": {"name": "年柱", "pillar": "甲辰"},
                "month": {"name": "月柱", "pillar": "乙巳"},
                "day": {"name": "日柱", "pillar": "丙午"},
                "hour": {"name": "时柱", "pillar": "丁未"},
            },
            "five_elements": {"木": 2.0, "火": 3.0, "土": 1.5, "金": 0.5, "水": 1.0},
        }
        cards = build_four_pillar_jiazi_cards(chart)
        self.assertEqual(len(cards), 4)
        self.assertEqual(cards[0]["life_area"], "早年环境、家族背景、外部圈层")
        self.assertEqual(cards[2]["pillar"], "丙午")
        self.assertEqual(cards[2]["nayin"], "天河水")
        self.assertIn("核心底色", cards[2]["user_explanation"])
        self.assertIn("不单独判断吉凶", cards[2]["boundary_note"])

    def test_nayin_and_real_five_element_comparison(self):
        from report.sixty_jiazi_report import compare_nayin_with_chart_elements

        chart = {
            "pillars": {
                "year": {"pillar": "甲辰"},
                "month": {"pillar": "乙巳"},
                "day": {"pillar": "丙午"},
                "hour": {"pillar": "丁未"},
            },
            "five_elements": {"木": 2.0, "火": 3.0, "土": 1.5, "金": 0.5, "水": 1.0},
        }
        comparison = compare_nayin_with_chart_elements(chart)
        self.assertIn("nayin_distribution", comparison)
        self.assertIn("chart_distribution", comparison)
        self.assertIn("以原局五行为主", comparison["explanation"])
        self.assertGreater(comparison["nayin_distribution"]["火"], 0)

    def test_sixty_jiazi_markdown_report_section(self):
        from report.sixty_jiazi_report import build_sixty_jiazi_markdown

        chart = {
            "pillars": {
                "year": {"name": "年柱", "pillar": "甲辰"},
                "month": {"name": "月柱", "pillar": "乙巳"},
                "day": {"name": "日柱", "pillar": "丙午"},
                "hour": {"name": "时柱", "pillar": "丁未"},
            },
            "five_elements": {"木": 2.0, "火": 3.0, "土": 1.5, "金": 0.5, "水": 1.0},
        }
        markdown = build_sixty_jiazi_markdown(chart)
        self.assertIn("## 六十甲子说明书", markdown)
        self.assertIn("四柱甲子名片", markdown)
        self.assertIn("纳音与原局五行对比", markdown)
        self.assertIn("立春", markdown)
        self.assertIn("不作为断事核心", markdown)
        self.assertLessEqual(markdown.count("六十甲子与纳音是知识层和解释层"), 1)
        self.assertNotIn("{'", markdown)

    def test_bazi_empty_state_mentions_sixty_jiazi_feature(self):
        from pathlib import Path

        text = Path(__file__).resolve().parents[1].joinpath("ui", "bazi_page.py").read_text(encoding="utf-8")
        self.assertIn("四柱甲子名片", text)
        self.assertIn("生成命盘后会显示", text)
        self.assertIn("navigate_to", text)

    def test_bazi_sixty_jiazi_renderer_has_streamlit_available(self):
        import ui.bazi_page as page

        self.assertTrue(hasattr(page, "st"))


if __name__ == "__main__":
    unittest.main()
