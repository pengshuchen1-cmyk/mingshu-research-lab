from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editorial_tokens_and_accessibility_rules_exist():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for token in [
        "--ms-surface: #FAFAFA",
        "--ms-ink: #18181B",
        "--ms-action: #EC4899",
        "'Noto Serif SC'",
        "'Noto Sans SC'",
        "min-height: 44px",
        ":focus-visible",
        "prefers-reduced-motion: reduce",
        "@media (max-width: 640px)",
    ]:
        assert token in css
    for forbidden in ["#05080A", "#D8B96A", "linear-gradient", "border-radius: 999px"]:
        assert forbidden not in css


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
