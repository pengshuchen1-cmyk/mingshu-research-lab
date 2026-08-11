from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ui_uses_current_streamlit_iframe_api_only():
    ui_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "ui").glob("*.py"))
    )

    assert "streamlit.components.v1" not in ui_sources
    assert "components.html(" not in ui_sources
    assert ui_sources.count("st.iframe(") == 6
    assert "build_helix_background_script" in ui_sources
