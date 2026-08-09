from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_guidance_is_conclusion_first_and_no_chart_required():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")

    for token in [
        "def _render_public_guidance_hero",
        "def _render_guidance_details",
        "今日重点",
        "今日提醒",
        'with st.expander("依据与边界")',
    ]:
        assert token in source

    render_body = source.split("def render_yearly_page", 1)[1]
    assert render_body.index("_render_public_guidance_hero") < render_body.index(
        'chart = st.session_state.get("current_chart")'
    )
    assert "无需出生资料" in source


def test_personal_yearly_analysis_uses_editorial_overview_and_insight_cards():
    source = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")
    for token in [
        "def _render_year_overview",
        "def _render_risk_action_cards",
        "ms3-year-cover",
        "ms3-year-metrics",
        "ms3-insight-card",
        "主要风险",
        "优先行动",
        "行动边界",
    ]:
        assert token in source


def test_personal_overview_leads_with_plain_summary_and_next_action():
    source = (ROOT / "ui" / "life_overview_page.py").read_text(encoding="utf-8")
    for token in ["个人摘要", "下一步建议", "尚未建立个人命盘"]:
        assert token in source

    for hidden_copy in [
        "**参考**",
        "同一套分数同时呈现等级与白话简评，避免重复评分。",
    ]:
        assert hidden_copy not in source

    for preserved_copy in ["命理依据", "**判断依据**", "medical_disclaimer"]:
        assert preserved_copy in source

    assert 'st.container(key="ms-life-overview")' in source
    assert 'st.container(key="ms-life-next-actions")' in source


def test_personal_overview_uses_chart_visuals_and_one_five_dimension_section():
    source = (ROOT / "ui" / "life_overview_page.py").read_text(encoding="utf-8")

    for token in [
        "render_four_pillars_matrix(chart)",
        "render_element_distribution(chart)",
        "五维洞察",
        "财富",
        "关系",
        "健康",
        "事业",
        "整体平衡",
        "查看详情",
        "优势",
        "隐患",
        "行动建议",
    ]:
        assert token in source

    for obsolete in ["四维简评", "五维评分", "st.columns(4)", "st.columns(5)"]:
        assert obsolete not in source


def test_report_starts_with_summary_before_export_controls():
    source = (ROOT / "ui" / "report_page.py").read_text(encoding="utf-8")
    assert "def _render_report_summary" in source
    assert "报告摘要" in source
    assert source.index("_render_report_summary") < source.index("st.download_button")
    assert "报告名片预览" in source


def test_archive_has_local_privacy_empty_state_and_destructive_copy():
    source = (ROOT / "ui" / "archive_page.py").read_text(encoding="utf-8")
    for token in ["def _render_archive_empty_state", "数据仅保存在本机", "删除命盘", "确认删除"]:
        assert token in source
