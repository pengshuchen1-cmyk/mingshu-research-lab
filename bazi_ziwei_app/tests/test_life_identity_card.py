"""个人摘要五行身份卡展示契约。"""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "ui" / "life_overview_page.py"
STYLES_PATH = ROOT / "ui" / "styles.py"


def _chart(
    day_master: str = "丙",
    *,
    element_scores: dict[str, float] | None = None,
) -> dict:
    return {
        "profile": {"name": "林某"},
        "day_master": day_master,
        "day_master_strength": {"strength": "中和", "net_score": 3.0},
        "five_elements": element_scores
        or {"木": 1.2, "火": 4.8, "土": 2.1, "金": 0.9, "水": 1.0},
    }


def _overview() -> dict:
    return {
        "overall_pattern": "丙火日主中和 · 比劫格局",
        "overall_summary": "丙火日主中和，整体节奏稳中有进。后续详见完整命盘。",
        "life_keywords": ["丙日主", "中和", "火偏旺", "比劫格局"],
    }


def test_identity_card_model_has_a_fixed_presentation_contract():
    from ui.life_overview_page import _build_life_identity_card

    model = _build_life_identity_card(_chart(), _overview())

    assert set(model) == {
        "name",
        "day_master",
        "day_element",
        "strength",
        "dominant_elements",
        "pattern",
        "summary",
        "term_ids",
    }
    assert model == {
        "name": "林某",
        "day_master": "丙",
        "day_element": "火",
        "strength": "中和",
        "dominant_elements": ["火"],
        "pattern": "比劫格局",
        "summary": "丙火日主中和，整体节奏稳中有进。",
        "term_ids": ["day-master", "day-element-fire", "strength", "element-fire", "pattern"],
    }


def test_identity_card_reads_chart_and_overview_data_without_parsing_html():
    from ui.life_overview_page import _build_life_identity_card

    chart = _chart(
        "庚",
        element_scores={"木": 0.5, "火": 0.5, "土": 3.0, "金": 4.0, "水": 2.0},
    )
    chart["profile"]["name"] = "周某"
    chart["day_master_strength"]["strength"] = "身强"
    overview = _overview()
    overview["overall_pattern"] = "庚金日主身强 · 印星格局"
    overview["overall_summary"] = "庚金的结构重在稳定承接。第二句不进入摘要卡。"

    model = _build_life_identity_card(chart, overview)

    assert model["name"] == "周某"
    assert model["day_master"] == "庚"
    assert model["day_element"] == "金"
    assert model["strength"] == "身强"
    assert model["dominant_elements"] == ["金", "土"]
    assert model["pattern"] == "印星格局"
    assert model["summary"] == "庚金的结构重在稳定承接。"


def test_identity_summary_adds_chart_specific_structure_when_analysis_exists():
    from ui.life_overview_page import _build_life_identity_card

    chart = _chart()
    chart["ten_god_counts"] = {
        "比肩": 3, "劫财": 2, "食神": 1, "伤官": 1, "正财": 2,
        "偏财": 0, "正官": 1, "七杀": 2, "正印": 1, "偏印": 0,
    }
    chart["day_master_strength"].update(
        {"favorable_elements": ["木", "水"], "unfavorable_elements": ["火"], "net_score": 3.0}
    )

    summary = _build_life_identity_card(chart, _overview())["summary"]

    assert "比劫5" in summary
    assert "官杀3" in summary
    assert "财星2" in summary
    assert "喜木水" in summary
    assert "净评分3" in summary


def test_identity_card_skips_the_profile_key_before_the_real_overview_sentence():
    from ui.life_overview_page import _build_life_identity_card

    overview = _overview()
    overview["overall_summary"] = (
        "林某｜女｜1990-01-01｜10:0｜上海。"
        "丙火日主中和 · 比劫格局，整体节奏稳中有进。"
        "后续详见完整命盘。"
    )

    model = _build_life_identity_card(_chart(), overview)

    assert model["summary"] == "丙火日主中和 · 比劫格局，整体节奏稳中有进。"
    assert "1990-01-01" not in model["summary"]


def test_identity_card_does_not_label_a_balanced_element_as_dominant():
    from ui.life_overview_page import _build_life_identity_card

    model = _build_life_identity_card(
        _chart(element_scores={"木": 2, "火": 2, "土": 2, "金": 2, "水": 2}),
        _overview(),
    )

    assert model["dominant_elements"] == []
    assert model["term_ids"] == ["day-master", "day-element-fire", "strength", "pattern"]


@pytest.mark.parametrize(
    ("day_master", "day_element", "pattern_class"),
    [
        ("甲", "木", "ms-identity-pattern-wood"),
        ("丙", "火", "ms-identity-pattern-fire"),
        ("戊", "土", "ms-identity-pattern-earth"),
        ("庚", "金", "ms-identity-pattern-metal"),
        ("壬", "水", "ms-identity-pattern-water"),
    ],
)
def test_each_day_element_has_text_and_a_distinct_pattern(
    monkeypatch, day_master, day_element, pattern_class
):
    import ui.life_overview_page as page

    rendered: list[str] = []
    monkeypatch.setattr(
        page.st,
        "markdown",
        lambda body, **_kwargs: rendered.append(str(body)),
    )
    model = page._build_life_identity_card(
        _chart(
            day_master,
            element_scores={"木": 0, "火": 0, "土": 0, "金": 0, "水": 0, day_element: 6},
        ),
        _overview(),
    )

    page._render_life_identity_card(model)

    html = "\n".join(rendered)
    assert f">{day_element}日主<" in html
    assert pattern_class in html
    assert f"{day_element}偏旺" in html
    assert "🌳" not in html and "🔥" not in html and "💧" not in html


def test_identity_card_replaces_the_old_parallel_tag_path_and_has_mobile_css():
    page_source = PAGE_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    assert "ms-life-tag" not in page_source
    for token in [
        "ms-life-identity-card",
        "ms-life-core-mark",
        "ms-life-strength-scale",
        "ms-life-dominant-elements",
        "ms-life-pattern-line",
    ]:
        assert token in page_source
        assert f".{token}" in styles
    for pattern in ["wood", "fire", "earth", "metal", "water"]:
        assert f".ms-identity-pattern-{pattern}" in styles
    assert "@media (max-width: 768px)" in styles
    assert "grid-template-columns: 1fr" in styles
    assert "ms-product-celestial-canvas" in styles
    assert "linear-gradient" in styles
