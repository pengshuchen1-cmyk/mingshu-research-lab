"""辅星/煞星/大限引擎测试 — v1.2-E"""

import os, sys, unittest; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))
FORBIDDEN = ["必有灾","必定出事","一定破财","必有大病","必定刑伤","短命","绝对","注定"]

class MinorStarTests(unittest.TestCase):
    def test_wenchang_works(self):
        from core.ziwei_minor_star_engine import calculate_wenchang
        r = calculate_wenchang("卯")
        self.assertTrue(r["placement_ready"])
        self.assertIn("branch", r)

    def test_wenqu_works(self):
        from core.ziwei_minor_star_engine import calculate_wenqu
        r = calculate_wenqu("午")
        self.assertTrue(r["placement_ready"])
        self.assertIn("branch", r)

    def test_zuofu_works(self):
        from core.ziwei_minor_star_engine import calculate_zuofu
        r = calculate_zuofu(5)
        self.assertTrue(r["placement_ready"])

    def test_youbi_works(self):
        from core.ziwei_minor_star_engine import calculate_youbi
        r = calculate_youbi(5)
        self.assertTrue(r["placement_ready"])

    def test_all_minor_stars_unique(self):
        from core.ziwei_minor_star_engine import calculate_all_minor_stars
        r = calculate_all_minor_stars("卯", 5)
        branches = [v["branch"] for v in r["stars"].values()]
        self.assertEqual(len(branches), len(set(branches)), "Minor stars should have unique branches")

    def test_no_forbidden_words(self):
        import json
        from core.ziwei_minor_star_engine import calculate_all_minor_stars
        text = json.dumps(calculate_all_minor_stars("卯", 5), ensure_ascii=False)
        for w in FORBIDDEN: self.assertNotIn(w, text)


class FierceStarTests(unittest.TestCase):
    def test_qingyang_works(self):
        from core.ziwei_fierce_star_engine import calculate_qingyang
        r = calculate_qingyang("庚")
        self.assertTrue(r["placement_ready"])
        self.assertEqual(r["branch"], "酉")

    def test_tuoluo_works(self):
        from core.ziwei_fierce_star_engine import calculate_tuoluo
        r = calculate_tuoluo("庚")
        self.assertTrue(r["placement_ready"])
        self.assertEqual(r["branch"], "未")

    def test_dikong_works(self):
        from core.ziwei_fierce_star_engine import calculate_dikong
        r = calculate_dikong("庚")
        self.assertTrue(r["placement_ready"])

    def test_dijie_works(self):
        from core.ziwei_fierce_star_engine import calculate_dijie
        r = calculate_dijie("庚")
        self.assertTrue(r["placement_ready"])

    def test_all_fierce_unique(self):
        from core.ziwei_fierce_star_engine import calculate_all_fierce_stars
        r = calculate_all_fierce_stars("庚", "午", "卯")
        branches = [v["branch"] for v in r["stars"].values() if v.get("placement_ready")]
        self.assertEqual(len(branches), len(set(branches)), "Fierce stars should have unique branches")

    def test_no_forbidden_words(self):
        import json
        from core.ziwei_fierce_star_engine import calculate_all_fierce_stars
        text = json.dumps(calculate_all_fierce_stars("庚","午","卯"), ensure_ascii=False)
        for w in FORBIDDEN: self.assertNotIn(w, text)


class DaxianTests(unittest.TestCase):
    def test_daxian_works(self):
        from core.ziwei_daxian_engine import calculate_daxian
        r = calculate_daxian("男", "庚", 5, "戌", "辰", {"命宫":["天同","巨门"]})
        self.assertTrue(r["daxian_ready"])
        self.assertEqual(len(r["stages"]), 12)

    def test_daxian_fields(self):
        from core.ziwei_daxian_engine import calculate_daxian
        r = calculate_daxian("男", "庚", 5, "戌", "辰", {})
        self.assertIn("start_age", r)
        self.assertIn("forward", r)
        self.assertIn("stages", r)
        self.assertIn("source_ids", r)
        stage = r["stages"][0]
        self.assertIn("age_range", stage)
        self.assertIn("palace", stage)
        self.assertIn("branch", stage)

    def test_daxian_invalid_input(self):
        from core.ziwei_daxian_engine import calculate_daxian
        r = calculate_daxian("", "", 0, "", "", {})
        self.assertFalse(r["daxian_ready"])

    def test_no_forbidden_words(self):
        import json
        from core.ziwei_daxian_engine import calculate_daxian
        text = json.dumps(calculate_daxian("男","庚",5,"戌","辰",{}), ensure_ascii=False)
        for w in FORBIDDEN: self.assertNotIn(w, text)

if __name__ == "__main__":
    unittest.main()
