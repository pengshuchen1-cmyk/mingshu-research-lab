"""v1.0.4 命局总论泛化句检查。"""

from __future__ import annotations

import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


GENERIC_SENTENCES = [
    "财运有机会，但需稳健",
    "感情需要沟通",
    "健康注意作息",
    "事业适合稳步发展",
    "暂无特别突出的财富风险点",
]

FORBIDDEN_WORDS = [
    "必定",
    "绝对",
    "注定",
    "一定发财",
    "一定离婚",
    "必定破财",
    "必有灾",
    "必有大病",
    "短命",
    "一定买房",
    "必有车祸",
]


class NoGenericLifeOverviewTests(unittest.TestCase):
    def test_life_overview_avoids_generic_sentences_and_forbidden_words(self):
        from core.bazi_engine import build_bazi_chart
        from core.life_overview_engine import analyze_life_overview

        chart = build_bazi_chart({"name": "泛化句检查", "gender": "男", "birth_date": "1998-04-01", "birth_hour": 6, "birth_minute": 0, "birth_place": "杭州", "use_solar_time": False})
        overview = analyze_life_overview(chart)
        text = str(overview)
        for sentence in GENERIC_SENTENCES:
            self.assertNotIn(sentence, text)
        for word in FORBIDDEN_WORDS:
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
