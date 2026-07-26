"""Structured OpenAI Responses API adapter for de-identified Bazi facts."""

from __future__ import annotations

from pydantic import ValidationError

from core.ai_models import AIConfig, AIRequestContext, BaziAIAnswer
from services.bazi_ai_prompt import build_messages


class AIServiceError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def classify_service_error(exc: Exception) -> str:
    exception_name = type(exc).__name__.lower()
    if isinstance(exc, TimeoutError) or "timeout" in exception_name:
        return "timeout"
    status = getattr(exc, "status_code", None)
    code = str(getattr(exc, "code", "") or "").lower()
    text = f"{code} {exc}".lower()
    if status in {401, 403}:
        return "invalid_credentials"
    if status == 429 and any(
        token in text for token in ("insufficient_quota", "billing", "quota")
    ):
        return "insufficient_quota"
    if status == 429:
        return "rate_limited"
    if status in {500, 502, 503, 504}:
        return "service_unavailable"
    if isinstance(exc, (ConnectionError, OSError)) or "connection" in exception_name:
        return "network_error"
    return "service_unavailable"


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

    def answer(self, context: AIRequestContext) -> BaziAIAnswer:
        if self._client is None:
            raise AIServiceError("disabled")
        try:
            response = self._client.responses.parse(
                model=self._config.model,
                reasoning={"effort": self._config.reasoning_effort},
                store=False,
                input=build_messages(context),
                text_format=BaziAIAnswer,
                timeout=self._config.timeout_seconds,
            )
        except TimeoutError:
            raise AIServiceError("timeout") from None
        except ValidationError:
            raise AIServiceError("unparseable_response") from None
        except Exception as exc:
            raise AIServiceError(classify_service_error(exc)) from None
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AIServiceError("unparseable_response")
        if isinstance(parsed, BaziAIAnswer):
            return parsed
        try:
            return BaziAIAnswer.model_validate(parsed)
        except Exception:
            raise AIServiceError("unparseable_response") from None
