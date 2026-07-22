"""第三轮个人命盘页用户可见收口测试。"""

from __future__ import annotations

import ast
from contextlib import nullcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "ui" / "life_overview_page.py"
REAL_PROFILE = {
    "name": "男命样例",
    "gender": "男",
    "birth_date": "1990-01-01",
    "birth_hour": 10,
    "birth_minute": 0,
    "birth_place": "上海",
    "use_solar_time": False,
}


def _page_source() -> str:
    return PAGE_PATH.read_text(encoding="utf-8")


def test_page_hides_source_line_but_preserves_basis_and_health_boundary():
    source = _page_source()

    assert "**参考**" not in source
    assert 'st.expander("命理依据"' in source
    assert "**判断依据**" in source
    assert "medical_disclaimer" in source

    from core.bazi_engine import build_bazi_chart
    from core.life_overview_engine import analyze_life_overview

    result = analyze_life_overview(build_bazi_chart(REAL_PROFILE))
    assert result["evidence"]
    assert result["source_ids"]
    assert result["source_titles"] == [
        "渊海子平",
        "三命通会",
        "子平真诠",
        "滴天髓阐微",
        "命理探源",
        "穷通宝鉴",
    ]
    assert "不构成医学诊断" in result["health_overview"]["medical_disclaimer"]


def test_five_dimension_cards_show_full_summary_without_redundant_caption(monkeypatch):
    import ui.life_overview_page as page

    long_relation_summary = (
        "关系判断应完整呈现夫妻宫、配偶星、桃花和现实边界，"
        "不能为了卡片高度而主动截断；这段文字特意超过七十二个字符，"
        "用于证明卡片主体保留了完整结论。"
        "即使结论继续说明双方沟通节奏、责任分工、现实经营与资源边界，"
        "卡片主体也必须逐字保留，不能用省略号替代后半段。"
    )
    markdown_calls: list[tuple[str, dict]] = []
    captions: list[str] = []
    monkeypatch.setattr(
        page.st,
        "markdown",
        lambda body, **kwargs: markdown_calls.append((str(body), kwargs)),
    )
    monkeypatch.setattr(page.st, "caption", lambda body, **_kwargs: captions.append(str(body)))
    monkeypatch.setattr(page.st, "expander", lambda *_args, **_kwargs: nullcontext())

    page._render_five_dimension_insights(
        {
            "scores": {
                "wealth": 62,
                "romance": 68,
                "health_stability": 40,
                "career": 94,
                "overall_balance": 66,
            },
            "romance_overview": {"romance_summary": long_relation_summary},
        }
    )

    card_html = "\n".join(
        body for body, kwargs in markdown_calls if kwargs.get("unsafe_allow_html")
    )
    assert long_relation_summary in card_html
    assert "同一套分数同时呈现等级与白话简评，避免重复评分。" not in captions


def test_five_dimension_renderer_has_no_active_summary_slicing():
    tree = ast.parse(_page_source())
    renderer = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_render_five_dimension_insights"
    )
    summary_slices = []
    for node in ast.walk(renderer):
        if not isinstance(node, ast.Subscript) or not isinstance(node.slice, ast.Slice):
            continue
        value = node.value
        if isinstance(value, ast.Name) and "summary" in value.id:
            summary_slices.append(node)

    assert summary_slices == []


def test_real_chart_baseline_keeps_personal_dimensions_relation_and_basis():
    from core.bazi_engine import build_bazi_chart
    from core.life_overview_engine import analyze_life_overview

    chart = build_bazi_chart(REAL_PROFILE)
    result = analyze_life_overview(chart)

    assert [chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")] == [
        "己巳",
        "丙子",
        "丙寅",
        "癸巳",
    ]
    assert result["overall_pattern"] == "丙火日主中和 · 比劫格局"
    expected_scores = {
        "wealth": 62,
        "romance": 68,
        "health_stability": 40,
        "career": 94,
        "overall_balance": 66,
    }
    assert {key: result["scores"][key] for key in expected_scores} == expected_scores
    relation = result["romance_overview"]["romance_summary"]
    for token in ["夫妻宫寅木", "财星2个", "桃花0处", "现实经营"]:
        assert token in relation
    assert result["evidence"][:3] == [
        "财星2个（正财0/偏财2）",
        "官杀2个（正官2/七杀0）",
        "食伤4个",
    ]
