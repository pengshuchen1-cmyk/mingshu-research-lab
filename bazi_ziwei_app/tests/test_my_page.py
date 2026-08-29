from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_my_page_reuses_canonical_profile_confirmation_when_empty():
    source = (ROOT / "ui" / "my_page.py").read_text(encoding="utf-8")

    assert "from ui.profile_form import (" in source
    assert "PROFILE_DRAFT_KEY" in source
    assert "render_profile_form" in source
    assert "if not profile or not chart:" in source
    assert "render_profile_form(show_header=False, compact=True)" in source
    assert 'st.session_state[PROFILE_SUCCESS_RETURN_KEY] = "设置/档案"' in source
    assert "build_bazi_chart" not in source
    assert "build_birth_preview" not in source


def test_my_page_has_real_session_and_local_controls_without_fake_accounts():
    source = (ROOT / "ui" / "my_page.py").read_text(encoding="utf-8")

    for label in ("编辑资料", "新建命盘", "打开本地命盘档案", "清除当前资料"):
        assert label in source
    assert "clear_private_session(st.session_state)" in source
    assert '"navigate_to"] = "设置/档案"' in source
    for forbidden in ("手机号", "跨设备同步", "长期记忆", "反馈数据库"):
        assert forbidden not in source
    assert '"加载本地档案"' in source
    assert '"当前会话（本机模式）"' in source
    assert "可信本机存储" not in source


def test_profile_edit_seed_keeps_china_standard_fields():
    from ui.my_page import _profile_draft

    draft = _profile_draft(
        {
            "name": "测试昵称",
            "relationship": "伴侣",
            "gender": "女",
            "calendar_type": "solar",
            "birth_date": "1990-02-03",
            "birth_hour": 8,
            "birth_minute": 30,
            "birth_place": "",
        }
    )

    assert draft["birth_date"] == date(1990, 2, 3)
    assert draft["time_precision"] == "精确时间"
    assert draft["relationship"] == "伴侣"
    assert "time_mode" not in draft


def test_profile_success_return_is_one_time_and_allowlisted():
    profile_form = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    privacy = (ROOT / "utils" / "session_privacy.py").read_text(encoding="utf-8")

    assert 'st.session_state.pop(PROFILE_SUCCESS_RETURN_KEY, "个人命盘")' in profile_form
    assert '{"个人命盘", "设置/档案"}' in profile_form
    assert '"profile_success_return_to"' in privacy


def test_explicit_profile_paste_parser_preserves_only_recognized_fields():
    from ui.profile_form import parse_profile_paste

    parsed = parse_profile_paste(
        "昵称：小青，本人，性别女，1990年2月3日 08:30，出生于北京",
        today=date(2025, 1, 1),
    )

    assert parsed == {
        "name": "小青",
        "relationship": "本人",
        "gender": "女",
        "calendar_label": "公历",
        "birth_date": date(1990, 2, 3),
        "birth_hour": 8,
        "birth_minute": 30,
        "time_precision": "精确时间",
        "time_known": True,
        "birth_place": "北京",
    }


def test_profile_paste_parser_rejects_invalid_or_ambiguous_values():
    from ui.profile_form import parse_profile_paste

    for raw in ("1990年2月31日", "本人，伴侣，性别女", "无明确资料"):
        try:
            parse_profile_paste(raw, today=date(2025, 1, 1))
        except ValueError:
            pass
        else:
            raise AssertionError(f"应拒绝：{raw}")


def test_relationship_is_display_only_and_not_a_birth_input_field():
    import inspect
    from core.birth_input_preview import BirthFormInput

    assert "relationship" not in inspect.signature(BirthFormInput).parameters
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    birth_input_block = source.split("birth_input = BirthFormInput(", 1)[1].split(")", 1)[0]
    assert "relationship" not in birth_input_block


def test_mobile_birth_picker_css_keeps_five_columns_without_overflow():
    from ui.styles import get_global_css

    css = get_global_css()
    assert ".st-key-ms5-birth-picker" in css
    assert "body:has(.st-key-ms5-birth-picker) .st-key-ms5-birth-picker" in css
    assert "box-shadow: none !important" in css


def test_empty_my_page_desktop_content_is_centered_without_narrowing_mobile():
    from ui.styles import get_global_css

    css = get_global_css()
    selector = 'body:has(.ms-my-add-bar) [data-testid="stMainBlockContainer"] {'
    desktop_rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "max-width: 800px !important" in desktop_rule
    mobile_css = css.split("@media (max-width: 640px)", 1)[1]
    mobile_rule = mobile_css.split(selector, 1)[1].split("}", 1)[0]
    assert "width: 100% !important" in mobile_rule
    assert "max-width: none !important" in mobile_rule


def test_picker_cancel_restores_snapshot_and_complete_closes():
    from ui.profile_form import (
        PROFILE_PICKER_DAY_KEY,
        PROFILE_PICKER_OPEN_KEY,
        cancel_birth_picker,
        complete_birth_picker,
        open_birth_picker,
    )

    draft = {"birth_date": date(1990, 2, 3), "birth_hour": 8, "birth_minute": 30}
    state = {}
    open_birth_picker(state, draft)
    state[PROFILE_PICKER_DAY_KEY] = 4
    cancel_birth_picker(state)
    assert state[PROFILE_PICKER_DAY_KEY] == 3
    assert state[PROFILE_PICKER_OPEN_KEY] is False

    open_birth_picker(state, draft)
    state[PROFILE_PICKER_DAY_KEY] = 4
    complete_birth_picker(state, draft)
    assert draft["birth_date"] == date(1990, 2, 4)
    assert state[PROFILE_PICKER_OPEN_KEY] is False


def test_cancel_restores_picker_snapshot_without_widget_state_mutation():
    from datetime import date
    from ui.profile_form import (
        PROFILE_PICKER_DAY_KEY,
        PROFILE_PICKER_OPEN_KEY,
        cancel_birth_picker,
        open_birth_picker,
    )

    state = {}
    open_birth_picker(state, {"birth_date": date(1992, 2, 3), "birth_hour": 8, "birth_minute": 30})
    state[PROFILE_PICKER_DAY_KEY] = 4
    cancel_birth_picker(state)

    assert state[PROFILE_PICKER_OPEN_KEY] is False
    assert state[PROFILE_PICKER_DAY_KEY] == 3


def test_real_streamlit_paste_callback_clears_instantiated_raw_widget():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string(
        """
import streamlit as st
from ui.my_page import _apply_profile_paste
from ui.profile_form import PROFILE_PASTE_KEY
st.text_area("粘贴并识别", key=PROFILE_PASTE_KEY)
st.button("识别并填入", on_click=_apply_profile_paste, args=(st.session_state,))
"""
    ).run()

    app.text_area(key="profile_paste_source").input(
        "昵称：小青，本人，性别女，1990年2月3日 08:30，出生于北京"
    ).run()
    app.button[0].click().run()

    assert len(app.exception) == 0
    try:
        raw_after = app.session_state["profile_paste_source"]
    except KeyError:
        raw_after = ""
    assert raw_after == ""
    assert "小青" not in raw_after
    assert app.session_state["profile_draft"]["name"] == "小青"
    assert "private_session_last_active_at" in app.session_state

def test_empty_my_page_field_order_and_real_picker_actions():
    my_source = (ROOT / "ui" / "my_page.py").read_text(encoding="utf-8")
    form_source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")

    assert my_source.index("添加档案") < my_source.index("粘贴并识别（可选）") < my_source.index("render_profile_form(show_header=False, compact=True)")
    assert "ms-my-avatar" not in my_source
    assert "ms-my-empty" not in my_source
    assert "头像" not in my_source
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    assert ".ms-my-avatar" not in styles
    assert ".ms-my-empty" not in styles
    form_body = form_source[form_source.index("def _render_unified_profile_form") :]
    ordered = ["name = st.text_input", '"关系"', '"性别"', "_birth_summary(draft)", '"出生地点"']
    assert [form_body.index(token) for token in ordered] == sorted(form_body.index(token) for token in ordered)
    assert '"取消",' in form_source
    assert '"完成",' in form_source
    assert "ms5-picker-head" not in form_source


def test_picker_session_keys_are_private():
    from ui.profile_form import (
        PROFILE_PICKER_KEYS,
        PROFILE_PICKER_OPEN_KEY,
        PROFILE_PICKER_SNAPSHOT_KEY,
    )
    from utils.session_privacy import PRIVATE_SESSION_KEYS

    assert set(PROFILE_PICKER_KEYS) <= set(PRIVATE_SESSION_KEYS)
    assert {PROFILE_PICKER_OPEN_KEY, PROFILE_PICKER_SNAPSHOT_KEY} <= set(PRIVATE_SESSION_KEYS)
    assert {
        "profile_paste_source",
        "profile_name_input",
        "profile_relationship_input",
        "profile_gender_input",
        "profile_place_input",
    } <= set(PRIVATE_SESSION_KEYS)
