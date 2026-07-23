"""新建命盘表单历法与时间精度控件测试。"""

from __future__ import annotations

import sys
import types
from datetime import date


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
    def __init__(self, *, values=None):
        super().__init__("streamlit")
        self.values = values or {}
        self.session_state = {}
        self.context_stack = []
        self.radio_calls = []
        self.selectbox_calls = []
        self.date_input_calls = []
        self.checkbox_calls = []
        self.submit_calls = []

    def container(self, **_kwargs):
        return _Context(self, "container")

    def form(self, _key):
        return _Context(self, "form")

    def columns(self, spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [_Context(self, "column") for _ in range(count)]

    def markdown(self, *_args, **_kwargs):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def text_input(self, label, **kwargs):
        return self.values.get(label, kwargs.get("value", ""))

    def radio(self, label, options, **kwargs):
        self.radio_calls.append((label, tuple(options), "form" in self.context_stack, kwargs))
        return self.values.get(label, options[kwargs.get("index", 0)])

    def selectbox(self, label, options, **kwargs):
        options = list(options)
        self.selectbox_calls.append((label, tuple(options), kwargs))
        return self.values.get(label, options[kwargs.get("index", 0)])

    def date_input(self, label, **kwargs):
        self.date_input_calls.append(label)
        return self.values.get(label, kwargs["value"])

    def checkbox(self, label, **kwargs):
        self.checkbox_calls.append(label)
        return self.values.get(label, kwargs.get("value", False))

    def form_submit_button(self, label, **_kwargs):
        self.submit_calls.append(label)
        return False

    def button(self, *_args, **_kwargs):
        return False

    def error(self, *_args, **_kwargs):
        return None


def _render(monkeypatch, values):
    import ui.profile_form as profile_form

    fake = _FakeStreamlit(values=values)
    draft = {"birth_date": date(1990, 1, 1)}
    fake.session_state[profile_form.PROFILE_DRAFT_KEY] = draft
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    profile_form._render_unified_profile_form(draft)
    return fake


def test_calendar_mode_is_outside_form_and_solar_uses_explicit_date_label(monkeypatch):
    fake = _render(monkeypatch, {"出生日期类型": "公历"})

    calendar_call = next(call for call in fake.radio_calls if call[0] == "出生日期类型")
    assert calendar_call[2] is False
    assert calendar_call[3]["key"] == "profile_calendar_label"
    assert fake.date_input_calls == ["公历出生日期"]


def test_lunar_mode_uses_separate_fields_and_never_uses_date_picker(monkeypatch):
    fake = _render(
        monkeypatch,
        {
            "出生日期类型": "农历",
            "农历年份": 1999,
            "农历月份": 7,
            "农历日期": 1,
            "是否闰月": False,
        },
    )

    assert {"农历年份", "农历月份", "农历日期"} <= {
        call[0] for call in fake.selectbox_calls
    }
    assert "是否闰月" in fake.checkbox_calls
    assert fake.date_input_calls == []


def test_time_precision_offers_exact_traditional_and_unknown_modes(monkeypatch):
    fake = _render(monkeypatch, {"出生日期类型": "公历"})

    precision_call = next(call for call in fake.radio_calls if call[0] == "出生时间精度")
    assert precision_call[1] == ("精确时间", "传统时辰", "时辰不详")
    assert precision_call[2] is True
    assert fake.submit_calls == ["校验并预览"]
