from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editorial_tokens_and_accessibility_rules_exist():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for token in [
        "--cc-primary: #DCEDE5",
        "--cc-primary-foreground: #174E3C",
        "--cc-background: #f5f5f7",
        "--cc-card: #FFFFFF",
        "--cc-foreground: #111111",
        "--cc-muted-foreground: #71717a",
        "--cc-border: rgba(0, 0, 0, .08)",
        "--cc-font-sm: 13px",
        "--cc-font-base: 17px",
        "--cc-font-lg: 24px",
        "'Noto Serif SC'",
        "'Noto Sans SC'",
        "min-height: 44px",
        ":focus-visible",
        "prefers-reduced-motion: reduce",
        "@media (max-width: 640px)",
    ]:
        assert token in css
    assert "ms-product-celestial-canvas" not in css
    assert "color-scheme: light" in css
    assert "border-radius: var(--cc-radius-card) !important" in css


def test_chunui_ssot_rejects_generated_dark_cinematic_direction():
    master = (ROOT / "design-system" / "chunui" / "MASTER.md").read_text(encoding="utf-8")

    assert "本项目 ChunUI 视觉实现的唯一规范" in master
    assert "#dcede5" in master
    assert "#174e3c" in master
    assert "#ff0a78" not in master.lower()
    assert "13 / 17 / 24px" in master
    assert "持续动画" in master
    assert "dark mode, cinematic" not in master


def test_hidden_sidebar_fallback_expands_and_indicates_focus():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for selector in [
        'section[data-testid="stSidebar"]:focus-within',
        'section[data-testid="stSidebar"] div[role="radiogroup"] label:focus-within',
        'section[data-testid="stSidebar"] div[role="radiogroup"] input:focus-visible',
    ]:
        assert selector in css


def test_existing_ziwei_bazi_and_luck_classes_have_theme_compatibility_rules():
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


def test_existing_life_report_bazi_and_ziwei_classes_have_theme_compatibility_rules():
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
