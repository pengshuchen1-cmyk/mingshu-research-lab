import sys
import types
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class _Context:
    def __init__(self, streamlit, kind):
        self.streamlit = streamlit
        self.kind = kind

    def __enter__(self):
        self.streamlit.context_stack.append(self.kind)
        return self

    def __exit__(self, *_args):
        self.streamlit.context_stack.pop()


class _FakeStreamlit(types.ModuleType):
    def __init__(self, *, solar_time=False, submitted=False, text_values=None):
        super().__init__("streamlit")
        self.solar_time = solar_time
        self.submitted = submitted
        self.text_values = text_values or {}
        self.session_state = {}
        self.context_stack = []
        self.container_calls = []
        self.form_parent_contexts = []
        self.checkbox_calls = []
        self.text_input_calls = []
        self.errors = []
        self.rerun_calls = 0

    def container(self, **kwargs):
        self.container_calls.append(kwargs)
        return _Context(self, "container")

    def form(self, _key):
        parent = self.context_stack[-1] if self.context_stack else None
        self.form_parent_contexts.append(parent)
        return _Context(self, "form")

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_Context(self, "column") for _ in range(count)]

    def markdown(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def text_input(self, label, **kwargs):
        self.text_input_calls.append((label, "form" in self.context_stack))
        return self.text_values.get(label, kwargs.get("value", ""))

    def selectbox(self, _label, options, **kwargs):
        return options[kwargs.get("index", 0)]

    def radio(self, _label, options, **kwargs):
        return options[kwargs.get("index", 0)]

    def date_input(self, _label, **kwargs):
        return kwargs["value"]

    def checkbox(self, label, **kwargs):
        inside_form = "form" in self.context_stack
        self.checkbox_calls.append((label, inside_form, kwargs))
        key = kwargs.get("key")
        if key:
            self.session_state[key] = self.solar_time
        return self.solar_time

    def form_submit_button(self, *_args, **_kwargs):
        return self.submitted

    def error(self, message):
        self.errors.append(str(message))

    def spinner(self, *_args, **_kwargs):
        return _Context(self, "spinner")

    def rerun(self):
        self.rerun_calls += 1


def test_profile_form_is_one_page_with_all_required_sections():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    for token in [
        "PROFILE_DRAFT_KEY",
        "def _render_unified_profile_form",
        "基本资料",
        "出生日期",
        "出生时间与地点",
        "高级设置",
        "出生资料只用于本地排盘",
        "生成命盘",
    ]:
        assert token in source
    assert source.count("with st.form(") == 1
    assert source.index("_render_unified_profile_form") < source.index("build_bazi_chart(profile)")


def test_profile_form_removes_step_navigation_and_duplicate_chart_summary():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    for token in [
        "PROFILE_STEP_KEY",
        "def _profile_step",
        "def _set_profile_step",
        "def _render_profile_step_one",
        "def _render_profile_step_two",
        "def _render_profile_step_three",
        "第 1 步，共 3 步",
        "下一步",
        "返回上一步",
        "### 当前命盘",
    ]:
        assert token not in source

    render_source = source[source.index("def render_profile_form") :]
    assert "_render_unified_profile_form(draft)" in render_source
    assert 'st.session_state["navigate_to"] = "个人命盘"' in source


def test_true_solar_longitude_rejects_non_numeric_or_out_of_range_values():
    from ui.profile_form import parse_birth_longitude

    for value in ("abc", "181", "-181"):
        try:
            parse_birth_longitude(value)
        except ValueError as exc:
            assert "出生地经度" in str(exc)
        else:
            raise AssertionError(f"{value} 应被拒绝")

    assert parse_birth_longitude("116.4") == 116.4


def test_public_profile_payload_allows_blank_optional_nickname(monkeypatch):
    import ui.profile_form as profile_form

    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    payload = profile_form._build_profile_payload(
        name="",
        gender="女",
        calendar_label="公历",
        birth_date=date(1990, 1, 1),
        birth_hour=10,
        birth_minute=0,
        birth_place="",
        use_solar_time=False,
        birth_longitude=None,
    )

    assert payload["name"] == "访客"
    assert payload["birth_place"] == ""


def test_public_form_source_requires_consent_and_starts_private_session_timer():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")

    assert "称呼（可选，建议昵称）" in source
    assert "我已阅读并同意本次会话隐私说明" in source
    assert "请先阅读并同意本次会话隐私说明" in source
    assert "touch_private_session(st.session_state)" in source


def test_first_solar_time_enable_immediately_reveals_longitude_without_submit_error(monkeypatch):
    import ui.profile_form as profile_form

    draft = {"name": "保留姓名", "birth_place": "北京", "birth_date": date(1990, 1, 1)}
    fake_streamlit = _FakeStreamlit(solar_time=True, submitted=False)
    fake_streamlit.session_state[profile_form.PROFILE_DRAFT_KEY] = draft
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    profile_form._render_unified_profile_form(draft)

    assert fake_streamlit.container_calls == [{"key": "ms5-profile-card", "border": True}]
    assert fake_streamlit.form_parent_contexts == ["container"]
    assert fake_streamlit.checkbox_calls[0][1] is False
    assert ("出生地经度（东经）", True) in fake_streamlit.text_input_calls
    assert fake_streamlit.errors == []
    assert draft["use_solar_time"] is True
    assert fake_streamlit.session_state[profile_form.PROFILE_DRAFT_KEY] is draft
    assert fake_streamlit.session_state.get("profile_use_solar_time") is True


def test_solar_time_switch_off_hides_longitude_and_preserves_disabled_state(monkeypatch):
    import ui.profile_form as profile_form

    draft = {
        "birth_date": date(1990, 1, 1),
        "use_solar_time": True,
        "birth_longitude": "116.4",
    }
    fake_streamlit = _FakeStreamlit(solar_time=False, submitted=False)
    fake_streamlit.session_state[profile_form.PROFILE_DRAFT_KEY] = draft
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    profile_form._render_unified_profile_form(draft)

    assert all(label != "出生地经度（东经）" for label, _inside_form in fake_streamlit.text_input_calls)
    assert draft["use_solar_time"] is False
    assert draft["birth_longitude"] is None
    assert fake_streamlit.session_state.get("profile_use_solar_time") is False


def test_successful_unified_form_navigates_and_clears_draft_and_switch_state(monkeypatch):
    import ui.profile_form as profile_form

    draft = {
        "name": "测试用户",
        "gender": "男",
        "calendar_label": "公历",
        "birth_date": date(1990, 6, 15),
        "birth_hour": 8,
        "birth_minute": 30,
        "birth_place": "北京",
        "use_solar_time": True,
    }
    fake_streamlit = _FakeStreamlit(
        solar_time=True,
        submitted=True,
        text_values={"姓名": "测试用户", "出生地点": "北京", "出生地经度（东经）": "116.4"},
    )
    fake_streamlit.session_state.update(
        {
            profile_form.PROFILE_DRAFT_KEY: draft,
            "profile_use_solar_time": True,
        }
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setattr(profile_form, "validate_profile", lambda _profile: (True, ""))
    monkeypatch.setattr(profile_form, "build_bazi_chart", lambda profile: {"profile": profile, "pillars": {}})
    monkeypatch.setattr(profile_form, "generate_basic_bazi_report", lambda _chart: {"summary": "ok"})

    profile_form._render_unified_profile_form(draft)

    assert fake_streamlit.session_state["current_profile"]["birth_longitude"] == 116.4
    assert fake_streamlit.session_state["navigate_to"] == "个人命盘"
    assert profile_form.PROFILE_DRAFT_KEY not in fake_streamlit.session_state
    assert "profile_use_solar_time" not in fake_streamlit.session_state
    assert fake_streamlit.rerun_calls == 1


def test_profile_card_styles_flatten_the_nested_submit_form():
    from ui.styles import get_global_css

    css = get_global_css()
    selector = '.st-key-ms5-profile-card div[data-testid="stForm"] {'
    assert selector in css
    rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "border: 0" in rule
    assert "box-shadow: none" in rule


def test_profile_card_checkbox_label_has_a_44px_touch_target():
    from ui.styles import get_global_css

    css = get_global_css()
    selector = '.st-key-ms5-profile-card [data-testid="stCheckbox"] label {'
    assert selector in css
    rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "min-height: 44px" in rule
