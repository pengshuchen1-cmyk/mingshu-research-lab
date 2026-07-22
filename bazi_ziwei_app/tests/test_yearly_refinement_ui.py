from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _captured_html(monkeypatch, renderer, *args):
    rendered = []

    def capture(body, **kwargs):
        rendered.append(str(body))

    monkeypatch.setattr("ui.yearly_page.st.markdown", capture)
    renderer(*args)
    return "\n".join(rendered)


def test_year_overview_renders_personal_cover_metrics_and_three_keywords(monkeypatch):
    from ui.yearly_page import _render_year_overview

    yearly_data = {
        "pillar": "丙午",
        "ten_god": "正财",
        "relation_to_favorable": "喜用相关",
        "overall_level": "稳中有进",
        "overall_text": "今年适合先稳住资源，再推进重要选择。第二句不应进入封面。",
        "annual_keywords": ["资源整合", "稳步推进", "重要选择", "第四个词"],
    }

    html = _captured_html(
        monkeypatch,
        _render_year_overview,
        {"name": "陈小满"},
        {"day_master": "甲"},
        yearly_data,
        2026,
    )

    for token in [
        "ms3-year-cover",
        "ms3-year-metrics",
        "2026",
        "丙午",
        "陈小满",
        "日主甲",
        "今年适合先稳住资源，再推进重要选择。",
        "资源整合",
        "稳步推进",
        "重要选择",
        "十神",
        "喜忌",
        "年度倾向",
        "白话解释",
    ]:
        assert token in html
    assert "第四个词" not in html


def test_risk_action_cards_use_conclusion_reason_and_action_structure(monkeypatch):
    from ui.yearly_page import _render_risk_action_cards

    yearly_data = {
        "risk_text": "现金流安排容易出现短时压力。",
        "advice_text": "先核对预算，再决定扩张节奏。",
        "relation_to_favorable": "喜忌混杂",
        "overall_level": "先稳后进",
        "suitable_actions": ["整理预算", "核对合同", "保留缓冲", "超量行动"],
        "actions_to_avoid": ["冲动扩张", "口头承诺"],
    }

    html = _captured_html(monkeypatch, _render_risk_action_cards, yearly_data)

    for token in [
        "ms3-insight-grid",
        "ms3-insight-card",
        "主要风险",
        "优先行动",
        "行动边界",
        "结论",
        "为什么",
        "怎么做",
        "适合做",
        "暂缓做",
        "现金流安排容易出现短时压力。",
        "先核对预算，再决定扩张节奏。",
        "整理预算",
        "核对合同",
        "保留缓冲",
        "冲动扩张",
    ]:
        assert token in html
    assert "超量行动" not in html


def test_yearly_dynamic_fields_escape_malicious_html(monkeypatch):
    from ui.yearly_page import _render_risk_action_cards, _render_year_overview

    attack = '<img src=x onerror="alert(1)"><script>bad()</script>'
    overview_html = _captured_html(
        monkeypatch,
        _render_year_overview,
        {"name": attack},
        {"day_master": attack},
        {
            "pillar": attack,
            "ten_god": attack,
            "relation_to_favorable": attack,
            "overall_level": attack,
            "overall_text": f"{attack}。第二句",
            "annual_keywords": [attack],
        },
        2026,
    )
    risk_html = _captured_html(
        monkeypatch,
        _render_risk_action_cards,
        {
            "risk_text": attack,
            "advice_text": attack,
            "relation_to_favorable": attack,
            "overall_level": attack,
            "suitable_actions": [attack],
            "actions_to_avoid": [attack],
        },
    )

    html = overview_html + risk_html
    assert "<img src=x" not in html
    assert "<script>bad()" not in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html
    assert "&lt;script&gt;bad()&lt;/script&gt;" in html


def test_first_sentence_supports_chinese_endings_and_contextual_fallbacks(monkeypatch):
    from ui.yearly_page import _first_sentence, _render_risk_action_cards

    assert _first_sentence("先做核对！再做扩张。", fallback="主题待观察") == "先做核对！"
    assert _first_sentence("信息够不够？再决定。", fallback="主题待观察") == "信息够不够？"
    assert _first_sentence("", fallback="主题待观察") == "主题待观察"

    html = _captured_html(monkeypatch, _render_risk_action_cards, {})
    assert "目前没有突出的年度风险信号，仍需结合现实变化持续观察。" in html
    assert "先处理最明确、可验证的一件事，并为调整保留余量。" in html


def test_yearly_page_removes_legacy_badges_alerts_and_structural_emoji_titles():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")

    for token in [
        "YEARLY FORTUNE · v1.0.6",
        "162 类现实事件覆盖",
        "st.warning(risk_text)",
        "st.info(advice_text)",
        "**✅ 适合做：**",
        "**❌ 不适合做：**",
        "### 🔴 高关注月份",
        "### 🟢 机会月份",
    ]:
        assert token not in source
    assert "_render_year_overview(profile, chart, yearly_data, target_year)" in source
    assert "_render_risk_action_cards(yearly_data)" in source


def test_yearly_page_does_not_repeat_unexplained_legacy_scores_chart():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")

    for obsolete in [
        "render_yearly_scores_chart",
        "年度评分图",
        "### 年度评分",
        "st.altair_chart(fig",
    ]:
        assert obsolete not in source


def test_yearly_css_is_responsive_and_keeps_touch_targets_usable():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    for token in [
        ".ms3-year-cover",
        ".ms3-year-metrics",
        ".ms3-insight-card",
        ".ms3-insight-grid",
        "grid-template-columns: repeat(3, minmax(0, 1fr))",
        "min-height: 44px",
        "@media (max-width: 768px)",
        "grid-template-columns: 1fr",
    ]:
        assert token in css

    number_button_selector = 'div[data-testid="stNumberInput"] button {'
    assert number_button_selector in css
    number_button_rule = css.split(number_button_selector, 1)[1].split("}", 1)[0]
    assert "min-width: 44px" in number_button_rule
    assert "min-height: 44px" in number_button_rule
