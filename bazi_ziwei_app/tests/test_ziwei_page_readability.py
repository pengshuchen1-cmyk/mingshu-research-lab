"""紫微斗数页面可读性测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ZiweiPageReadabilityTest(unittest.TestCase):
    """确保紫微页面先给普通用户看得懂的入口。"""

    def test_ziwei_page_has_plain_language_entry_and_boundary(self) -> None:
        text = (PROJECT_ROOT / "ui" / "ziwei_page.py").read_text(encoding="utf-8")

        self.assertIn("先看这张紫微名片", text)
        self.assertIn("重点先看", text)
        self.assertIn("当前版本不会把未确认算法包装成结论", text)
        self.assertIn("像性格底盘", text)
        self.assertIn("像后天用力方向", text)

    def test_ziwei_page_renders_plain_manual_and_star_combinations(self) -> None:
        text = (PROJECT_ROOT / "ui" / "ziwei_page.py").read_text(encoding="utf-8")

        self.assertIn("build_ziwei_plain_guide", text)
        self.assertIn("build_ziwei_capability_review", text)
        self.assertIn("算法完成度说明", text)
        self.assertIn("一句话先懂", text)
        self.assertIn("生活里怎么看", text)
        self.assertIn("可以怎么做", text)
        self.assertIn("边界提醒", text)
        self.assertIn("它是什么意思", text)
        self.assertIn("现实里怎么看", text)
        self.assertIn("应该注意什么", text)
        self.assertIn("星曜组合", text)
        self.assertIn("主星落宫怎么看", text)
        self.assertIn("常见组合", text)
        self.assertIn("load_star_combination_rules", text)

    def test_ziwei_page_exposes_algorithm_audit_tab(self) -> None:
        text = (PROJECT_ROOT / "ui" / "ziwei_page.py").read_text(encoding="utf-8")

        self.assertIn("audit_ziwei_algorithms", text)
        self.assertIn("算法复核", text)
        self.assertIn("五行局复核", text)
        self.assertIn("十四主星复核", text)
        self.assertIn("辅星/煞星复核", text)
        self.assertIn("大限复核", text)
        self.assertIn("仍需真实盘例继续校验", text)

    def test_ziwei_page_exposes_plain_triangle_manual(self) -> None:
        text = (PROJECT_ROOT / "ui" / "ziwei_page.py").read_text(encoding="utf-8")

        self.assertIn("relation_cards", text)
        self.assertIn("plain_explanation", text)
        self.assertIn("zw-triangle-role", text)
        self.assertIn("参考依据", text)


if __name__ == "__main__":
    unittest.main()
