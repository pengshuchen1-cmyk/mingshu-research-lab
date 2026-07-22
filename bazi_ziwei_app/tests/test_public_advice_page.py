from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_yearly_page_renders_public_advice_before_requiring_a_chart():
    text = (ROOT / "ui" / "yearly_page.py").read_text(encoding="utf-8")

    assert "build_daily_advice" in text
    assert "build_yearly_popular_advice" in text
    assert "def _render_public_guidance_hero" in text
    assert "def _render_guidance_details" in text
    render_body = text.split("def render_yearly_page", maxsplit=1)[1]
    assert render_body.index("_render_public_guidance_hero") < render_body.index(
        'chart = st.session_state.get("current_chart")'
    )
    assert render_body.index("_render_guidance_details") < render_body.index(
        'chart = st.session_state.get("current_chart")'
    )
    assert "无需出生资料" in text
    assert "个人年度分析" in text
