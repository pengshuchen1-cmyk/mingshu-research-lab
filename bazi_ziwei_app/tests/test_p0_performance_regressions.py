from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import mock_open


def _chart(fingerprint: str = "chart-a") -> dict:
    return {
        "chart_fingerprint_v2": fingerprint,
        "day_master": "甲",
        "profile": {"gender": "男"},
        "pillars": {
            "year": {"pillar": "甲子"},
            "month": {"pillar": "乙丑"},
            "day": {"pillar": "丙寅"},
            "hour": {"pillar": "丁卯"},
        },
        "day_master_strength": {
            "strength": "中和",
            "favorable_elements": ["木", "水"],
            "unfavorable_elements": ["金"],
        },
    }


def test_year_analysis_is_built_once_per_chart_year_and_version(monkeypatch):
    import utils.analysis_session_cache as cache

    calls = {"monthly": 0, "yearly": 0, "events": 0}
    monthly = [{"month": 1}]
    yearly = {"year": 2026}
    events = [{"month": 1, "top_events": []}]

    def build_monthly(chart, year):
        calls["monthly"] += 1
        return monthly

    def build_yearly(chart, year, luck_data, *, monthly_data):
        calls["yearly"] += 1
        assert monthly_data is monthly
        return {**yearly, "year": year}

    def build_events(chart, monthly_data, yearly_data, luck_data):
        calls["events"] += 1
        assert monthly_data is monthly
        return events

    monkeypatch.setattr(cache, "analyze_monthly_fortune", build_monthly)
    monkeypatch.setattr(cache, "analyze_yearly_fortune", build_yearly)
    monkeypatch.setattr(cache, "build_year_monthly_event_results", build_events)

    state = {}
    first = cache.get_or_build_year_analysis(
        state, _chart(), 2026, {"available": True}, version="rules-v1"
    )
    second = cache.get_or_build_year_analysis(
        state, _chart(), 2026, {"available": True}, version="rules-v1"
    )

    assert first == second
    assert calls == {"monthly": 1, "yearly": 1, "events": 1}

    cache.get_or_build_year_analysis(
        state, _chart(), 2027, {"available": True}, version="rules-v1"
    )
    assert calls == {"monthly": 2, "yearly": 2, "events": 2}

    cache.get_or_build_year_analysis(
        state, _chart(), 2027, {"available": True}, version="rules-v2"
    )
    cache.get_or_build_year_analysis(
        state, _chart("chart-b"), 2027, {"available": True}, version="rules-v2"
    )
    cache.get_or_build_year_analysis(
        state,
        _chart("chart-b"),
        2027,
        {
            "available": True,
            "dayun_list": [
                {
                    "pillar": "甲子",
                    "start_year": 2020,
                    "end_year": 2029,
                    "start_date": "2020-02-01",
                }
            ],
        },
        version="rules-v2",
    )
    assert calls == {"monthly": 5, "yearly": 5, "events": 5}


def test_fallback_analysis_fingerprint_excludes_profile_identity():
    from utils.analysis_session_cache import chart_analysis_fingerprint

    left = _chart("")
    right = _chart("")
    left["profile"].update({"name": "测试甲", "birth_date": "1990-01-01"})
    right["profile"].update({"name": "测试乙", "birth_date": "2000-12-31"})

    assert chart_analysis_fingerprint(left) == chart_analysis_fingerprint(right)

    right["pillars"]["hour"]["pillar"] = "戊辰"
    assert chart_analysis_fingerprint(left) != chart_analysis_fingerprint(right)


def test_yearly_analysis_reuses_supplied_month_data(monkeypatch):
    import core.monthly_engine as monthly_engine
    from core.yearly_engine import analyze_yearly_fortune

    def fail_if_called(*args, **kwargs):
        raise AssertionError("monthly analysis must not be rebuilt")

    monkeypatch.setattr(monthly_engine, "analyze_monthly_fortune", fail_if_called)

    result = analyze_yearly_fortune(
        _chart(),
        2026,
        monthly_data=[
            {
                "month_name": "正月",
                "pillar": "庚寅",
                "relation_to_favorable": "喜用相关",
                "branch_relations": [],
                "ten_god": "正官",
                "month": 1,
            }
        ],
    )

    assert result["year"] == 2026
    assert result["opportunity_months"] == ["正月（庚寅）"]


def test_luck_year_summary_skips_unused_monthly_analysis(monkeypatch):
    import core.luck_engine as luck_engine

    calls = []

    def build_year(chart, year, *, include_monthly_analysis):
        calls.append((year, include_monthly_analysis))
        return {"year": year}

    monkeypatch.setattr(luck_engine, "analyze_yearly_fortune", build_year)
    result = luck_engine._build_yearly_list(_chart(), years=3)

    assert len(result) == 3
    assert calls and all(include_monthly is False for _, include_monthly in calls)


def test_ai_dayun_resolution_skips_unused_year_summaries(monkeypatch):
    import core.ai_orchestrator as orchestrator

    captured = {}

    def get_luck(profile, chart, *, include_yearly_list):
        captured["include_yearly_list"] = include_yearly_list
        return {"available": True, "dayun_list": [{"pillar": "甲子"}]}

    monkeypatch.setattr(orchestrator, "get_luck_cycles", get_luck)
    periods = orchestrator._resolved_dayun_periods(
        _chart(), SimpleNamespace(time_scope="year")
    )

    assert periods == [{"pillar": "甲子"}]
    assert captured["include_yearly_list"] is False


def test_activation_assets_are_loaded_once_and_force_can_refresh(monkeypatch):
    import core.monthly_event_activation_bridge as bridge

    opener = mock_open(read_data="{}")
    monkeypatch.setattr("builtins.open", opener)
    monkeypatch.setattr(bridge, "_ACTIVATION_ASSETS_CACHE", None)

    first = bridge.load_activation_assets()
    second = bridge.load_activation_assets()
    assert first is second
    assert opener.call_count == 4

    refreshed = bridge.load_activation_assets(force=True)
    assert refreshed is not first
    assert opener.call_count == 8


def test_full_year_event_results_drop_large_internal_payloads(monkeypatch):
    import core.monthly_event_activation_bridge as bridge
    import core.monthly_event_inference_engine as inference

    raw = {
        "month": 1,
        "top_events": [],
        "bridge_events": [{"large": "payload"}],
        "event_score_map": {"event": 99},
        "month_unique_triggers": {"event": ["trigger"]},
    }
    monkeypatch.setattr(
        bridge, "infer_monthly_likely_events_full", lambda *args, **kwargs: dict(raw)
    )
    monkeypatch.setattr(inference, "postprocess_monthly_events", lambda rows: rows)

    result = bridge.build_year_monthly_event_results({}, [{}])

    assert result == [{"month": 1, "top_events": []}]


def test_report_text_exports_reuse_one_markdown_build(monkeypatch):
    import ui.report_page as report_page

    calls = {"markdown": 0, "text": 0}

    def build_markdown(*args, **kwargs):
        calls["markdown"] += 1
        return "# cached markdown"

    def build_text(*args, markdown_report=None, **kwargs):
        calls["text"] += 1
        assert markdown_report == "# cached markdown"
        return "cached text"

    monkeypatch.setattr(report_page, "build_markdown_report", build_markdown)
    monkeypatch.setattr(report_page, "build_text_report", build_text)

    state = {}
    args = (
        state,
        {"name": "测试"},
        _chart(),
        {"summary": "summary"},
        {"available": True},
        {"year": 2026},
        [{"month": 1}],
        [{"month": 1, "top_events": []}],
    )
    first = report_page._get_or_build_text_exports(*args)
    second = report_page._get_or_build_text_exports(*args)

    assert first == second
    assert calls == {"markdown": 1, "text": 1}
    assert report_page._REPORT_PDF_KEY not in state

    args[1]["name"] = "另一个测试名"
    report_page._get_or_build_text_exports(*args)
    assert calls == {"markdown": 2, "text": 2}


def test_text_report_accepts_prebuilt_markdown(monkeypatch):
    import report.export_report as export_report

    monkeypatch.setattr(
        export_report,
        "build_markdown_report",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("markdown must not be rebuilt")
        ),
    )

    result = export_report.build_text_report(
        {}, {}, {}, markdown_report="# 标题\n## 章节\n- 内容"
    )

    assert "标题" in result
    assert "内容" in result


def test_webp_hero_preserves_dimensions_and_is_much_smaller():
    from pathlib import Path

    from PIL import Image

    assets = Path(__file__).resolve().parents[1] / "assets"
    png_path = assets / "hero-sky-v1.png"
    webp_path = assets / "hero-sky-v1.webp"

    with Image.open(png_path) as png, Image.open(webp_path) as webp:
        assert webp.size == png.size
    assert webp_path.stat().st_size < png_path.stat().st_size * 0.15


def test_pdf_generation_is_lazy_and_home_does_not_clear_global_cache():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    report_source = (root / "ui" / "report_page.py").read_text(encoding="utf-8")
    home_source = (root / "ui" / "home.py").read_text(encoding="utf-8")

    button_position = report_source.index('elif st.button("生成 PDF 报告"')
    pdf_build_position = report_source.index("pdf_report = build_pdf_report(")
    assert pdf_build_position > button_position
    assert "st.cache_data.clear()" not in home_source
