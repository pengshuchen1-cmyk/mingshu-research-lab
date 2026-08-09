from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editorial_tokens_and_accessibility_rules_exist():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for token in [
        "--ms-surface: #FAFAFA",
        "--ms-panel: #FFFFFF",
        "--ms-ink: #18181B",
        "--ms-action: #BE185D",
        "'Noto Serif SC'",
        "'Noto Sans SC'",
        "min-height: 44px",
        ":focus-visible",
        "prefers-reduced-motion: reduce",
        "@media (max-width: 640px)",
    ]:
        assert token in css
    for forbidden in ["#05080A", "#D8B96A", "linear-gradient"]:
        assert forbidden not in css
    assert "border-radius: var(--ms-radius) !important" in css


def test_hidden_sidebar_fallback_expands_and_indicates_focus():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for selector in [
        'section[data-testid="stSidebar"]:focus-within',
        'section[data-testid="stSidebar"] div[role="radiogroup"] label:focus-within',
        'section[data-testid="stSidebar"] div[role="radiogroup"] input:focus-visible',
    ]:
        assert selector in css


def test_existing_ziwei_bazi_and_luck_classes_have_light_compatibility_rules():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for selector in [
        ".zw-hero",
        ".zw-hero-card",
        ".zw-star-chip",
        ".zw-tag",
        ".zw-keyword",
        ".ms-luck-stage-head",
        ".ms-luck-stage-pillar",
    ]:
        assert selector in css


def test_existing_life_report_bazi_and_ziwei_classes_have_light_compatibility_rules():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for selector in [
        ".ms-life-summary-title",
        ".ms-life-summary-text",
        ".ms-life-score-value",
        ".ms-life-score-level",
        ".ms-report-text",
        ".ms-month-card-head",
        ".ms-bazi-section",
        ".ms-bazi-risk",
        ".zw-boundary",
        ".zw-triangle-muted",
    ]:
        assert selector in css


def test_selectbox_styles_target_the_react_aria_shell_without_double_border():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert '.stSelectbox div[role="group"] {' in css
    assert '.stSelectbox input[role="combobox"] {' in css
    assert 'input:not([role="combobox"]), textarea' in css
    assert 'border: 0 !important;' in css.split(
        '.stSelectbox input[role="combobox"] {', 1
    )[1].split("}", 1)[0]
    assert 'div:has(> [role="listbox"]) {' in css
    assert '[role="listbox"] [role="option"][aria-selected="true"]' in css
