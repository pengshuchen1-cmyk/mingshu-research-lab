from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_focuses_on_question_entry_instead_of_daily_advice():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

    assert "_render_question_composer" in source
    assert "build_daily_advice" not in source
    assert "_daily_advice_card_markup" not in source
    assert "ms2-daily-advice" not in source


def test_homepage_does_not_render_unlabelled_fixed_personal_results():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

    for fixed_claim in [
        "98.7%",
        "96.2%",
        "95.4%",
        "93.1%",
        "命盘评分",
        "甲辰运",
        "正官格",
        "事业上升期",
    ]:
        assert fixed_claim not in source


def test_pending_home_question_is_session_only_and_consumed_once():
    from ui.inquiry_page import PENDING_QUESTION_KEY, pop_pending_question

    state = {PENDING_QUESTION_KEY: "  今天我的运势如何  "}
    assert pop_pending_question(state) == "今天我的运势如何"
    assert PENDING_QUESTION_KEY not in state
    assert pop_pending_question(state) is None


def test_homepage_arrow_routes_to_chart_and_clears_pending_question(monkeypatch):
    import ui.homepage_components as homepage
    from ui.inquiry_page import PENDING_QUESTION_KEY

    class RerunRequested(RuntimeError):
        pass

    state = {PENDING_QUESTION_KEY: "旧问题"}
    fake_streamlit = type(
        "FakeStreamlit",
        (),
        {
            "session_state": state,
            "rerun": staticmethod(lambda: (_ for _ in ()).throw(RerunRequested())),
        },
    )()
    monkeypatch.setattr(homepage, "st", fake_streamlit)

    with pytest.raises(RerunRequested):
        homepage._open_product_page("个人命盘")

    assert PENDING_QUESTION_KEY not in state
    assert state["mingshu_app_entered"] is True
    assert state["navigate_to"] == "个人命盘"


def test_inquiry_without_chart_preserves_pending_question_and_never_answers(monkeypatch):
    import ui.inquiry_page as inquiry

    state = {inquiry.PENDING_QUESTION_KEY: "今天我的运势如何"}
    empty_states = []
    fake_streamlit = type(
        "FakeStreamlit",
        (),
        {
            "session_state": state,
            "button": staticmethod(lambda *_args, **_kwargs: False),
        },
    )()
    monkeypatch.setattr(inquiry, "st", fake_streamlit)
    monkeypatch.setattr(
        inquiry,
        "empty_state_header",
        lambda title, description: empty_states.append((str(title), str(description))),
    )
    monkeypatch.setattr(
        inquiry,
        "_answer",
        lambda *_args, **_kwargs: pytest.fail("无命盘时不应提交问答"),
    )

    inquiry.render_inquiry_page()

    assert empty_states == [
        (
            "AI 问答需要个人命盘",
            "请先新建或选择一个命盘，AI 才能读取本地四柱规则结论。",
        )
    ]
    assert state[inquiry.PENDING_QUESTION_KEY] == "今天我的运势如何"
