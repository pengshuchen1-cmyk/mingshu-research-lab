"""公网启动前阻断数据库、日志与备份文件进入发布目录。"""

from __future__ import annotations

from pathlib import Path


def find_private_release_artifacts(root: str | Path) -> list[Path]:
    base = Path(root)
    candidates: list[Path] = []
    data_dir = base / "data"
    if data_dir.exists():
        candidates.extend(path for path in data_dir.rglob("*.db") if path.is_file())
        candidates.extend(path for path in data_dir.rglob("*backup*") if path.is_file())
    logs_dir = base / "logs"
    if logs_dir.exists():
        candidates.extend(path for path in logs_dir.rglob("*") if path.is_file())
    return sorted(set(candidates))


def assert_public_release_safe(root: str | Path) -> None:
    found = find_private_release_artifacts(root)
    if found:
        relative = "、".join(str(path.relative_to(Path(root))) for path in found[:8])
        raise RuntimeError(f"公网发布目录发现隐私文件：{relative}")
