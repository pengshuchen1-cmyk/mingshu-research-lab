from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _write_manifest(manifest_path: Path, rule_path: str) -> None:
    manifest_path.write_text(
        json.dumps({"files": [{"path": rule_path, "sha256": "stale"}]}),
        encoding="utf-8",
    )


def test_rebuild_manifest_hashes_relative_regular_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from tools import rebuild_bazi_rule_manifest as rebuild

    manifest_dir = tmp_path / "rules"
    manifest_dir.mkdir()
    rule = manifest_dir / "safe.json"
    rule.write_text('{"rules": []}\n', encoding="utf-8")
    manifest = manifest_dir / "manifest.json"
    _write_manifest(manifest, "safe.json")
    monkeypatch.setattr(rebuild, "MANIFEST", manifest)

    rebuild.main()

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    expected = hashlib.sha256(rule.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert payload["files"][0]["sha256"] == expected


def test_rebuild_manifest_normalizes_crlf_before_hashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from tools import rebuild_bazi_rule_manifest as rebuild

    manifest_dir = tmp_path / "rules"
    manifest_dir.mkdir()
    rule = manifest_dir / "safe.json"
    rule.write_bytes(b'{"rules": []}\r\n')
    manifest = manifest_dir / "manifest.json"
    _write_manifest(manifest, "safe.json")
    monkeypatch.setattr(rebuild, "MANIFEST", manifest)

    rebuild.main()

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["files"][0]["sha256"] == hashlib.sha256(b'{"rules": []}\n').hexdigest()


def test_rule_pack_json_is_forced_to_lf_by_git_attributes():
    repository_root = Path(__file__).resolve().parents[2]
    attributes = (repository_root / ".gitattributes").read_text(encoding="utf-8").splitlines()

    assert "bazi_ziwei_app/rules/bazi_skill/*.json text eol=lf" in attributes


@pytest.mark.parametrize("rule_path", ("/absolute.json", "../outside.json", "directory"))
def test_rebuild_manifest_rejects_nonlocal_or_nonfile_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rule_path: str,
):
    from tools import rebuild_bazi_rule_manifest as rebuild

    manifest_dir = tmp_path / "rules"
    manifest_dir.mkdir()
    (manifest_dir / "directory").mkdir()
    manifest = manifest_dir / "manifest.json"
    _write_manifest(manifest, rule_path)
    monkeypatch.setattr(rebuild, "MANIFEST", manifest)

    with pytest.raises(ValueError, match="rule file"):
        rebuild.main()


def test_rebuild_manifest_rejects_symlink_that_resolves_outside_manifest_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from tools import rebuild_bazi_rule_manifest as rebuild

    manifest_dir = tmp_path / "rules"
    manifest_dir.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"rules": []}\n', encoding="utf-8")
    (manifest_dir / "linked.json").symlink_to(outside)
    manifest = manifest_dir / "manifest.json"
    _write_manifest(manifest, "linked.json")
    monkeypatch.setattr(rebuild, "MANIFEST", manifest)

    with pytest.raises(ValueError, match="rule file"):
        rebuild.main()
