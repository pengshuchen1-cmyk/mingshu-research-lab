"""Session-scoped transition from the public landing page into the product shell."""

from __future__ import annotations

from typing import MutableMapping


APP_ENTERED_KEY = "mingshu_app_entered"
LANDING_PAGE_NAME = "首页"
DEFAULT_APP_PAGE = "今日/年度建议"


def has_entered_app(state: MutableMapping) -> bool:
    """Return whether the current Streamlit session entered the product shell."""
    return state.get(APP_ENTERED_KEY) is True


def enter_app(state: MutableMapping) -> None:
    """Mark the current Streamlit session as having left the landing page."""
    state[APP_ENTERED_KEY] = True
