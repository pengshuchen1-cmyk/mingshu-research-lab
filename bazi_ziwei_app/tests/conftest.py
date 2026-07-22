"""测试默认模拟本机开发模式；公网测试会在单例内显式切换。"""

import pytest


@pytest.fixture(autouse=True)
def _local_runtime_by_default(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "local")
