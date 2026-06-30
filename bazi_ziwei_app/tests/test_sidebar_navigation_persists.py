"""侧边栏导航稳定性测试。"""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SidebarNavigationPersistsTest(unittest.TestCase):
    """侧边栏导航稳定性测试。"""

    def test_sidebar_navigation_always_renders_when_navigate_to_is_used(self) -> None:
        """快捷跳转时也必须渲染左侧导航，否则载入命盘后侧栏会消失。"""
        text = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn('st.session_state["sidebar_navigation"] = nav_target', text)
        self.assertIn('key="sidebar_navigation"', text)
        self.assertIn("st.sidebar.radio", text)
        self.assertNotIn("selected = nav_target", text)


if __name__ == "__main__":
    unittest.main()
