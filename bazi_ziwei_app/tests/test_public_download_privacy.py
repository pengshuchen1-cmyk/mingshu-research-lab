def test_public_report_filenames_never_contain_name_or_birth_data(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "public")
    from ui.report_page import _safe_filename as report_filename
    from ui.special_reports_page import _safe_filename as special_filename

    for filename in (
        report_filename("金丝雀姓名_1990-01-01", "pdf"),
        special_filename("金丝雀姓名_1990-01-01", "事业专项", "md"),
    ):
        assert "金丝雀姓名" not in filename
        assert "1990" not in filename
        assert filename.startswith("命数研究室_个人报告")
