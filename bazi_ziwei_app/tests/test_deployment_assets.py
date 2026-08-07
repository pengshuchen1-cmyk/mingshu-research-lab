from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_docker_assets_keep_private_data_out_and_healthcheck_in():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "USER mingshu" in dockerfile
    assert "MINGSHU_RUNTIME_MODE=public" in dockerfile
    assert "/_stcore/health" in dockerfile
    assert "/_stcore/health" in compose
    for pattern in (".venv", "data/*.db", "logs/", ".env"):
        assert pattern in dockerignore
    assert '"8501:8501"' not in compose


def test_linux_container_installs_and_registers_chinese_pdf_font():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    export_report = (ROOT / "report" / "export_report.py").read_text(encoding="utf-8")
    compatibility_report = (ROOT / "report" / "compatibility_report.py").read_text(encoding="utf-8")

    assert "fonts-droid-fallback" in dockerfile
    font_path = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
    assert font_path in export_report
    assert font_path in compatibility_report


def test_public_privacy_copy_describes_server_side_processing():
    profile_form = (ROOT / "ui" / "profile_form.py").read_text(encoding="utf-8")
    privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")

    assert "传至本站服务器内存" in profile_form
    assert "不写入公网命盘数据库" in profile_form
    assert "传至本站服务器内存" in privacy


def test_mainland_filing_numbers_are_configurable_and_rendered_in_footer():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")

    for setting in ("MINGSHU_ICP_NUMBER", "MINGSHU_PUBLIC_SECURITY_NUMBER"):
        assert setting in compose
        assert setting in env_example
        assert setting in app
    assert "https://beian.miit.gov.cn/" in app
    assert "https://beian.mps.gov.cn/" in app
    assert "render_compliance_footer()" in app
