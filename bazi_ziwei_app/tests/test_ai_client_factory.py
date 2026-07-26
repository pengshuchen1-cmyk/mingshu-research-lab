from __future__ import annotations

import pytest


def test_factory_selects_kimi_by_default():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.kimi_bazi_client import KimiBaziClient

    client = build_ai_client(AIConfig("key", True))

    assert isinstance(client, KimiBaziClient)


def test_factory_keeps_openai_available():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.openai_bazi_client import OpenAIBaziClient

    client = build_ai_client(
        AIConfig(
            "key",
            True,
            "gpt-5.6-sol",
            "medium",
            30,
            "openai",
            "https://api.openai.com/v1",
        )
    )

    assert isinstance(client, OpenAIBaziClient)


def test_factory_rejects_unknown_provider_without_external_call():
    from core.ai_models import AIConfig
    from services.ai_client_factory import build_ai_client
    from services.ai_service_errors import AIServiceError

    with pytest.raises(AIServiceError) as captured:
        build_ai_client(AIConfig("key", True, provider="unknown"))

    assert captured.value.code == "service_unavailable"
