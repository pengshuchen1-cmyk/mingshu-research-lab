"""检查命数研究室运行环境。"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from types import ModuleType

INSTALL_HINT = "请先运行：python -m pip install -r requirements.txt"


def check_dependencies(importer: Callable[[str], ModuleType] = importlib.import_module) -> tuple[bool, list[str]]:
    """
    检查程序运行所需依赖是否可导入。
    """
    messages: list[str] = []

    for package_name, display_name in [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
    ]:
        try:
            importer(package_name)
        except Exception:
            messages.append(f"{display_name} 未安装或不可导入。")

    try:
        lunar_python = importer("lunar_python")
        if not hasattr(lunar_python, "Solar"):
            raise ImportError("Solar 不存在")
    except Exception:
        messages.append("lunar_python 未安装或不可导入，无法使用 Solar。")

    if messages:
        messages.append(INSTALL_HINT)
        return False, messages
    return True, ["环境检查通过"]


def main() -> int:
    """
    执行环境检查并输出中文提示。
    """
    ok, messages = check_dependencies()
    for message in messages:
        print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
