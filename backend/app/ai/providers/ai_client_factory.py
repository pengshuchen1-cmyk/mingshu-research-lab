"""Select the configured cloud AI adapter."""

from __future__ import annotations

from ..ai_models import AIConfig
from .ai_service_errors import AIServiceError
from .kimi_bazi_client import KimiBaziClient
from .openai_bazi_client import OpenAIBaziClient


def build_ai_client(config: AIConfig) -> object:
    if config.provider == "kimi":
        return KimiBaziClient(config)
    if config.provider == "openai":
        return OpenAIBaziClient(config)
    raise AIServiceError("service_unavailable")
