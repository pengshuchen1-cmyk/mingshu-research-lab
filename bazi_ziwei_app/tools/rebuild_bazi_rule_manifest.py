#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "rules" / "bazi_skill" / "manifest.json"


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in payload["files"]:
        path = MANIFEST.parent / item["path"]
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
