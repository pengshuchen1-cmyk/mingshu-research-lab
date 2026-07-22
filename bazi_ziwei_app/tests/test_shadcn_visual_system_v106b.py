from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_existing_pages_inherit_editorial_tokens():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    for token in [".ms-card", ".mingshu-report-card", "var(--ms-surface)", "var(--ms-ink)"]:
        assert token in css
