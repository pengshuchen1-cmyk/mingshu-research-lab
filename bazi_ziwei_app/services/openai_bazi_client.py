"""Structured OpenAI Responses API adapter for de-identified Bazi facts."""

from __future__ import annotations

import json

from core.ai_models import AIConfig, AIRequestContext, BaziAIAnswer


SYSTEM_INSTRUCTION = """你是命数研究室的四柱问答助手。
仅使用请求中提供的去身份化命盘事实和本地规则，不自行重排命盘，不补造出生信息。
回答必须区分命局倾向、时间触发、不确定性和现实建议；证据必须来自提供的事实与规则。
不得保证结婚、离婚、发财、疾病、死亡、法律、投资或借贷结果。
如果事实不足，请明确说明不能判断当前现实状态。"""


class AIServiceError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def build_messages(context: AIRequestContext) -> list[dict[str, str]]:
    payload = context.model_dump(mode="json")
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False, sort_keys=True),
        },
    ]


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
        except TimeoutError as exc:
            raise AIServiceError("timeout") from exc
        except Exception as exc:
            raise AIServiceError("service_error") from exc
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AIServiceError("unparseable_response")
        if isinstance(parsed, BaziAIAnswer):
            return parsed
        try:
            return BaziAIAnswer.model_validate(parsed)
        except Exception as exc:
            raise AIServiceError("unparseable_response") from exc
