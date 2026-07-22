"""四柱矩阵与五行分布展示组件测试。"""

from __future__ import annotations

import math

from core.bazi_engine import build_bazi_chart


def _sample_chart() -> dict:
    chart = build_bazi_chart(
        {
            "name": "图形样例",
            "gender": "男",
            "birth_date": "1990-01-01",
            "birth_hour": 10,
            "birth_minute": 0,
            "birth_place": "上海",
            "use_solar_time": False,
        }
    )
    assert "error" not in chart
    return chart


def test_four_pillars_view_uses_fixed_order_and_complete_text_fields():
    from ui.chart_visual_components import build_four_pillars_view

    pillars = build_four_pillars_view(_sample_chart())

    assert [pillar["label"] for pillar in pillars] == ["年柱", "月柱", "日柱", "时柱"]
    for pillar in pillars:
        assert pillar["stem"]
        assert pillar["branch"]
        assert pillar["stem_element"] in "木火土金水"
        assert pillar["branch_element"] in "木火土金水"
        assert isinstance(pillar["ten_god"], str)
        assert isinstance(pillar["hidden_stems"], list)


def test_four_pillars_view_preserves_real_xun_kong_values():
    from ui.chart_visual_components import build_four_pillars_view

    chart = _sample_chart()
    pillars = build_four_pillars_view(chart)

    assert [pillar["xun_kong"] for pillar in pillars] == [
        chart["pillars"][key]["xun_kong"]
        for key in ["year", "month", "day", "hour"]
    ]


def test_four_pillars_view_safely_adapts_string_pillars_and_mixed_hidden_stems():
    from ui.chart_visual_components import build_four_pillars_view

    chart = {
        "day_master": "丙",
        "pillars": {
            "year": "甲子",
            "month": {"pillar": "乙丑"},
            "day": {"gan": "丙", "zhi": "寅"},
            "hour": {"heavenly_stem": "丁", "earthly_branch": "卯"},
        },
        "ten_gods": {"year": "偏印", "month": {"gan": "正印"}},
        "hidden_stems": {
            "year": ["癸"],
            "month": [{"stem": "己", "ten_god": "伤官"}],
        },
    }

    pillars = build_four_pillars_view(chart)

    assert [(item["stem"], item["branch"]) for item in pillars] == [
        ("甲", "子"),
        ("乙", "丑"),
        ("丙", "寅"),
        ("丁", "卯"),
    ]
    assert pillars[0]["hidden_stems"][0]["stem"] == "癸"
    assert pillars[1]["hidden_stems"][0]["ten_god"] == "伤官"


def test_element_distribution_has_fixed_order_non_negative_values_and_text_levels():
    from ui.chart_visual_components import build_element_distribution

    distribution = build_element_distribution(_sample_chart())

    assert [item["element"] for item in distribution] == list("木火土金水")
    assert all(item["value"] >= 0 for item in distribution)
    assert all(item["percentage"] >= 0 for item in distribution)
    assert all(item["level"] in {"偏旺", "中等", "偏弱"} for item in distribution)


def test_element_distribution_clamps_invalid_or_negative_display_values():
    from ui.chart_visual_components import build_element_distribution

    distribution = build_element_distribution(
        {"five_elements": {"木": -2, "火": "3.5", "土": None, "金": "bad"}}
    )

    assert [item["value"] for item in distribution] == [0.0, 3.5, 0.0, 0.0, 0.0]


def test_element_distribution_rejects_non_finite_values():
    from ui.chart_visual_components import build_element_distribution

    distribution = build_element_distribution(
        {"five_elements": {"木": float("inf"), "火": float("-inf"), "土": float("nan"), "金": 2}}
    )

    assert [item["value"] for item in distribution] == [0.0, 0.0, 0.0, 2.0, 0.0]
    assert all(math.isfinite(item["percentage"]) for item in distribution)


def test_renderers_output_text_labels_and_horizontal_bars(monkeypatch):
    import ui.chart_visual_components as components

    rendered: list[str] = []
    monkeypatch.setattr(
        components.st,
        "markdown",
        lambda body, **_kwargs: rendered.append(str(body)),
    )

    chart = _sample_chart()
    components.render_four_pillars_matrix(chart)
    components.render_element_distribution(chart)
    html = "\n".join(rendered)

    for label in ["年柱", "月柱", "日柱", "时柱", "木", "火", "土", "金", "水"]:
        assert label in html
    assert "ms4-four-pillars" in html
    assert "ms4-element-bar" in html
    assert "width:" in html
    assert "radar" not in html.lower()


def test_four_pillars_renderer_keeps_cards_when_optional_helper_rows_are_absent(monkeypatch):
    import ui.chart_visual_components as components

    rendered: list[str] = []
    monkeypatch.setattr(
        components.st,
        "markdown",
        lambda body, **_kwargs: rendered.append(str(body)),
    )
    chart = {
        "pillars": {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        }
    }

    components.render_four_pillars_matrix(chart)
    html = "\n".join(rendered)

    assert html.count('class="ms4-pillar-card"') == 4
    for label in ["年柱", "月柱", "日柱", "时柱"]:
        assert label in html


def test_four_pillars_renderer_shows_xun_kong_and_escapes_untrusted_fields(monkeypatch):
    import ui.chart_visual_components as components

    rendered: list[str] = []
    monkeypatch.setattr(
        components.st,
        "markdown",
        lambda body, **_kwargs: rendered.append(str(body)),
    )
    chart = {
        "pillars": {
            "year": {
                "name": '<img src=x onerror="boom">',
                "pillar": "甲子",
                "na_yin": "<b>海中金</b>",
                "xun_kong": "<script>戌亥</script>",
                "di_shi": "沐浴<script>",
                "ten_god": "<i>偏印</i>",
            },
            "month": {"pillar": "乙丑", "void": "申酉"},
            "day": "丙寅",
            "hour": "丁卯",
        },
        "hidden_stems": {
            "year": [{"stem": "癸", "ten_god": "<em>正印</em>"}],
        },
    }

    view = components.build_four_pillars_view(chart)
    assert view[0]["xun_kong"] == "<script>戌亥</script>"
    assert view[1]["xun_kong"] == "申酉"

    components.render_four_pillars_matrix(chart)
    html = "\n".join(rendered)

    assert "旬空 &lt;script&gt;戌亥&lt;/script&gt;" in html
    assert "旬空 申酉" in html
    for unsafe in ["<img", "<script>", "<b>", "<i>", "<em>"]:
        assert unsafe not in html


def test_mobile_four_pillars_keeps_four_readable_columns_in_a_local_scroller():
    from pathlib import Path

    css = (Path(__file__).resolve().parents[1] / "ui" / "styles.py").read_text(
        encoding="utf-8"
    )
    matrix_rule = css.split(".ms4-four-pillars {", 1)[1].split("}", 1)[0]
    assert "grid-template-columns: repeat(4, minmax(150px, 1fr))" in matrix_rule
    assert "overflow-x: auto" in matrix_rule
    assert "max-width: 100%" in matrix_rule
    assert "overscroll-behavior-inline: contain" in matrix_rule

    chart_section_rule = css.split(".ms4-chart-section {", 1)[1].split("}", 1)[0]
    assert "max-width: 100%" in chart_section_rule
    assert "overflow: hidden" in chart_section_rule

    mobile_css = css.split("@media (max-width: 768px)", 1)[1]
    assert ".ms4-four-pillars { grid-template-columns: repeat(2" not in mobile_css
    assert ".ms4-four-pillars { grid-template-columns: 1fr" not in mobile_css
    phone_css = mobile_css.split("@media (max-width: 480px)", 1)[1]
    assert ".ms4-pillar-helper { display: none; }" in phone_css
