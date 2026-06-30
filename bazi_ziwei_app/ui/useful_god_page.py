"""日主喜忌页面兼容入口。"""

from __future__ import annotations

from ui.five_element_page import render_five_element_page


def render_useful_god_page() -> None:
    """兼容旧导航测试，实际复用五行喜忌页面。"""
    render_five_element_page()
