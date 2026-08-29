"""Adaptive local answers built only from supplied AI context."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..bazi.bazi_rulebook import load_rulebook
from .ai_analysis_plan import AnalysisPlanError
from .ai_models import AIRequestContext, AnalysisPlan, BaziAIAnswer

_BORROWING_TERMS = (
    "房贷", "按揭", "借钱", "负债", "融资", "抵押", "借贷", "贷款", "杠杆",
)
_MAX_LOCAL_STRING_CHARS = 3000
_MAX_LOCAL_MAIN_ANSWER_CHARS = 6000
_MAX_LOCAL_TIMING_BLOCK_CHARS = 1200
_MAX_LOCAL_ADVICE_BLOCK_CHARS = 1600
_MAX_LOCAL_LIMITATIONS_BLOCK_CHARS = 1600
_TRUNCATION_SUFFIX = "…（已按本地回答长度上限截断）"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object, default: str = "未提供") -> str:
    text = str(value or "").strip()
    return text or default


def _strings(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [
        str(item).strip()
        for item in value
        if item is not None and str(item).strip()
    ]


def _bounded_string(value: str) -> str:
    text = value.strip()
    if len(text) <= _MAX_LOCAL_STRING_CHARS:
        return text
    prefix_limit = _MAX_LOCAL_STRING_CHARS - len(_TRUNCATION_SUFFIX)
    return text[:prefix_limit].rstrip() + _TRUNCATION_SUFFIX


def _bounded_main_answer(value: str) -> str:
    text = value.strip()
    if len(text) <= _MAX_LOCAL_MAIN_ANSWER_CHARS:
        return text
    prefix_limit = _MAX_LOCAL_MAIN_ANSWER_CHARS - len(_TRUNCATION_SUFFIX)
    return text[:prefix_limit].rstrip() + _TRUNCATION_SUFFIX


def _bounded_block(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    prefix_limit = max(1, limit - len(_TRUNCATION_SUFFIX))
    return text[:prefix_limit].rstrip() + _TRUNCATION_SUFFIX


def _deduplicated(items: Sequence[str], *, limit: int = 12) -> list[str]:
    bounded = (_bounded_string(item) for item in items if item.strip())
    return list(dict.fromkeys(bounded))[:limit]


def _bullet_block(title: str, items: Sequence[str], limit: int) -> str:
    selected = _deduplicated(items, limit=limit)
    if not selected:
        return ""
    return f"**{title}**\n" + "\n".join(f"- {item}" for item in selected)


def _adaptive_local_text(
    context: AIRequestContext,
    conclusion: str,
    chart_evidence: Sequence[str],
    rule_evidence: Sequence[str],
    timing: Sequence[str],
    advice: Sequence[str],
    limitations: Sequence[str],
) -> str:
    leading_parts = [_bounded_string(conclusion)]
    evidence = [*chart_evidence[:4], *rule_evidence[:2]]
    if evidence:
        leading_parts.append(_bullet_block("主要依据", evidence, 6))

    trailing_parts: list[str] = []
    if (context.requires_timing or context.category == "timing") and timing:
        trailing_parts.append(
            _bounded_block(
                _bullet_block("阶段观察", timing, 4),
                _MAX_LOCAL_TIMING_BLOCK_CHARS,
            )
        )
    if advice:
        trailing_parts.append(
            _bounded_block(
                _bullet_block("现实建议", advice, 4),
                _MAX_LOCAL_ADVICE_BLOCK_CHARS,
            )
        )
    if limitations and (
        context.category == "relationship"
        or context.requires_timing
        or any(term in context.question for term in _BORROWING_TERMS)
    ):
        trailing_parts.append(
            _bounded_block(
                _bullet_block("需要说明", limitations, 4),
                _MAX_LOCAL_LIMITATIONS_BLOCK_CHARS,
            )
        )

    trailing = "\n\n".join(part for part in trailing_parts if part)
    separator = "\n\n" if leading_parts and trailing else ""
    leading_budget = _MAX_LOCAL_MAIN_ANSWER_CHARS - len(trailing) - len(separator)
    leading = _bounded_block(
        "\n\n".join(part for part in leading_parts if part),
        max(1, leading_budget),
    )
    return _bounded_main_answer(f"{leading}{separator}{trailing}")


def _base_chart_evidence(facts: Mapping[str, object]) -> list[str]:
    pillars = _strings(facts.get("pillars"))
    strength = _mapping(facts.get("strength"))
    pattern = _mapping(facts.get("pattern"))
    evidence = []
    if pillars:
        evidence.append(f"四柱为{'、'.join(pillars)}。")
    evidence.extend(
        [
            f"{_text(facts.get('day_master'))}日主。",
            f"强弱结论为{_text(strength.get('classification'))}。",
            f"格局结论为{_text(pattern.get('classification'))}。",
        ]
    )
    return evidence


def _domain_evidence(
    facts: Mapping[str, object],
    category: str,
) -> list[str]:
    strength = _mapping(facts.get("strength"))
    pattern = _mapping(facts.get("pattern"))
    wealth = _mapping(facts.get("wealth"))
    relationship = _mapping(facts.get("relationship"))

    if category == "wealth":
        return _strings(wealth.get("evidence"))
    if category == "career":
        return [
            *_strings(pattern.get("evidence")),
            *_strings(strength.get("evidence")),
            *_strings(wealth.get("evidence"))[:1],
        ]
    if category in {"relationship", "family"}:
        return _strings(relationship.get("evidence"))
    if category == "overview":
        return [
            *_strings(strength.get("evidence"))[:2],
            *_strings(pattern.get("evidence"))[:2],
        ]
    return []


def _is_current_marriage_question(context: AIRequestContext) -> bool:
    return (
        context.category == "relationship"
        and context.current_marriage_status_requested
    )


def _relationship_stability_signals(
    facts: Mapping[str, object],
) -> list[Mapping[str, object]]:
    raw_signals = _mapping(facts.get("relationship")).get("stability_signals")
    if not isinstance(raw_signals, Sequence) or isinstance(
        raw_signals, (str, bytes)
    ):
        return []
    return [item for item in raw_signals if isinstance(item, Mapping)]


def _current_marriage_tendency(facts: Mapping[str, object]) -> str:
    polarities = {
        str(item.get("polarity") or "").strip().lower()
        for item in _relationship_stability_signals(facts)
    }
    if polarities == {"support"}:
        return (
            "更偏向已经结婚，或者至少曾有过一段接近婚姻的长期正式关系；"
            "不像是到现在完全没有过稳定姻缘"
        )
    if polarities == {"pressure"}:
        return "更偏向目前未必处于稳定婚姻中，或曾有关系但经历明显波折"
    return (
        "更偏向认为“关系机会存在”不等于“已经形成稳定婚姻”，"
        "现有中性信号不足以让某一现实状态显著更可能"
    )


def _relationship_signal_descriptions(facts: Mapping[str, object]) -> list[str]:
    descriptions: list[str] = []
    for signal in _relationship_stability_signals(facts):
        for key in ("fact", "explanation"):
            text = str(signal.get(key) or "").strip()
            if text:
                descriptions.append(text)
    return _deduplicated(descriptions)


def _has_current_or_target_timing(facts: Mapping[str, object]) -> bool:
    if _mapping(facts.get("current_context")):
        return True
    target_years = facts.get("target_years")
    if not isinstance(target_years, Sequence) or isinstance(
        target_years, (str, bytes)
    ):
        return False
    return any(bool(_mapping(item)) for item in target_years)


def _analysis_conclusion(
    context: AIRequestContext,
    facts: Mapping[str, object],
) -> str:
    category = context.category
    strength = _text(_mapping(facts.get("strength")).get("classification"))
    pattern = _text(_mapping(facts.get("pattern")).get("classification"))
    wealth = _text(_mapping(facts.get("wealth")).get("summary"))
    relationship = _text(_mapping(facts.get("relationship")).get("summary"))
    day_master = _text(facts.get("day_master"))

    if category == "wealth":
        return f"财务判断以已提供的财富事实为主：{wealth}"
    if category == "career":
        return (
            f"事业判断应结合{day_master}日主、{strength}与{pattern}："
            "可据此观察工作方式和承载条件，但具体行业选择仍需现实验证。"
        )
    if category == "relationship":
        if _is_current_marriage_question(context):
            basis = (
                "结合本盘提供的配偶星/夫妻宫/关系稳定信号及当前时运"
                if _has_current_or_target_timing(facts)
                else "结合本盘提供的关系结构与稳定条件"
            )
            signal_descriptions = _relationship_signal_descriptions(facts)
            supplied_signals = (
                f"；结构化稳定信号事实：{'；'.join(signal_descriptions)}"
                if signal_descriptions
                else ""
            )
            return (
                "单凭八字，不能确认现实中的婚姻登记状态。"
                "但如果一定要根据命盘作倾向判断："
                f"{basis}，"
                f"我{_current_marriage_tendency(facts)}。"
                "仍需以本人现实情况为准。"
                f"本次依据的关系事实是：{relationship}{supplied_signals}"
            )
        return f"关系判断仅描述互动倾向与建立条件：{relationship}"
    if category == "family":
        return (
            "命盘只能观察家庭互动倾向，不能替代当事人的真实经历；"
            f"可参考已提供的关系事实：{relationship}"
        )
    if category == "timing":
        return (
            "时间判断仅整理请求中已经提供的大运、当前与目标年份事实，"
            "不据此补算未提供的运程。"
        )
    return (
        f"整体结构以{day_master}日主、{strength}和{pattern}为主线；"
        "各主题仍需结合对应事实与现实处境分别验证。"
    )


def _timing_conditions(
    context: AIRequestContext,
    facts: Mapping[str, object],
) -> list[str]:
    dayun = _mapping(facts.get("dayun"))
    direction = str(dayun.get("direction") or "").strip()
    start = str(dayun.get("start") or "").strip()
    conditions: list[str] = []
    is_current_marriage = _is_current_marriage_question(context)
    has_current_or_target_timing = _has_current_or_target_timing(facts)
    if (direction or start) and (
        not is_current_marriage or has_current_or_target_timing
    ):
        conditions.append(
            "已提供的大运事实："
            + "；".join(
                item
                for item in (
                    f"方向为{direction}" if direction else "",
                    f"起运为{start}" if start else "",
                )
                if item
            )
            + "。"
        )

    current = _mapping(facts.get("current_context"))
    current_parts = []
    if current.get("year"):
        current_parts.append(f"{current['year']}年")
    if current.get("year_pillar"):
        current_parts.append(f"年柱{current['year_pillar']}")
    if current.get("month_pillar"):
        current_parts.append(f"月柱{current['month_pillar']}")
    if current.get("day_pillar"):
        current_parts.append(f"日柱{current['day_pillar']}")
    if current_parts:
        conditions.append("已提供的当前事实：" + "、".join(current_parts) + "。")

    target_years = facts.get("target_years")
    if isinstance(target_years, Sequence) and not isinstance(
        target_years, (str, bytes)
    ):
        for raw_target in target_years:
            target = _mapping(raw_target)
            year = str(target.get("year") or "").strip()
            pillar = str(target.get("year_pillar") or "").strip()
            if year or pillar:
                detail = f"{year}年" if year else "目标年份"
                if pillar:
                    detail += f"年柱{pillar}"
                conditions.append(f"已提供的目标年份事实：{detail}。")

    dayun_periods = facts.get("dayun_periods")
    if isinstance(dayun_periods, Sequence) and not isinstance(
        dayun_periods, (str, bytes)
    ):
        supplied_periods = [
            _mapping(item)
            for item in dayun_periods
            if isinstance(item, Mapping)
        ]
        try:
            current_year = int(current.get("year") or 0)
        except (TypeError, ValueError):
            current_year = 0

        def numeric(value: object) -> int:
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        def relevance(period: Mapping[str, object]) -> tuple[int, int]:
            pillar = str(period.get("pillar") or "")
            ten_god = str(period.get("ten_god") or "")
            if (pillar and pillar in context.question) or (
                ten_god and ten_god in context.question
            ):
                priority = 0
            elif current_year and (
                numeric(period.get("start_year"))
                <= current_year
                <= numeric(period.get("end_year"))
            ):
                priority = 1
            elif context.category == "wealth" and ten_god in {"正财", "偏财"}:
                priority = 2
            else:
                priority = 3
            return priority, numeric(period.get("start_year"))

        for period in sorted(supplied_periods, key=relevance):
            start_year = str(period.get("start_year") or "").strip()
            end_year = str(period.get("end_year") or "").strip()
            start_age = str(period.get("start_age") or "").strip()
            end_age = str(period.get("end_age") or "").strip()
            pillar = str(period.get("pillar") or "").strip()
            ten_god = str(period.get("ten_god") or "").strip()
            if not (start_year and end_year and pillar):
                continue
            age_text = (
                f"，约{start_age}—{end_age}岁"
                if start_age and end_age
                else ""
            )
            ten_god_text = f"，十神为{ten_god}" if ten_god else ""
            conditions.append(
                f"已提供的大运阶段事实：{start_year}—{end_year}年"
                f"为{pillar}大运{age_text}{ten_god_text}。"
            )

    if is_current_marriage:
        relationship = _text(_mapping(facts.get("relationship")).get("summary"))
        if has_current_or_target_timing:
            conditions.append(
                "关系状态的倾向判断依据已提供的关系事实："
                f"{relationship}；并只把上述已提供的大运或流年事实作为时间条件，"
                "仍需由本人现实情况核实。"
            )
        else:
            conditions.append(
                "关系状态的倾向判断：当前上下文未提供当前或目标年份事实，"
                "本次倾向只依据已提供的关系结构与稳定条件；"
                "仍需由本人现实情况核实。"
            )

    if not conditions:
        conditions.append("当前上下文未提供具体大运或流年事实，不能补充时间断语。")
    return _deduplicated(conditions)


def _practical_advice(context: AIRequestContext) -> list[str]:
    advice_by_category = {
        "overview": [
            "把强弱、格局、财富和关系结论分别与现实经历核对，再确定优先事项。",
            "将重要决定拆成可复核的小步骤，并保留调整空间。",
        ],
        "wealth": [
            "先核对稳定收入、必要支出和现金储备，再评估项目规模。",
            "区分赚钱机会与留财能力，用预算、回款节点和风险上限约束行动。",
        ],
        "career": [
            "用低成本试做、作品或阶段目标验证岗位与行业匹配度。",
            "同时评估技能、平台、团队、时间和现金流承载条件。",
        ],
        "relationship": [
            "以真实互动、边界、沟通和承诺落实情况判断关系进展。",
            "不要用命盘代替对方意愿或当前关系事实。",
        ],
        "family": [
            "把可观察的沟通模式与具体事件分开记录，优先处理现实边界。",
            "需要时通过坦诚沟通或专业支持核对家庭经历。",
        ],
        "timing": [
            "只在已提供的阶段事实上设置复盘节点，不把年份标签当作行动保证。",
            "重大决定仍需核对现实资源、风险和备选方案。",
        ],
        "other": [
            "补充具体主题和现实约束后，再把命盘事实转成可执行步骤。",
        ],
    }
    advice = list(advice_by_category.get(context.category, advice_by_category["other"]))
    if any(term in context.question for term in _BORROWING_TERMS):
        advice.extend(
            [
                "借贷或抵押前先做现金流压力测试，覆盖收入下降、成本上升等最坏情景。",
                "明确还款来源、可承受损失、止损条件和退出方案，再决定是否承担风险。",
            ]
        )
    return _deduplicated(advice)


def _limitations(context: AIRequestContext) -> list[str]:
    limitations = [
        "本回答只使用请求中已提供的命盘事实和规则证据，没有重新计算四柱、大运或流年。",
        "命理内容只用于观察倾向与条件，不保证现实结果，也不替代专业决策。",
    ]
    if context.category == "relationship":
        limitations.append("命盘不能单独证明当事人当前是否已婚或关系是否已经建立。")
    if _is_current_marriage_question(context):
        limitations.append(
            "上述倾向不代表确定已婚或未婚，也不构成现实或法律状态认定，"
            "仍需以本人现实情况为准。"
        )
    if any(term in context.question for term in _BORROWING_TERMS):
        limitations.append("命盘不能保证借贷、抵押、投资或创业结果。")
    if context.requires_timing or context.category == "timing":
        limitations.append("未提供的年份、月份、大运阶段或现实事件均不作推断。")
    return _deduplicated(limitations, limit=8)


def build_local_answer(context: AIRequestContext) -> BaziAIAnswer:
    """Build a complete answer without performing any astrological calculation."""
    facts = _mapping(context.chart_facts)
    chart_evidence = _deduplicated(
        [
            *_base_chart_evidence(facts),
            *_domain_evidence(facts, context.category),
        ]
    )
    rule_evidence = _deduplicated(
        [
            str(item.get("statement") or "").strip()
            for item in context.rule_evidence
            if isinstance(item, Mapping)
        ]
    )
    conclusion = _analysis_conclusion(context, facts)
    timing = _timing_conditions(context, facts)
    advice = _practical_advice(context)
    limitations = _limitations(context)
    return BaziAIAnswer(
        analysis_conclusion=_adaptive_local_text(
            context,
            conclusion,
            chart_evidence,
            rule_evidence,
            timing,
            advice,
            limitations,
        ),
        chart_evidence=chart_evidence,
        rule_evidence=rule_evidence,
        timing_conditions=timing,
        practical_advice=advice,
        uncertainty_limitations=limitations,
    )


def _plan_rule_statements(plan: AnalysisPlan) -> list[str]:
    book = load_rulebook()
    statements = []
    for claim in plan.claims:
        for rule_id in claim.rule_ids:
            try:
                statement = book.by_id(rule_id).statement
            except KeyError:
                raise AnalysisPlanError("PLAN_RULE_ID_MISSING") from None
            statements.append(statement)
    return _deduplicated(statements)


def _plan_fact_texts(plan: AnalysisPlan) -> list[str]:
    facts = []
    for claim in plan.claims:
        marker = "命盘事实："
        if marker not in claim.local_text:
            continue
        fact_block = claim.local_text.split(marker, 1)[1]
        for suffix in (" 条件：", " 建议：", " 限制："):
            fact_block = fact_block.split(suffix, 1)[0]
        fact_texts = [item.strip() for item in fact_block.split("；事实：")]
        if len(fact_texts) != len(claim.fact_ids):
            fact_texts = [fact_block.strip()] * len(claim.fact_ids)
        for fact_id, fact_text in zip(claim.fact_ids, fact_texts):
            if fact_id.startswith(("dayun.", "year.", "month.", "age.")):
                continue
            if (
                fact_id.startswith("domain.health_advisory.")
                and fact_id != "domain.health_advisory.strength"
            ):
                continue
            if fact_text:
                facts.append(fact_text)
    return _deduplicated(facts)


def _prefixed_values(
    plan: AnalysisPlan,
    prefix: str,
    *,
    limit: int,
) -> list[str]:
    values = []
    for claim in plan.claims:
        for condition in claim.conditions:
            if condition.startswith(prefix):
                values.append(condition[len(prefix):].strip())
    return _deduplicated(values, limit=limit)


def _render_plan_body(plan: AnalysisPlan) -> str:
    depth = plan.resolved.requested_depth
    paragraphs = []
    if plan.resolved.interpretation_receipt:
        paragraphs.append(plan.resolved.interpretation_receipt)
    if depth in {"direct", "single_year"}:
        paragraphs.extend(claim.local_text for claim in plan.claims)
    else:
        paragraphs.extend(
            f"**{claim.topic}**\n{claim.local_text}"
            for claim in plan.claims
        )
    disclaimer = "命理分析仅供传统文化参考，不替代现实中的医疗、法律或财务决策。"
    body = "\n\n".join(paragraphs)
    budget = _MAX_LOCAL_MAIN_ANSWER_CHARS - len(disclaimer) - 2
    if len(body) > budget:
        raise AnalysisPlanError("PLAN_RENDER_CAPACITY_EXCEEDED")
    return f"{body}\n\n{disclaimer}"


def render_local_plan(plan: AnalysisPlan) -> BaziAIAnswer:
    """Render a complete offline answer from an already-grounded plan."""
    rule_statements = _plan_rule_statements(plan)
    chart_evidence = _plan_fact_texts(plan)
    timing = _prefixed_values(plan, "条件：", limit=12)
    advice = _prefixed_values(plan, "建议：", limit=12)
    limitations = _deduplicated(
        [
            limitation.removeprefix("限制：").strip()
            for claim in plan.claims
            for limitation in claim.uncertainty
        ],
        limit=8,
    )
    return BaziAIAnswer(
        analysis_conclusion=_render_plan_body(plan),
        chart_evidence=chart_evidence,
        rule_evidence=rule_statements,
        timing_conditions=timing,
        practical_advice=advice,
        uncertainty_limitations=limitations,
    )
