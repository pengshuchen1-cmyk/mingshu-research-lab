"""Kimi K3 Chat Completions adapter for de-identified Bazi facts."""

from __future__ import annotations

import json

from core.ai_models import AIConfig, AIRequestContext, BaziAIAnswer
from services.ai_service_errors import AIServiceError, classify_service_error
from services.bazi_ai_prompt import build_messages


KIMI_MODEL = "kimi-k3"


def _response_format() -> dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "bazi_ai_answer",
            "strict": True,
            "schema": BaziAIAnswer.model_json_schema(),
        },
    }


class KimiBaziClient:
    def __init__(self, config: AIConfig, client: object | None = None):
        self._config = config
        if client is not None:
            self._client = client
        elif config.enabled:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
            )
        else:
            self._client = None

    def answer(self, context: AIRequestContext) -> BaziAIAnswer:
        if self._config.model != KIMI_MODEL:
            raise AIServiceError("service_unavailable")
        if self._client is None:
            raise AIServiceError("disabled")
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=build_messages(context),
                response_format=_response_format(),
                stream=False,
                max_completion_tokens=4000,
                extra_body={
                    "reasoning_effort": self._config.reasoning_effort,
                },
                timeout=self._config.timeout_seconds,
            )
            choices = getattr(response, "choices", None) or []
            if not choices or getattr(choices[0], "finish_reason", None) == "length":
                raise AIServiceError("unparseable_response")
            content = getattr(getattr(choices[0], "message", None), "content", None)
            parsed = json.loads(content) if isinstance(content, str) else None
            return BaziAIAnswer.model_validate(parsed)
        except AIServiceError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError):
            raise AIServiceError("unparseable_response") from None
        except Exception as exc:
            raise AIServiceError(classify_service_error(exc)) from None
