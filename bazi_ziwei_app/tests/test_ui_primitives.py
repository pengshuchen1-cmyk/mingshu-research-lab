from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_native_primitives_cover_reusable_shadcn_style_roles():
    source = (ROOT / "ui" / "primitives.py").read_text(encoding="utf-8")

    for function_name in [
        "card",
        "badge",
        "page_header",
        "section_header",
        "callout",
        "metric_card",
        "empty_state_header",
    ]:
        assert f"def {function_name}(" in source

    assert "st.container(" in source
    assert "border=True" in source
    assert "streamlit_shadcn_ui" not in source
    assert "st.iframe" not in source


def test_global_theme_styles_native_components_consistently():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    for selector in [
        '[class*="st-key-ms-ui-card-"]',
        ".ms-ui-page-header",
        ".ms-ui-section-header",
        ".ms-ui-badge",
        ".ms-ui-callout",
        ".ms-ui-metric",
        'div[data-testid="stTabs"] [data-baseweb="tab-list"]',
        'div[data-testid="stAlert"]',
        'div[data-testid="stForm"]',
    ]:
        assert selector in css

    assert "--ms-radius: 12px" in css
    assert "--ms-radius-small: 8px" in css
    assert "--ms-shadow-raised" in css


def test_core_pages_use_shared_page_and_content_primitives():
    files = {
        "life_overview_page.py": ("page_header", "section_header", "empty_state_header"),
        "report_page.py": ("page_header", "section_header", "empty_state_header"),
        "profile_form.py": ("page_header",),
        "privacy_center_page.py": ("page_header", "section_header", "card", "callout", "metric_card"),
        "archive_page.py": ("page_header", "section_header", "card", "empty_state_header"),
    }

    for filename, primitives in files.items():
        source = (ROOT / "ui" / filename).read_text(encoding="utf-8")
        for primitive in primitives:
            assert primitive in source
