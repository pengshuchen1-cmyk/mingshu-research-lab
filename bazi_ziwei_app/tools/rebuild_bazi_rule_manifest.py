#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rules" / "bazi_skill" / "manifest.json"


def _resolve_rule_file(manifest_dir: Path, relative_path: object) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("manifest rule file path is required")

    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts:
        raise ValueError("manifest rule file must stay inside manifest directory")

    target = (manifest_dir / requested).resolve()
    if manifest_dir not in target.parents:
        raise ValueError("manifest rule file must stay inside manifest directory")
    if not target.is_file():
        raise ValueError("manifest rule file must be a regular file")
    return target


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_dir = MANIFEST.parent.resolve()
    for item in payload["files"]:
        path = _resolve_rule_file(manifest_dir, item["path"])
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
