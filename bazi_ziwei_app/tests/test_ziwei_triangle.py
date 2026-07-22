"""三方四正 + 四化测试 — v1.2-C。"""

import os, sys, json, unittest; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

FORBIDDEN = ["必定","绝对","注定","一定发财","一定离婚","必有灾","必有大病","必定富贵","必定孤独","必死","短命","活不长"]

class ZiweiTriangleTests(unittest.TestCase):
    def setUp(self):
        from core.ziwei_engine import build_ziwei_chart
        self.profile = {"name":"T","gender":"男","birth_date":"1990-01-01","birth_hour":5,"birth_minute":0}
        self.chart = build_ziwei_chart(self.profile)
        from core.ziwei_triangle_engine import get_sanfang_sizheng
        self.tri = get_sanfang_sizheng("命宫", self.chart)

    def test_triangle_returns_required_fields(self):
        self.assertIn("target_palace", self.tri)
        self.assertIn("sanfang", self.tri)
        self.assertIn("sizheng", self.tri)
        self.assertIn("summary", self.tri)
        self.assertEqual(len(self.tri["sanfang"]), 2)

    def test_triangle_contains_stars(self):
        self.assertIn("main_stars", self.tri)

    def test_no_forbidden_words(self):
        for word in FORBIDDEN:
            self.assertNotIn(word, json.dumps(self.tri, ensure_ascii=False))

    def test_boundary_present(self):
        self.assertIn("module_boundary", self.tri)

    def test_triangle_has_plain_manual_basis_and_sources(self):
        for field in ["plain_explanation", "relation_cards", "opportunity", "risk", "advice", "source_ids", "basis"]:
            self.assertIn(field, self.tri)
        self.assertGreaterEqual(len(self.tri["relation_cards"]), 4)
        roles = {item.get("role") for item in self.tri["relation_cards"]}
        self.assertIn("本宫", roles)
        self.assertIn("三合支援", roles)
        self.assertIn("对宫照应", roles)
        self.assertIn("紫微斗数大全", self.tri["basis"])
        self.assertIn("ziwei_doushu_daquan", self.tri["source_ids"])


class ZiweiSihuaTests(unittest.TestCase):
    def test_all_year_gan_have_mapping(self):
        from core.ziwei_sihua_engine import SIHUA_MAP
        for yg in "甲乙丙丁戊己庚辛壬癸":
            self.assertIn(yg, SIHUA_MAP)
            m = SIHUA_MAP[yg]
            for tt in ["化禄","化权","化科","化忌"]:
                self.assertIn(tt, m)

    def test_sihua_returns_structure(self):
        from core.ziwei_sihua_engine import get_sihua_by_year_gan
        s = get_sihua_by_year_gan("甲")
        self.assertIn("sihua_ready", s)
        self.assertTrue(s["sihua_ready"])
        self.assertIn("mapping", s)
        self.assertIn("interpretation", s)

    def test_invalid_year_gan(self):
        from core.ziwei_sihua_engine import get_sihua_by_year_gan
        s = get_sihua_by_year_gan("")
        self.assertFalse(s["sihua_ready"])

    def test_apply_to_chart(self):
        from core.ziwei_engine import build_ziwei_chart
        from core.ziwei_sihua_engine import get_sihua_by_year_gan, apply_sihua_to_chart
        from core.ziwei_star_engine import get_year_gan_from_profile
        profile = {"name":"T","gender":"男","birth_date":"1990-01-01","birth_hour":5,"birth_minute":0}
        chart = build_ziwei_chart(profile)
        yg = get_year_gan_from_profile(profile)
        s = get_sihua_by_year_gan(yg)
        s = apply_sihua_to_chart(chart, s)
        self.assertIn("sihua_by_palace", s)

    def test_no_forbidden_words(self):
        from core.ziwei_sihua_engine import get_sihua_by_year_gan
        for yg in "甲乙丙丁戊己庚辛壬癸":
            s = get_sihua_by_year_gan(yg)
            text = json.dumps(s, ensure_ascii=False)
            for word in FORBIDDEN:
                self.assertNotIn(word, text)

    def test_only_main_stars_in_main_transforms(self):
        from core.ziwei_sihua_engine import get_sihua_by_year_gan, MAIN_STARS
        for yg in "甲乙丙丁戊己庚辛壬癸":
            s = get_sihua_by_year_gan(yg)
            for star in s.get("main_star_transforms", {}).values():
                self.assertIn(star, MAIN_STARS)

if __name__ == "__main__":
    unittest.main()
