import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def test_product_navigation_uses_internal_named_routes_only():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'PUBLIC_PAGE_NAMES = ("首页", "今日/年度建议", "个人命盘", "简明报告", "设置/档案")' in source
    assert "PRODUCT_NAV_ITEMS" in source
    assert 'st.session_state["navigate_to"] = target' in source
    assert "def render_product_navigation" in source
    assert "?page=" not in source.split("def render_product_navigation", 1)[1]


def test_request_navigation_sets_only_named_target_and_reruns(monkeypatch):
    app = importlib.import_module("app")
    rerun_calls = []
    fake_streamlit = SimpleNamespace(
        session_state={},
        rerun=lambda: rerun_calls.append(True),
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    app._request_navigation("简明报告")

    assert fake_streamlit.session_state == {"navigate_to": "简明报告"}
    assert rerun_calls == [True]


def test_product_navigation_targets_are_named_pages():
    app = importlib.import_module("app")
    pages = app.get_pages()

    assert all(target in pages for _, target in app.PRODUCT_NAV_ITEMS)
