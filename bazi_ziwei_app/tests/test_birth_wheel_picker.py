"""Contracts for the isolated Streamlit v2 birth wheel."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _columns():
    from ui.birth_wheel_picker import wheel_column

    return [
        wheel_column("year", "年", [1990, 1991], 1990, lambda value: f"{value}年"),
        wheel_column("month", "月", [1, 2], 1, lambda value: f"{value}月"),
        wheel_column("day", "日", [1, 2], 1, lambda value: f"{value}日"),
        wheel_column("hour", "时", [0, 1], 0, lambda value: f"{value:02d}时"),
        wheel_column("minute", "分", [0, 30], 0, lambda value: f"{value:02d}分"),
    ]


def test_selection_is_whitelisted_by_exact_value_and_type():
    from ui.birth_wheel_picker import validate_wheel_selection

    valid = {"year": 1991, "month": 2, "day": 2, "hour": 1, "minute": 30}
    assert validate_wheel_selection(valid, _columns()) == valid
    assert validate_wheel_selection({**valid, "month": 13}, _columns()) is None
    assert validate_wheel_selection({**valid, "year": "1991"}, _columns()) is None
    assert validate_wheel_selection({**valid, "extra": 1}, _columns()) is None


def test_sync_rejects_tampered_component_state_before_picker_keys_change():
    from ui.profile_form import PROFILE_PICKER_YEAR_KEY, sync_birth_wheel_selection

    state = {PROFILE_PICKER_YEAR_KEY: 1990}
    assert sync_birth_wheel_selection(
        state,
        {"year": 2099, "month": 1, "day": 1, "hour": 0, "minute": 0},
        _columns(),
        precision="精确时间",
    ) is False
    assert state[PROFILE_PICKER_YEAR_KEY] == 1990


def test_component_source_uses_v2_accessible_native_wheels_without_html_injection():
    source = (ROOT / "ui" / "birth_wheel_picker.py").read_text(encoding="utf-8")

    assert "st.components.v2.component" in source
    assert "components.v1" not in source
    assert "innerHTML" not in source
    assert "textContent" in source
    assert "scroll-snap-type: y mandatory" in source
    assert "role', 'listbox" in source
    assert "role', 'option" in source
    assert "ArrowDown" in source and "Home" in source and "PageDown" in source
    assert "prefers-reduced-motion: reduce" in source
    assert "--row-height: 44px" in source
    assert "grid-template-columns: repeat(5, minmax(0, 1fr))" in source


def test_component_session_key_is_private_and_expirable():
    from utils.session_privacy import PRIVATE_SESSION_KEYS

    assert "profile_birth_wheel" in PRIVATE_SESSION_KEYS


def test_reopening_picker_discards_stale_component_selection():
    from datetime import date
    from ui.birth_wheel_picker import BIRTH_WHEEL_COMPONENT_KEY
    from ui.profile_form import PROFILE_PICKER_DAY_KEY, open_birth_picker

    state = {BIRTH_WHEEL_COMPONENT_KEY: {"selection": {"day": 31}}}
    open_birth_picker(state, {"birth_date": date(1992, 2, 3)})

    assert BIRTH_WHEEL_COMPONENT_KEY not in state
    assert state[PROFILE_PICKER_DAY_KEY] == 3


def test_component_callback_syncs_selection_before_the_next_render():
    from ui.birth_wheel_picker import BIRTH_WHEEL_COMPONENT_KEY
    from ui.profile_form import (
        PROFILE_PICKER_DAY_KEY,
        PROFILE_PICKER_YEAR_KEY,
        sync_birth_wheel_component_state,
    )

    selection = {"year": 1991, "month": 2, "day": 2, "hour": 1, "minute": 30}
    state = {BIRTH_WHEEL_COMPONENT_KEY: {"selection": selection}}
    assert sync_birth_wheel_component_state(state, _columns(), precision="精确时间") is True
    assert state[PROFILE_PICKER_YEAR_KEY] == 1991
    assert state[PROFILE_PICKER_DAY_KEY] == 2


def test_component_callback_rejects_expired_public_session(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from ui.birth_wheel_picker import BIRTH_WHEEL_COMPONENT_KEY
    import ui.profile_form as profile_form
    from ui.profile_form import PROFILE_PICKER_YEAR_KEY, sync_birth_wheel_component_state
    from utils.session_privacy import LAST_ACTIVE_KEY

    expired_at = datetime.now(timezone.utc) - timedelta(minutes=31)
    state = {
        BIRTH_WHEEL_COMPONENT_KEY: {
            "selection": {"year": 1991, "month": 2, "day": 2, "hour": 1, "minute": 30}
        },
        PROFILE_PICKER_YEAR_KEY: 1990,
        "profile_draft": {"name": "不得复活"},
        LAST_ACTIVE_KEY: expired_at.isoformat(),
    }
    monkeypatch.setattr(profile_form, "is_public_mode", lambda: True)
    assert sync_birth_wheel_component_state(state, _columns(), precision="精确时间") is False
    assert "profile_draft" not in state
    assert PROFILE_PICKER_YEAR_KEY not in state
    assert BIRTH_WHEEL_COMPONENT_KEY not in state


def test_component_callback_does_not_apply_public_ttl_in_local_mode(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from ui.birth_wheel_picker import BIRTH_WHEEL_COMPONENT_KEY
    import ui.profile_form as profile_form
    from ui.profile_form import PROFILE_PICKER_YEAR_KEY, sync_birth_wheel_component_state
    from utils.session_privacy import LAST_ACTIVE_KEY

    selection = {"year": 1991, "month": 2, "day": 2, "hour": 1, "minute": 30}
    state = {
        BIRTH_WHEEL_COMPONENT_KEY: {"selection": selection},
        PROFILE_PICKER_YEAR_KEY: 1990,
        "profile_draft": {"name": "本地档案"},
        LAST_ACTIVE_KEY: (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat(),
    }
    monkeypatch.setattr(profile_form, "is_public_mode", lambda: False)

    assert sync_birth_wheel_component_state(state, _columns(), precision="精确时间") is True
    assert state[PROFILE_PICKER_YEAR_KEY] == 1991
    assert state["profile_draft"] == {"name": "本地档案"}


def test_scroll_publishes_center_value_without_a_debounce_race():
    source = (ROOT / "ui" / "birth_wheel_picker.py").read_text(encoding="utf-8")

    scroll_handler = source.split("listbox.onscroll = () => {", 1)[1].split("};", 1)[0]
    assert "Math.round(listbox.scrollTop / rowHeight)" in scroll_handler
    assert "publish(column.id, column.items[index].value)" in scroll_handler
    assert "setTimeout" not in scroll_handler
    assert "behavior: 'auto'" in source


def test_picker_buttons_are_flat_text_actions():
    from ui.styles import get_global_css

    css = get_global_css()
    selector = "body:has(.st-key-ms5-birth-picker) .st-key-ms5-birth-picker .stButton button {"
    rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "background: transparent !important" in rule
    assert "border: 0 !important" in rule
    assert "box-shadow: none !important" in rule
    assert 'button[data-testid="stBaseButton-primary"]' in css
    assert "color: #174E3C !important" in css


def test_picker_header_centers_calendar_and_anchors_text_actions():
    from ui.styles import get_global_css

    css = get_global_css()
    header = css.split(
        '.st-key-ms5-picker-toolbar [data-testid="stHorizontalBlock"] {',
        1,
    )[1].split("}", 1)[0]
    assert "grid-template-columns: minmax(44px, 1fr) auto minmax(44px, 1fr) !important" in header
    assert "align-items: center !important" in header
    assert '>[data-testid="stColumn"]:first-child' not in header
    assert ':first-child .stButton button' in css
    assert "color: var(--cc-muted-foreground) !important" in css
    assert ':last-child .stButton button' in css
    assert "color: #174E3C !important" in css
    assert ".ms5-picker-hint" in css
