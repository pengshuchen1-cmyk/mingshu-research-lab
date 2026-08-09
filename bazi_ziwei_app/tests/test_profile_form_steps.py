import sys
import types
from datetime import date, timedelta
from pathlib import Path
from types import MappingProxyType, SimpleNamespace


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
    def __init__(
        self,
        *,
        values=None,
        preview_submitted=False,
        confirm_submitted=False,
        session_state=None,
    ):
        super().__init__("streamlit")
        self.values = values or {}
        self.preview_submitted = preview_submitted
        self.confirm_submitted = confirm_submitted
        self.session_state = session_state if session_state is not None else {}
        self.context_stack = []
        self.container_calls = []
        self.form_parent_contexts = []
        self.markdowns = []
        self.captions = []
        self.infos = []
        self.errors = []
        self.submit_calls = []
        self.button_calls = []
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

    def markdown(self, value, **_kwargs):
        self.markdowns.append(str(value))

    def caption(self, value, **_kwargs):
        self.captions.append(str(value))

    def info(self, value, **_kwargs):
        self.infos.append(str(value))

    def text_input(self, label, **kwargs):
        return self.values.get(label, kwargs.get("value", ""))

    def selectbox(self, label, options, **kwargs):
        options = list(options)
        return self.values.get(label, options[kwargs.get("index", 0)])

    def radio(self, label, options, **kwargs):
        return self.values.get(label, options[kwargs.get("index", 0)])

    def date_input(self, label, **kwargs):
        return self.values.get(label, kwargs["value"])

    def checkbox(self, label, **kwargs):
        return self.values.get(label, kwargs.get("value", False))

    def form_submit_button(self, label, **_kwargs):
        self.submit_calls.append((label, "form" in self.context_stack))
        if label == "校验并预览":
            return self.preview_submitted
        if label == "确认生成命盘":
            return self.confirm_submitted
        return False

    def button(self, label, **_kwargs):
        self.button_calls.append((label, "form" in self.context_stack))
        return False

    def error(self, message):
        self.errors.append(str(message))

    def spinner(self, *_args, **_kwargs):
        return _Context(self, "spinner")

    def rerun(self):
        self.rerun_calls += 1


def _preview(
    value,
    *,
    chart_fingerprint="chart-v1",
    solar_datetime="1999-08-11 10:00",
):
    profile = MappingProxyType(value.to_profile())
    chart = MappingProxyType(
        {
            "profile": profile,
            "pillars": MappingProxyType({}),
            "chart_fingerprint_v2": chart_fingerprint,
        }
    )
    return SimpleNamespace(
        profile=profile,
        chart=chart,
        input_text="农历1999年七月初一，非闰月，男，巳时",
        solar_datetime=solar_datetime,
        pillars=("己卯", "壬申", "乙未", "辛巳"),
        calculation_basis="本地规则证据",
        input_fingerprint=value.fingerprint(),
        chart_fingerprint=chart_fingerprint,
    )


def _lunar_values(**overrides):
    values = {
        "姓名": "测试用户",
        "性别": "男",
        "出生日期类型": "农历",
        "农历年份": 1999,
        "农历月份": 7,
        "农历日期": 1,
        "是否闰月": False,
        "出生时间精度": "传统时辰",
        "传统时辰": "巳时",
        "出生地点": "北京",
    }
    values.update(overrides)
    return values


def _run_form(
    monkeypatch,
    *,
    values=None,
    preview_submitted=False,
    confirm_submitted=False,
    session_state=None,
    preview_builder=None,
):
    import ui.profile_form as profile_form

    state = session_state if session_state is not None else {}
    draft = state.setdefault(profile_form.PROFILE_DRAFT_KEY, {})
    fake = _FakeStreamlit(
        values=values or _lunar_values(),
        preview_submitted=preview_submitted,
        confirm_submitted=confirm_submitted,
        session_state=state,
    )
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    monkeypatch.setattr(
        profile_form,
        "build_birth_preview",
        preview_builder or (lambda value: _preview(value)),
    )
    monkeypatch.setattr(
        profile_form,
        "generate_basic_bazi_report",
        lambda _chart: {"summary": "ok"},
    )
    profile_form._render_unified_profile_form(draft)
    return fake


def test_first_submit_saves_receipt_without_saving_chart_and_renders_confirmation(monkeypatch):
    import ui.profile_form as profile_form

    state = {}
    first_render = _run_form(
        monkeypatch,
        preview_submitted=True,
        session_state=state,
    )
    fake = _run_form(monkeypatch, session_state=state)

    assert first_render.rerun_calls == 1
    assert fake.submit_calls == [
        ("校验并预览", True),
        ("确认生成命盘", True),
    ]
    assert fake.button_calls == []
    receipt = "\n".join(fake.markdowns)
    assert "原始输入：农历1999年七月初一，非闰月，男，巳时" in receipt
    assert "标准时间：中国标准时间 1999-08-11 10:00" in receipt
    assert "四柱预览：己卯 / 壬申 / 乙未 / 辛巳" in receipt
    assert "计算依据：本地规则证据" in receipt
    saved = state[profile_form.PROFILE_PREVIEW_KEY]
    assert "profile" in saved
    assert "chart" not in saved
    assert "current_chart" not in state
    assert "private_session_last_active_at" in state


def test_changing_birth_field_invalidates_saved_preview(monkeypatch):
    import ui.profile_form as profile_form

    state = {}
    _run_form(monkeypatch, preview_submitted=True, session_state=state)
    fake = _run_form(
        monkeypatch,
        values=_lunar_values(**{"农历日期": 2}),
        session_state=state,
    )

    assert profile_form.PROFILE_PREVIEW_KEY not in state
    assert profile_form.PROFILE_PREVIEW_INPUT_KEY not in state
    assert ("确认生成命盘", True) not in fake.submit_calls
    assert any("已变更" in message for message in fake.infos)


def test_changing_exact_time_to_equivalent_traditional_hour_invalidates_preview(
    monkeypatch,
):
    import ui.profile_form as profile_form

    state = {}
    _run_form(
        monkeypatch,
        values=_lunar_values(
            **{
                "出生时间精度": "精确时间",
                "出生小时": 10,
                "出生分钟": 0,
            }
        ),
        preview_submitted=True,
        session_state=state,
    )
    fake = _run_form(
        monkeypatch,
        values=_lunar_values(),
        session_state=state,
    )

    assert profile_form.PROFILE_PREVIEW_KEY not in state
    assert ("确认生成命盘", True) not in fake.submit_calls
    assert any("已变更" in message for message in fake.infos)


def test_switching_from_lunar_preview_to_solar_uses_a_safe_default_date(monkeypatch):
    state = {}
    _run_form(monkeypatch, preview_submitted=True, session_state=state)

    fake = _run_form(
        monkeypatch,
        values={
            "姓名": "测试用户",
            "性别": "男",
            "出生日期类型": "公历",
            "出生时间精度": "精确时间",
            "出生地点": "北京",
        },
        session_state=state,
    )

    assert fake.errors == []


def test_exact_midnight_is_restored_without_invalidating_preview(monkeypatch):
    import ui.profile_form as profile_form

    state = {}
    midnight_values = _lunar_values(
        **{
            "出生时间精度": "精确时间",
            "出生小时": 0,
            "出生分钟": 0,
        }
    )
    _run_form(
        monkeypatch,
        values=midnight_values,
        preview_submitted=True,
        session_state=state,
    )
    fake = _run_form(
        monkeypatch,
        values=_lunar_values(**{"出生时间精度": "精确时间"}),
        session_state=state,
    )

    assert profile_form.PROFILE_PREVIEW_KEY in state
    assert ("确认生成命盘", True) in fake.submit_calls
    assert fake.infos == []


def test_converted_lunar_date_in_the_future_is_not_saved_as_preview(monkeypatch):
    tomorrow = date.today() + timedelta(days=1)

    fake = _run_form(
        monkeypatch,
        preview_submitted=True,
        preview_builder=lambda value: _preview(
            value,
            solar_datetime=f"{tomorrow.isoformat()} 10:00",
        ),
    )

    assert fake.errors == ["出生日期不能晚于今天。"]
    assert "profile_birth_preview" not in fake.session_state
    assert "private_session_last_active_at" in fake.session_state
    assert ("确认生成命盘", True) not in fake.submit_calls


def test_confirmation_rebuilds_matching_chart_before_generation(monkeypatch):
    import ui.profile_form as profile_form

    calls = []

    def builder(value):
        calls.append(value)
        return _preview(value)

    state = {}
    _run_form(
        monkeypatch,
        preview_submitted=True,
        session_state=state,
        preview_builder=builder,
    )
    fake = _run_form(
        monkeypatch,
        confirm_submitted=True,
        session_state=state,
        preview_builder=builder,
    )

    assert len(calls) == 2
    assert fake.session_state["current_profile"]["calendar_type"] == "lunar"
    assert fake.session_state["current_chart"]["chart_fingerprint_v2"] == "chart-v1"
    assert fake.session_state["navigate_to"] == "个人命盘"
    assert fake.rerun_calls == 1


def test_confirmation_rejects_rebuilt_chart_with_changed_fingerprint(monkeypatch):
    import ui.profile_form as profile_form

    calls = 0

    def builder(value):
        nonlocal calls
        calls += 1
        return _preview(value, chart_fingerprint=f"chart-v{calls}")

    state = {}
    _run_form(
        monkeypatch,
        preview_submitted=True,
        session_state=state,
        preview_builder=builder,
    )
    fake = _run_form(
        monkeypatch,
        confirm_submitted=True,
        session_state=state,
        preview_builder=builder,
    )

    assert "current_chart" not in state
    assert fake.rerun_calls == 0
    assert any("命盘结果已变化" in message for message in fake.errors)


def test_conversion_failure_shows_no_confirmation(monkeypatch):
    def fail(_value):
        raise ValueError("农历日期无法转换")

    fake = _run_form(
        monkeypatch,
        preview_submitted=True,
        preview_builder=fail,
    )

    assert fake.errors == ["农历日期无法转换"]
    assert "private_session_last_active_at" in fake.session_state
    assert ("确认生成命盘", True) not in fake.submit_calls


def test_profile_form_remains_one_data_entry_form():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    assert source.count("with st.form(") == 1
    assert "PROFILE_STEP_KEY" not in source
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


def test_public_form_keeps_consent_and_discloses_cloud_ai(monkeypatch):
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")

    assert "称呼（可选，建议昵称）" in source
    assert "我已阅读并同意本次会话隐私说明" in source
    assert "请先阅读并同意本次会话隐私说明" in source
    privacy_notice = (
        "出生资料会传至本站服务器内存用于排盘，不写入公网命盘数据库。进入 AI 问答后，"
        "去身份化命盘事实、问题和近期对话会发送给已配置的云端 AI 服务；原始生日、姓名和"
        "地点不会发送给该服务，30 分钟无操作后清除本次会话。"
    )
    assert privacy_notice in source
    assert "touch_private_session(st.session_state)" in source


def test_birth_input_explains_name_is_not_required_before_calendar_choice():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    notice = (
        "无需输入姓名，只需选择农历或公历的出生日期及时间；"
        "性别仍用于排盘规则。"
    )

    assert notice in source
    assert source.index(notice) < source.index('"出生日期类型"')


def test_profile_card_styles_flatten_the_nested_submit_form():
    from ui.styles import get_global_css

    css = get_global_css()
    selector = '.st-key-ms5-profile-card div[data-testid="stForm"] {'
    assert selector in css
    rule = css.split(selector, 1)[1].split("}", 1)[0]
    assert "border: 0" in rule
    assert "box-shadow: none" in rule


def test_profile_form_shows_two_stage_progress_and_mobile_single_columns():
    source = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "填写出生资料" in source
    assert "核对排盘结果" in source
    assert 'aria-label="建立命盘进度"' in source
    assert '.st-key-ms5-profile-card [data-testid="stHorizontalBlock"]' in styles
    assert "grid-template-columns: minmax(0, 1fr) !important" in styles
