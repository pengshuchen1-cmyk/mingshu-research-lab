"""Shared prompt and message construction for Bazi cloud providers."""

from __future__ import annotations

import json

from core.ai_intent import (
    CURRENT_MARRIAGE_DISCLAIMER,
)
from core.ai_models import AIRequestContext


_DEPTH_TARGETS = {
    "direct": "300—700",
    "single_year": "700—1200",
    "topic": "1200—2200",
    "long_range": "2200—4000",
    "monthly": "2200—4000",
}

_SYSTEM_INSTRUCTION = """你是命数研究室的四柱问答表达助手。
只允许使用用户消息中的 FactPacket 和 AnalysisPlan，不得使用自身命理知识补充材料。
FactPacket 与 AnalysisPlan 已由本地排盘和规则生成；不得重新计算四柱、节气、
日柱、时柱、起运、大运、流年或流月，也不得引入材料中没有的干支、十神、
强弱、格局、年份、规则或现实状态。

返回 CloudBaziAnalysis 的 segments。每个段落必须提供非空 claim_ids 和自然正文 text。
每个 claim_id 必须从 allowed_claim_ids 中原样复制；不得翻译、缩写、拼接、改写或创造新编号。
无法展开某个 claim 时省略该段，由本地规则补齐。正文只能展开所引用 claim 的
allowed_conclusion、fact_ids、rule_ids、conditions、uncertainty 和
prohibited_expansion，不得写入 claim 之外的命理结论，也不得覆盖本地结论。

本次 requested_depth 为 {requested_depth}，全文目标约 {target} 个中文字符。
长度是内容深度目标，不得凑字数、重复、泛化或扩写无关内容。结论优先，证据紧贴结论，
自然说明适用条件、现实建议与必要限制。结构化段落仅供内部校验和装配；
段落正文不得固定套用六个栏目，可以按当前问题自然成文或使用必要的小标题。

不得保证结婚、离婚、发财、疾病、死亡、法律、投资或借贷结果，
不得断言材料未提供的现实婚姻、健康、财产或法律状态。
"""


def _current_marriage_instruction(context: AIRequestContext) -> str:
    plan = context.analysis_plan
    if (
        plan is None
        or plan.resolved.domain != "relationship"
        or not plan.resolved.current_marriage_status_requested
    ):
        return ""
    supported = any(
        claim.id.startswith("relationship.") and claim.uncertainty
        for claim in plan.claims
    )
    if not supported:
        raise ValueError("relationship_uncertainty_required")
    return (
        "\n当前问题询问现实婚姻登记状态。整个回答的第一段 text 必须先以"
        f"“{CURRENT_MARRIAGE_DISCLAIMER}”开头，再基于 relationship claim "
        "及其 uncertainty 给出概率倾向；不得确定现实登记状态。\n"
    )


def build_messages(context: AIRequestContext) -> list[dict[str, str]]:
    if context.fact_packet is None or context.analysis_plan is None:
        raise ValueError("grounded_context_required")
    requested_depth = context.analysis_plan.resolved.requested_depth
    system_instruction = _SYSTEM_INSTRUCTION.format(
        requested_depth=requested_depth,
        target=_DEPTH_TARGETS[requested_depth],
    )
    system_instruction += _current_marriage_instruction(context)
    payload = {
        "allowed_claim_ids": [
            claim.id for claim in context.analysis_plan.claims
        ],
        "fact_packet": context.fact_packet.model_dump(mode="json"),
        "analysis_plan": context.analysis_plan.model_dump(mode="json"),
    }
    return [
        {"role": "system", "content": system_instruction},
        {
            "role": "user",
            "content": json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
            ),
        },
    ]
