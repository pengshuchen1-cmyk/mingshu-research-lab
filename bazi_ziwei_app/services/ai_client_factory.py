"""Select the configured cloud AI adapter."""

from __future__ import annotations

from core.ai_models import AIConfig
from services.ai_service_errors import AIServiceError
from services.kimi_bazi_client import KimiBaziClient
from services.openai_bazi_client import OpenAIBaziClient


def build_ai_client(config: AIConfig) -> object:
    if config.provider == "kimi":
        return KimiBaziClient(config)
    if config.provider == "openai":
        return OpenAIBaziClient(config)
    raise AIServiceError("service_unavailable")
