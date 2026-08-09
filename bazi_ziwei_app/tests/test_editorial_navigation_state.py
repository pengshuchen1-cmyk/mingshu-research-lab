from app import _resolve_active_page
from utils.navigation_state import (
    APP_ENTERED_KEY,
    DEFAULT_APP_PAGE,
    LANDING_PAGE_NAME,
    enter_app,
    has_entered_app,
)


def test_private_route_stays_active_across_reruns_until_user_chooses_a_public_page():
    pages = {"首页": object(), "今日/年度建议": object(), "设置/档案": object(), "八字排盘": object()}
    sidebar_pages = {
        "今日/年度建议": pages["今日/年度建议"],
        "设置/档案": pages["设置/档案"],
    }

    active = _resolve_active_page("八字排盘", None, "设置/档案", pages, sidebar_pages)
    assert active == "八字排盘"
    assert _resolve_active_page(None, active, "设置/档案", pages, sidebar_pages) == "八字排盘"
    assert _resolve_active_page("今日/年度建议", active, "设置/档案", pages, sidebar_pages) == "今日/年度建议"


def test_landing_entry_state_is_session_scoped_and_defaults_to_today():
    state = {}

    assert not has_entered_app(state)
    enter_app(state)

    assert state == {APP_ENTERED_KEY: True}
    assert has_entered_app(state)
    assert LANDING_PAGE_NAME == "首页"
    assert DEFAULT_APP_PAGE == "今日/年度建议"
