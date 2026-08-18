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
        selected = self.values.get(label)
        if selected is None and kwargs.get("key") in self.session_state:
            selected = self.session_state[kwargs["key"]]
        if selected is None:
            selected = options[kwargs.get("index", 0)]
        if kwargs.get("key"):
            self.session_state[kwargs["key"]] = selected
        return selected

    def selectbox(self, label, options, **kwargs):
        options = list(options)
        self.selectbox_calls.append((label, tuple(options), kwargs))
        selected = self.values.get(label)
        if selected is None and kwargs.get("key") in self.session_state:
            selected = self.session_state[kwargs["key"]]
        if selected not in options:
            selected = options[kwargs.get("index", 0)]
        if kwargs.get("key"):
            self.session_state[kwargs["key"]] = selected
        return selected

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
    calendar_label = values.get("历法", values.get("出生日期类型", "公历"))
    draft = {
        "birth_date": date(1990, 1, 1),
        "calendar_label": calendar_label,
        "lunar_year": values.get("年", 1999),
        "lunar_month": values.get("月", 7),
        "lunar_day": values.get("日", 1),
    }
    fake.session_state[profile_form.PROFILE_DRAFT_KEY] = draft
    profile_form.open_birth_picker(fake.session_state, draft)
    def fake_wheel(columns, **_kwargs):
        fake.wheel_columns = columns
        return {column["id"]: column["selected"] for column in columns}
    monkeypatch.setattr(profile_form, "render_birth_wheel", fake_wheel)
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    profile_form._render_unified_profile_form(draft)
    return fake


def test_calendar_mode_is_outside_form_and_solar_uses_explicit_five_columns(monkeypatch):
    fake = _render(monkeypatch, {"历法": "公历"})

    calendar_call = next(call for call in fake.radio_calls if call[0] == "历法")
    assert calendar_call[2] is False
    assert calendar_call[3]["key"] == "profile_picker_calendar"
    assert [column["id"] for column in fake.wheel_columns] == ["year", "month", "day", "hour", "minute"]
    assert {call[0] for call in fake.selectbox_calls}.isdisjoint({"年", "月", "日", "时", "分"})
    assert fake.date_input_calls == []


def test_lunar_mode_uses_separate_fields_and_never_uses_date_picker(monkeypatch):
    fake = _render(
        monkeypatch,
        {
            "历法": "农历",
            "年": 2023,
            "月": 2,
            "日": 1,
            "闰月": False,
        },
    )

    assert [column["label"] for column in fake.wheel_columns] == ["年", "月", "日", "时", "分"]
    assert {call[0] for call in fake.selectbox_calls}.isdisjoint({"年", "月", "日", "时", "分"})
    assert "闰月" in fake.checkbox_calls
    assert fake.date_input_calls == []


def test_picker_removes_time_precision_choice_and_uses_exact_clock_columns(monkeypatch):
    fake = _render(monkeypatch, {"历法": "公历"})

    assert all(call[0] != "出生时间精度" for call in fake.radio_calls)
    assert fake.session_state["profile_picker_precision"] == "精确时间"
    assert fake.wheel_columns[3]["items"][12]["label"] == "12时"
    assert fake.wheel_columns[4]["items"][0]["label"] == "00分"
    assert fake.submit_calls == ["校验并预览"]


def test_solar_day_options_follow_month_length_and_leap_year():
    from ui.profile_form import valid_solar_days

    assert valid_solar_days(2024, 2, today=date(2025, 1, 1))[-1] == 29
    assert valid_solar_days(2023, 2, today=date(2025, 1, 1))[-1] == 28
    assert valid_solar_days(2024, 4, today=date(2025, 1, 1))[-1] == 30


def test_lunar_month_options_follow_library_leap_month_and_day_counts():
    from lunar_python import LunarYear
    from ui.profile_form import lunar_month_days

    assert LunarYear.fromYear(2023).getLeapMonth() == 2
    assert len(lunar_month_days(2023, 2)) == 30
    assert len(lunar_month_days(2023, 2, is_leap_month=True)) == 29
    assert LunarYear.fromYear(2024).getLeapMonth() == 0
    assert lunar_month_days(2024, 2, is_leap_month=True) == []


def test_profile_form_source_has_no_native_date_input():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "ui" / "profile_form.py").read_text(encoding="utf-8")
    assert "st.date_input" not in source
