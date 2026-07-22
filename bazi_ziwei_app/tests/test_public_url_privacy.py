from pathlib import Path


def test_application_never_places_birth_data_in_url_or_query_parameters():
    root = Path(__file__).resolve().parents[1]
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [root / "app.py", root / "ui" / "profile_form.py", root / "ui" / "report_page.py"]
    )
    for forbidden in ("st.query_params", "experimental_set_query_params", "experimental_get_query_params"):
        assert forbidden not in sources
