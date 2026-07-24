"""Structured OpenAI Responses API adapter for de-identified Bazi facts."""

from __future__ import annotations

import json

from pydantic import ValidationError

from core.ai_models import AIConfig, AIRequestContext, BaziAIAnswer


SYSTEM_INSTRUCTION = """你是命数研究室的四柱问答助手。
仅使用请求中提供的去身份化命盘事实和本地规则，不得补充未提供的事实、规则或现实状态。
不得重新计算四柱、节气、起运或大运，不得根据原始出生数据推断或补造出生信息。
回答必须严格包含以下六个非空部分：
1. 分析结论（analysis_conclusion）：区分命局倾向与当前现实状态。
2. 命盘证据（chart_evidence）：逐条引用请求中提供的具体命盘事实。
3. 规则证据（rule_evidence）：逐条引用请求中提供的本地规则。
4. 时间条件（timing_conditions）：说明结论成立所需的时间触发条件。
5. 现实建议（practical_advice）：提供审慎、可执行且现实的建议。
6. 不确定性与限制（uncertainty_limitations）：明确证据边界与不能判断之处。
不得保证结婚、离婚、发财、疾病、死亡、法律、投资或借贷结果。
如果问题询问当前是否已婚、未婚或已经结婚，分析结论必须先以
“单凭八字，不能确认现实中的婚姻登记状态。”开头，再根据已提供的关系信号给出
“更偏向、可能、未必”等概率倾向；不得把现实婚姻状态写成确定事实。
如果事实不足，请明确说明不能判断当前现实状态。"""


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
