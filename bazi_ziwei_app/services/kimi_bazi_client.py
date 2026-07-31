"""Kimi K3 Chat Completions adapter for de-identified Bazi facts."""

from __future__ import annotations

import json
from copy import deepcopy

from core.ai_models import (
    AIConfig,
    AIRequestContext,
    CloudBaziAnalysis,
    CloudGeneration,
)
from services.ai_service_errors import AIServiceError, classify_service_error
from services.bazi_ai_prompt import build_messages


KIMI_MODEL = "kimi-k3"


def _response_format(
    allowed_claim_ids: tuple[str, ...],
) -> dict[str, object]:
    schema = deepcopy(CloudBaziAnalysis.model_json_schema())
    claim_items = schema["$defs"]["CloudSegment"]["properties"][
        "claim_ids"
    ]["items"]
    claim_items["enum"] = list(allowed_claim_ids)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "bazi_cloud_analysis",
            "strict": True,
            "schema": schema,
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
                max_retries=0,
            )
        else:
            self._client = None

    def answer(self, context: AIRequestContext) -> CloudGeneration:
        if self._config.model != KIMI_MODEL:
            raise AIServiceError("service_unavailable")
        if self._client is None:
            raise AIServiceError("disabled")
        try:
            plan = context.analysis_plan
            if plan is None:
                raise AIServiceError("unparseable_response")
            allowed_claim_ids = tuple(claim.id for claim in plan.claims)
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=build_messages(context),
                response_format=_response_format(allowed_claim_ids),
                stream=False,
                max_completion_tokens=6000,
                extra_body={
                    "reasoning_effort": self._config.reasoning_effort,
                },
                timeout=self._config.timeout_seconds,
            )
            choices = getattr(response, "choices", None) or []
            if not choices or getattr(choices[0], "finish_reason", None) == "length":
                raise AIServiceError("unparseable_response")
            content = getattr(getattr(choices[0], "message", None), "content", None)
            raw = json.loads(content) if isinstance(content, str) else None
            parsed = CloudBaziAnalysis.model_validate(raw)
            usage = getattr(response, "usage", None)
            return CloudGeneration(
                analysis=parsed,
                input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            )
        except AIServiceError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError):
            raise AIServiceError("unparseable_response") from None
        except Exception as exc:
            raise AIServiceError(classify_service_error(exc)) from None
