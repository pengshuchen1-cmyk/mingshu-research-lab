from pathlib import Path

import pytest


def test_public_release_scanner_rejects_database_logs_and_private_exports(tmp_path):
    from utils.release_privacy import assert_public_release_safe

    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "profiles.db").write_bytes(b"private")
    with pytest.raises(RuntimeError, match="隐私文件"):
        assert_public_release_safe(tmp_path)

    (tmp_path / "data" / "profiles.db").unlink()
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "app.log").write_text("private", encoding="utf-8")
    with pytest.raises(RuntimeError, match="隐私文件"):
        assert_public_release_safe(tmp_path)


def test_repository_ignore_rules_cover_private_artifacts():
    root = Path(__file__).resolve().parents[1]
    ignore = (root / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("data/*.db", "data/*backup*.db", "logs/", "*.log"):
        assert pattern in ignore


def test_privacy_policy_exists_and_explains_session_only_processing():
    root = Path(__file__).resolve().parents[1]
    policy = (root / "PRIVACY.md").read_text(encoding="utf-8")
    for text in ("仅本次会话", "30 分钟", "立即清除", "不写入", "称呼"):
        assert text in policy
