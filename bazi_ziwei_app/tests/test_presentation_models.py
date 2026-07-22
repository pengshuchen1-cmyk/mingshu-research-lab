import datetime as dt
import json

import pytest


def test_daily_guidance_view_is_public_and_json_safe():
    from core.presentation_models import build_daily_guidance_view

    view = build_daily_guidance_view(dt.date(2026, 7, 11))

    assert view["kind"] == "daily_guidance"
    assert view["is_personal"] is False
    assert set(view) == {
        "kind",
        "is_personal",
        "date",
        "day_pillar",
        "title",
        "element_theme",
        "wearing_colors",
        "wearing_advice",
        "cautions",
        "primary_action",
        "theme",
        "focus",
        "action",
        "reminder",
        "details",
        "basis",
        "boundary_note",
    }
    assert json.loads(json.dumps(view, ensure_ascii=False)) == view
    assert "birth" not in json.dumps(view, ensure_ascii=False).lower()
    assert view["day_pillar"]


def test_daily_guidance_view_exposes_public_advice_as_safe_copies():
    from core.presentation_models import build_daily_guidance_view

    colors = ["青绿", "米白", "浅灰"]
    cautions = ["避免临时起意", "不要同时推进太多事"]
    actions = ["先完成最重要的一件事", "整理工作环境"]
    advice = {
        "date": "2026-07-14",
        "day_pillar": "己丑",
        "title": "今日指引",
        "element_theme": "木",
        "lucky_colors": colors,
        "wearing_advice": "选择青绿或米白单品",
        "actions_to_avoid": cautions,
        "suitable_actions": actions,
        "relaxation_advice": "保留一段安静时间",
        "basis": "传统历法公开参考",
        "boundary_note": "这是大众参考，不读取出生资料。",
        "name": "不应泄露",
        "birth_date": "2000-01-01",
        "birth_place": "不应泄露",
    }

    view = build_daily_guidance_view(advice=advice)

    assert view["element_theme"] == "木"
    assert view["wearing_colors"] == colors
    assert view["wearing_advice"] == "选择青绿或米白单品"
    assert view["cautions"] == cautions
    assert view["primary_action"] == actions[0]
    assert view["wearing_colors"] is not colors
    assert view["cautions"] is not cautions
    serialized = json.dumps(view, ensure_ascii=False)
    assert json.loads(serialized) == view
    assert "不应泄露" not in serialized
    assert "birth_date" not in serialized
    assert "birth_place" not in serialized


def test_missing_chart_is_not_invented():
    from core.presentation_models import build_chart_summary_view, build_profile_status

    assert build_chart_summary_view(None) == {
        "kind": "chart_summary",
        "ready": False,
        "summary": "尚未建立个人命盘。",
    }
    assert build_profile_status(None, None) == {
        "kind": "profile_status",
        "has_profile": False,
        "has_chart": False,
        "next_action": "新建命盘",
    }


def test_yearly_guidance_and_chart_summary_expose_only_safe_fields():
    from core.presentation_models import (
        build_chart_summary_view,
        build_profile_status,
        build_yearly_guidance_view,
    )

    yearly = build_yearly_guidance_view(2026)
    assert set(yearly) == {
        "kind",
        "is_personal",
        "year",
        "title",
        "theme",
        "focus",
        "actions",
        "basis",
        "boundary_note",
    }
    assert yearly["kind"] == "yearly_guidance"
    assert yearly["is_personal"] is False
    assert json.loads(json.dumps(yearly, ensure_ascii=False)) == yearly

    chart_summary = build_chart_summary_view(
        {
            "day_master": "甲",
            "day_master_strength": {"favorable_elements": ["水", "木"]},
            "profile": {"name": "不应泄露", "birth_date": "2000-01-01"},
        }
    )
    assert set(chart_summary) == {
        "kind",
        "ready",
        "summary",
        "day_master",
        "favorable_elements",
        "next_action",
    }
    assert "不应泄露" not in json.dumps(chart_summary, ensure_ascii=False)
    assert "甲" in chart_summary["summary"]
    assert "水、木" in chart_summary["summary"]
    assert build_profile_status({"name": "用户"}, chart_summary) == {
        "kind": "profile_status",
        "has_profile": True,
        "has_chart": True,
        "next_action": "个人命盘",
    }


@pytest.mark.parametrize("incomplete_advice", [{}, {"title": "今年建议｜2026年 丙午"}])
def test_incomplete_yearly_advice_fails_without_fabricating_a_view(incomplete_advice):
    from core.presentation_models import build_yearly_guidance_view

    with pytest.raises(ValueError, match="年度大众建议数据不完整"):
        build_yearly_guidance_view(1999, advice=incomplete_advice)


@pytest.mark.parametrize("invalid_chart", [None, {}, {"profile": {}}, {"foo": "bar"}])
def test_invalid_chart_shapes_are_explicitly_treated_as_no_chart(invalid_chart):
    from core.presentation_models import build_chart_summary_view, build_profile_status

    assert build_chart_summary_view(invalid_chart) == {
        "kind": "chart_summary",
        "ready": False,
        "summary": "尚未建立个人命盘。",
    }
    assert build_profile_status(None, invalid_chart) == {
        "kind": "profile_status",
        "has_profile": False,
        "has_chart": False,
        "next_action": "新建命盘",
    }
