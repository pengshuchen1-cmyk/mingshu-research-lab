from app import _resolve_active_page


def test_private_route_stays_active_across_reruns_until_user_chooses_a_public_page():
    pages = {"首页": object(), "设置/档案": object(), "八字排盘": object()}
    sidebar_pages = {"首页": pages["首页"], "设置/档案": pages["设置/档案"]}

    active = _resolve_active_page("八字排盘", None, "设置/档案", pages, sidebar_pages)
    assert active == "八字排盘"
    assert _resolve_active_page(None, active, "设置/档案", pages, sidebar_pages) == "八字排盘"
    assert _resolve_active_page("首页", active, "设置/档案", pages, sidebar_pages) == "首页"
