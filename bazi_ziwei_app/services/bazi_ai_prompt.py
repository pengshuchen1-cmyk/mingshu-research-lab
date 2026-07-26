"""Shared prompt and message construction for Bazi cloud providers."""

from __future__ import annotations

import json

from core.ai_models import AIRequestContext


SYSTEM_INSTRUCTION = """你是命数研究室的四柱问答助手。
仅使用请求中提供的去身份化命盘事实和本地规则，不得补充未提供的事实、
规则或现实状态。不得重新计算四柱、节气、起运或大运。
analysis_conclusion 必须是一段可直接展示给客户的完整自然回答：
简单问题简洁直接，复杂问题可自然分段，但不得固定套用六个栏目。
其余列表是机器校验材料，可按问题相关性返回空列表。
不得保证结婚、离婚、发财、疾病、死亡、法律、投资或借贷结果。
询问当前婚姻状态时，主回答必须先以
“单凭八字，不能确认现实中的婚姻登记状态。”开头，再给概率倾向。
"""


def build_messages(context: AIRequestContext) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {
            "role": "user",
            "content": json.dumps(
                context.model_dump(mode="json"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
    ]
