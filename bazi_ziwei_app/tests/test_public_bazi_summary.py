from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chart():
    from core.bazi_engine import build_bazi_chart
    from core.luck_engine import get_luck_cycles

    profile = {
        "gender": "女",
        "calendar_type": "solar",
        "birth_date": "1996-09-04",
        "birth_hour": 23,
        "birth_minute": 45,
    }
    chart = build_bazi_chart(profile)
    get_luck_cycles(profile, chart)
    return chart


def test_basic_and_special_reports_expose_same_public_summary():
    from report.bazi_report import generate_basic_bazi_report
    from report.love_report import generate_love_report
    from report.wealth_report import generate_wealth_report

    chart = _chart()
    reports = [
        generate_basic_bazi_report(chart),
        generate_wealth_report(chart),
        generate_love_report(chart, chart["profile"]),
    ]

    for report in reports:
        assert report["public_summary"] == chart["public_summary"]
        assert "算法版本" not in str(report["public_summary"])
        assert "调候依据" not in str(report["public_summary"])


def test_customer_pages_use_shared_rule_summary_and_hide_seasonal_basis():
    components = (ROOT / "ui" / "bazi_components.py").read_text(encoding="utf-8")
    assert "def render_rule_summary" in components
    for filename in ("bazi_page.py", "life_overview_page.py", "report_page.py"):
        source = (ROOT / "ui" / filename).read_text(encoding="utf-8")
        assert "render_rule_summary" in source
        assert "调候依据" not in source
