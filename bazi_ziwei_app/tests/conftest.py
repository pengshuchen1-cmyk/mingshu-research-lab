"""测试默认模拟本机开发模式；公网测试会在单例内显式切换。"""

import pytest


@pytest.fixture(autouse=True)
def _local_runtime_by_default(monkeypatch):
    monkeypatch.setenv("MINGSHU_RUNTIME_MODE", "local")


@pytest.fixture(autouse=True)
def _isolated_ai_request_controller_registry():
    from core import ai_request_control

    with ai_request_control._CONTROLLER_REGISTRY_LOCK:
        ai_request_control._CONTROLLER_REGISTRY.clear()
    yield
    with ai_request_control._CONTROLLER_REGISTRY_LOCK:
        ai_request_control._CONTROLLER_REGISTRY.clear()
