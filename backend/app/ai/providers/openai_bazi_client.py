"""Structured OpenAI Responses API adapter for de-identified Bazi facts."""

from __future__ import annotations

from pydantic import ValidationError

from ..ai_models import (
    AIConfig,
    AIRequestContext,
    CloudBaziAnalysis,
    CloudGeneration,
)
from .ai_service_errors import AIServiceError, classify_service_error
from .bazi_ai_prompt import build_messages


class OpenAIBaziClient:
    def __init__(self, config: AIConfig, client: object | None = None):
        self._config = config
        if client is not None:
            self._client = client
        elif config.enabled:
            from openai import OpenAI

            self._client = OpenAI(api_key=config.api_key)
        else:
            self._client = None

    def answer(self, context: AIRequestContext) -> CloudGeneration:
        if self._client is None:
            raise AIServiceError("disabled")
        try:
            response = self._client.responses.parse(
                model=self._config.model,
                reasoning={"effort": self._config.reasoning_effort},
                store=False,
                input=build_messages(context),
                text_format=CloudBaziAnalysis,
                timeout=self._config.timeout_seconds,
            )
        except TimeoutError:
            raise AIServiceError("timeout") from None
        except (ValidationError, ValueError):
            raise AIServiceError("unparseable_response") from None
        except Exception as exc:
            raise AIServiceError(classify_service_error(exc)) from None
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AIServiceError("unparseable_response")
        try:
            cloud = (
                parsed
                if isinstance(parsed, CloudBaziAnalysis)
                else CloudBaziAnalysis.model_validate(parsed)
            )
            usage = getattr(response, "usage", None)
            return CloudGeneration(
                analysis=cloud,
                input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            )
        except Exception:
            raise AIServiceError("unparseable_response") from None
