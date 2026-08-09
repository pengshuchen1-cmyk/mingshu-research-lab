"""侧边栏导航稳定性测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SidebarNavigationPersistsTest(unittest.TestCase):
    """侧边栏导航稳定性测试。"""

    def test_public_sidebar_navigation_uses_simplified_pages(self) -> None:
        """默认侧栏只展示大众使用版入口。"""
        import sys

        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        from app import get_pages, get_sidebar_pages

        all_pages = get_pages()
        sidebar_pages = get_sidebar_pages(all_pages)

        self.assertEqual(
            list(sidebar_pages.keys()),
            ["今日/年度建议", "个人命盘", "AI问答", "简明报告", "设置/档案"],
        )
        self.assertNotIn("大运流年", sidebar_pages)
        self.assertNotIn("六十甲子", sidebar_pages)
        self.assertIn("大运流年", all_pages)
        self.assertIn("六十甲子", all_pages)

    def test_sidebar_navigation_always_renders_when_navigate_to_is_used(self) -> None:
        """快捷跳转时也必须渲染左侧导航，否则载入命盘后侧栏会消失。"""
        text = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn('st.session_state.pop("navigate_to", None)', text)
        self.assertIn("sidebar_pages = get_sidebar_pages(pages)", text)
        self.assertIn('key="sidebar_navigation"', text)
        self.assertIn("st.sidebar.radio", text)
        self.assertLess(
            text.index("if has_entered_app(st.session_state):"),
            text.index("st.sidebar.radio"),
        )
        self.assertIn("def _resolve_active_page", text)
        self.assertIn("active_page = _resolve_active_page(", text)
        self.assertIn("render_product_navigation(active_page)", text)
        self.assertIn("pages[active_page]()", text)
        sidebar_radio = text.index("st.sidebar.radio")
        self.assertLess(sidebar_radio, text.index("active_page = _resolve_active_page("))
        self.assertLess(sidebar_radio, text.index("render_product_navigation(active_page)"))
        self.assertLess(sidebar_radio, text.index("pages[active_page]()"))
        self.assertNotIn("selected = nav_target", text)


if __name__ == "__main__":
    unittest.main()
