"""Build locally renderable, evidence-grounded Bazi analysis plans."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date

from core.ai_models import AnalysisPlan, ClaimPlan, FactItem, FactPacket


class AnalysisPlanError(ValueError):
    """Stable failure for incomplete or unrenderable grounded plans."""

    _MESSAGES = {
        "PLAN_DOMAIN_FACTS_MISSING": "未找到当前问题领域所需的命盘事实。",
        "PLAN_DOMAIN_RULES_MISSING": "未找到当前问题领域所需的规则证据。",
        "PLAN_SAFETY_RULES_MISSING": "未找到本地回答所需的安全规则。",
        "PLAN_TIMING_FACTS_MISSING": "未找到全部请求时间及相关大运事实。",
        "PLAN_CAPACITY_EXCEEDED": "请求事实无法在本地结论计划容量内完整表达。",
        "PLAN_RULE_ID_MISSING": "结论计划引用的本地规则不存在。",
        "PLAN_RENDER_CAPACITY_EXCEEDED": "本地结论计划无法在回答容量内完整呈现。",
    }

    def __init__(self, code: str):
        self.code = code
        message = self._MESSAGES.get(code, "本地结论计划暂不可用。")
        super().__init__(f"{code}: {message}")


_DOMAIN_CONTENT = {
    "overview": {
        "topic": "整体结构",
        "conclusion": "整体判断以已提供的日主强弱、格局和四柱结构为主线。",
        "condition": "各主题需结合对应命盘事实与现实处境分别核对。",
        "advice": "先核实现实中的主要目标，再选择需要深入观察的领域。",
        "limit": "命盘只描述传统结构倾向，不证明具体事件已经发生。",
    },
    "wealth": {
        "topic": "财务承载",
        "conclusion": "财务主题应同时观察机会、承载能力与留存条件。",
        "condition": "只有现金流、成本和风险边界可承受时，机会才适合转为行动。",
        "advice": "先做预算和下行情景测试，再决定投入规模与退出条件。",
        "limit": "命盘不能证明现实资产数额，也不保证财务结果。",
    },
    "career": {
        "topic": "事业路径",
        "conclusion": "事业判断可由日主强弱、格局和十神结构观察工作方式与角色适配。",
        "condition": "岗位选择仍需同时满足技能、平台、团队和精力承载条件。",
        "advice": "用试做、作品或阶段目标验证岗位与行业匹配度。",
        "limit": "命盘不证明现实职位，也不保证升职、录用或事业结果。",
    },
    "relationship": {
        "topic": "关系条件",
        "conclusion": "关系主题只能观察吸引、建立与稳定条件，不能据此确认现实状态。",
        "condition": "关系进展取决于双方意愿、互动质量、边界和承诺落实。",
        "advice": "以真实沟通和持续行动核对关系是否具备稳定条件。",
        "limit": "现实婚姻状态未知，命盘不能断言已婚、未婚或关系已经建立。",
    },
    "family": {
        "topic": "家庭互动",
        "conclusion": "家庭主题只用于观察互动角色、沟通方式与边界倾向。",
        "condition": "具体家庭关系仍取决于真实经历、共同生活与沟通环境。",
        "advice": "把可观察的互动模式与单次事件分开记录，再处理现实边界。",
        "limit": "命盘不能替代当事人的家庭经历，也不能断言现实关系状态。",
    },
    "health_advisory": {
        "topic": "身心节律",
        "conclusion": "健康主题仅把五行、季节与强弱结构转为作息和精力管理提示。",
        "condition": "只有结合睡眠、压力、饮食、运动和实际体感才能评估生活调整。",
        "advice": "出现持续不适时记录症状并及时咨询合格医疗专业人士。",
        "limit": "现实健康状态未知；本回答不作疾病诊断，也不替代医疗判断。",
    },
    "children": {
        "topic": "子女议题",
        "conclusion": "子女主题只参考时柱、十神与藏干结构讨论传统倾向。",
        "condition": "生育与养育结果取决于健康、选择、关系和现实资源等多重条件。",
        "advice": "涉及生育健康或养育决策时，以现实沟通和专业意见为准。",
        "limit": "现实生育及子女状态未知，命盘不能断言数量、性别或具体结果。",
    },
    "education": {
        "topic": "学习路径",
        "conclusion": "学业主题可由十神、格局与强弱结构观察学习方式和资源需求。",
        "condition": "表现仍取决于基础、投入时间、教学环境与复习反馈。",
        "advice": "用阶段测验和错题复盘验证学习方法，再调整节奏。",
        "limit": "命盘不能替代成绩、能力评估，也不保证考试或录取结果。",
    },
    "relocation": {
        "topic": "迁移条件",
        "conclusion": "迁移主题只观察结构中的变化倾向与承载条件。",
        "condition": "搬迁或异地发展需同时满足工作、住处、成本、手续和支持网络条件。",
        "advice": "先核算迁移成本并准备试住、备选岗位与退出方案。",
        "limit": "命盘不能证明必然迁移，也不保证异地发展结果。",
    },
    "property": {
        "topic": "置业承载",
        "conclusion": "房产主题应把财富结构、日主承载与五行事实转为预算和风险观察。",
        "condition": "置业行动需满足首付、月供、应急储备、合同和退出条件。",
        "advice": "先做现金流压力测试，并独立核对产权、合同、利率与交易成本。",
        "limit": "命盘不能证明现实资产状态，也不保证财务结果。",
    },
    "benefactor": {
        "topic": "外部助力",
        "conclusion": "贵人主题只用于观察支持更可能通过何种角色、平台与协作条件出现。",
        "condition": "外部助力需要由能力展示、互惠合作和稳定信用触发。",
        "advice": "主动沉淀作品、清晰表达需求，并用实际合作验证支持质量。",
        "limit": "命盘不能保证特定人士出现，也不能断言他人一定提供帮助。",
    },
    "timing": {
        "topic": "阶段观察",
        "conclusion": "时间主题只整理事实包中已提供的大运、流年或流月信息。",
        "condition": "阶段提示必须落到现实资源、事件进展和复盘节点上验证。",
        "advice": "在已提供的时间范围内设置复盘点，并保留调整方案。",
        "limit": "未提供的时间事实不作补算，阶段标签也不保证现实结果。",
    },
}

_DOMAIN_RULE_PREFIXES = {
    "overview": ("STRENGTH-", "PATTERN-"),
    "wealth": ("WEALTH-",),
    "career": ("CAREER-",),
    "relationship": ("REL-",),
    "family": ("FAMILY-",),
    "health_advisory": ("HEALTH-",),
    "children": ("CHILDREN-",),
    "education": ("EDU-",),
    "relocation": ("MOVE-",),
    "property": ("PROPERTY-",),
    "benefactor": ("BENEFACTOR-",),
    "timing": ("DAYUN-", "CAL-"),
}

_TIME_KIND_TIE_PRIORITY = {
    "dayun": 0,
    "year": 1,
    "month": 2,
    "age": 3,
}
_TIMING_KINDS = frozenset(_TIME_KIND_TIE_PRIORITY)
_MAX_CLAIM_FACTS = 24
_MAX_CLAIM_TEXT = 1200
_MAX_PLAN_CLAIMS = 60


def _compose_local_paragraph(
    conclusion: str,
    facts: list[FactItem],
    conditions: list[str],
    uncertainty: list[str],
) -> str:
    fact_text = "；事实：".join(item.text.strip() for item in facts)
    parts = [conclusion]
    if fact_text:
        parts.append(f"命盘事实：{fact_text}")
    parts.extend(conditions)
    parts.extend(uncertainty)
    return " ".join(part.strip() for part in parts if part.strip())


def _local_paragraph(
    conclusion: str,
    facts: list[FactItem],
    conditions: list[str],
    uncertainty: list[str],
) -> str:
    paragraph = _compose_local_paragraph(
        conclusion,
        facts,
        conditions,
        uncertainty,
    )
    if len(paragraph) > _MAX_CLAIM_TEXT:
        raise AnalysisPlanError("PLAN_CAPACITY_EXCEEDED")
    return paragraph


def _claim(
    claim_id: str,
    topic: str,
    conclusion: str,
    facts: list[FactItem],
    rules: list[dict[str, str]],
    *,
    conditions: list[str] | None = None,
    uncertainty: list[str] | None = None,
) -> ClaimPlan:
    return ClaimPlan(
        id=claim_id,
        topic=topic,
        allowed_conclusion=conclusion,
        local_text=_local_paragraph(
            conclusion,
            facts,
            conditions or [],
            uncertainty or [],
        ),
        fact_ids=[item.id for item in facts],
        rule_ids=[item["id"] for item in rules],
        conditions=conditions or [],
        uncertainty=uncertainty or [],
        prohibited_expansion=["不得保证结果", "不得断言现实状态"],
    )


def _dedupe_facts(items: Sequence[FactItem], limit: int = 3) -> list[FactItem]:
    unique: dict[str, FactItem] = {}
    for item in items:
        unique.setdefault(item.id, item)
    return list(unique.values())[:limit]


def _dedupe_rules(
    items: Sequence[dict[str, str]],
    limit: int = 4,
) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for item in items:
        rule_id = str(item.get("id") or "").strip()
        if rule_id:
            unique.setdefault(rule_id, item)
    return list(unique.values())[:limit]


def _domain_facts(packet: FactPacket) -> list[FactItem]:
    prefix = f"domain.{packet.resolved.domain}."
    domain = [item for item in packet.facts if item.id.startswith(prefix)]
    if domain:
        return domain
    preferred_ids = {
        "wealth": "chart.wealth",
        "overview": "chart.day_master_strength",
        "relationship": "chart.pillars",
    }
    preferred = preferred_ids.get(packet.resolved.domain)
    if preferred:
        matched = [item for item in packet.facts if item.id == preferred]
        if matched:
            return matched
    if packet.resolved.domain == "timing":
        timing = [item for item in packet.facts if item.kind in _TIMING_KINDS]
        if timing:
            return timing
    raise AnalysisPlanError("PLAN_DOMAIN_FACTS_MISSING")


def _domain_rules(packet: FactPacket) -> list[dict[str, str]]:
    prefixes = _DOMAIN_RULE_PREFIXES.get(packet.resolved.domain, ())
    domain = [
        item
        for item in packet.rule_evidence
        if str(item.get("id") or "").startswith(prefixes)
    ]
    if domain:
        return _dedupe_rules(domain)
    raise AnalysisPlanError("PLAN_DOMAIN_RULES_MISSING")


def _safety_rules(packet: FactPacket) -> list[dict[str, str]]:
    safety = [
        item
        for item in packet.rule_evidence
        if str(item.get("id") or "").startswith("SAFETY-")
    ]
    if not safety:
        raise AnalysisPlanError("PLAN_SAFETY_RULES_MISSING")
    return _dedupe_rules(safety)


def _conditions(content: dict[str, str], prefix: str = "") -> list[str]:
    condition = content["condition"]
    if prefix:
        condition = f"{prefix}；{condition}"
    return [
        f"条件：{condition}",
        f"建议：{content['advice']}",
    ]


def _base_claims(packet: FactPacket) -> list[ClaimPlan]:
    content = _DOMAIN_CONTENT[packet.resolved.domain]
    domain_facts = _domain_facts(packet)
    core_facts = _dedupe_facts(
        domain_facts,
        4 if packet.resolved.domain == "health_advisory" else 1,
    )
    chart_facts = [
        item for item in packet.facts if item.source == "chart"
    ] or list(packet.facts)
    domain_rules = _domain_rules(packet)
    safety_rules = _safety_rules(packet)
    return [
        _claim(
            f"{packet.resolved.domain}.core",
            content["topic"],
            content["conclusion"],
            core_facts,
            domain_rules,
            conditions=_conditions(content),
            uncertainty=[f"限制：{content['limit']}"],
        ),
        _claim(
            f"{packet.resolved.domain}.structure",
            "命盘结构",
            "本次结论只从事实包中的结构信息展开，不补算未提供内容。",
            _dedupe_facts(chart_facts, 1),
            domain_rules,
            conditions=_conditions(
                content,
                "结构事实需与问题主题和现实背景共同验证",
            ),
            uncertainty=[f"限制：{content['limit']}"],
        ),
        _claim(
            f"{packet.resolved.domain}.action",
            "现实落点",
            "命盘倾向只有转化为可观察条件和可复盘行动时才具有参考意义。",
            _dedupe_facts(domain_facts, 1),
            safety_rules,
            conditions=_conditions(content, "行动前先核对现实约束"),
            uncertainty=[f"限制：{content['limit']}"],
        ),
    ]


def _date_from_text(text: str) -> date | None:
    match = re.search(r"((?:19|20)\d{2}-\d{2}-\d{2})", text)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _timing_sort_key(item: FactItem) -> tuple[date, int, str]:
    parsed = _date_from_text(item.text)
    if item.kind == "year":
        try:
            parsed = date(int(item.id.split(".")[1]), 1, 1)
        except (IndexError, TypeError, ValueError):
            parsed = parsed or date.max
    elif item.kind == "month":
        try:
            _, raw_year, raw_month = item.id.split(".", 2)
            parsed = date(int(raw_year), int(raw_month), 1)
        except (TypeError, ValueError):
            parsed = parsed or date.max
    return (
        parsed or date.max,
        _TIME_KIND_TIE_PRIORITY[item.kind],
        item.id,
    )


def _required_timing_ids(packet: FactPacket) -> set[str]:
    resolved = packet.resolved
    required = {f"year.{year}" for year in resolved.target_years}
    required.update(
        f"month.{year}.{month}"
        for year in resolved.target_years
        for month in resolved.target_months
    )
    required.update(
        f"age.{resolved.age_mode}.{age}"
        for age in resolved.age_values
    )
    if resolved.time_scope != "none":
        required.update(
            item.id for item in packet.facts if item.kind == "dayun"
        )
    return required


def _validated_timing_facts(packet: FactPacket) -> list[FactItem]:
    timing = [item for item in packet.facts if item.kind in _TIMING_KINDS]
    available_ids = {item.id for item in timing}
    required_ids = _required_timing_ids(packet)
    if packet.resolved.time_scope == "dayun" and not any(
        item.kind == "dayun" for item in timing
    ):
        raise AnalysisPlanError("PLAN_TIMING_FACTS_MISSING")
    if required_ids - available_ids:
        raise AnalysisPlanError("PLAN_TIMING_FACTS_MISSING")
    if packet.resolved.time_scope != "none" and not timing:
        raise AnalysisPlanError("PLAN_TIMING_FACTS_MISSING")
    return sorted(timing, key=_timing_sort_key)


def _timing_topic(facts: Sequence[FactItem]) -> str:
    first = facts[0]
    last = facts[-1]
    if first.kind == "month":
        if len(facts) == 1:
            _, year, month = first.id.split(".", 2)
            return f"{int(year)}年{int(month)}月"
        _, year, first_month = first.id.split(".", 2)
        last_month = last.id.rsplit(".", 1)[-1]
        return f"{int(year)}年{int(first_month)}—{int(last_month)}月"
    if first.kind == "year":
        first_year = int(first.id.split(".")[1])
        last_year = int(last.id.split(".")[1])
        return (
            f"{first_year}年流年"
            if first_year == last_year
            else f"{first_year}—{last_year}年流年"
        )
    if first.kind == "age":
        return first.text.split("对应", 1)[0] or "年龄范围"
    return "大运阶段"


def _timing_conclusion(facts: Sequence[FactItem]) -> str:
    if len(facts) == 1:
        return "该阶段只按已提供的时间事实观察主题条件。"
    return f"以下按连续时间顺序聚合{len(facts)}条已提供事实。"


def _timing_annotations(index: int) -> tuple[list[str], list[str]]:
    conditions = (
        ["条件：仅在请求事实覆盖的时间范围内观察。"]
        if index == 0
        else []
    )
    uncertainty = (
        ["限制：时间标签不等于事件必然发生。"]
        if index == 0
        else []
    )
    return conditions, uncertainty


def _timing_groups(timing_facts: list[FactItem]) -> list[list[FactItem]]:
    if len(timing_facts) <= 20:
        return [[item] for item in timing_facts]
    groups: list[list[FactItem]] = []
    current: list[FactItem] = []
    for item in timing_facts:
        candidate = [*current, item]
        conclusion = _timing_conclusion(candidate)
        conditions, uncertainty = _timing_annotations(len(groups))
        fits = (
            len(candidate) <= _MAX_CLAIM_FACTS
            and len(
                _compose_local_paragraph(
                    conclusion,
                    candidate,
                    conditions,
                    uncertainty,
                )
            ) <= _MAX_CLAIM_TEXT
            and (not current or item.kind == current[-1].kind)
        )
        if current and not fits:
            groups.append(current)
            current = [item]
        else:
            current = candidate
    if current:
        groups.append(current)
    if len(groups) + 1 > _MAX_PLAN_CLAIMS:
        raise AnalysisPlanError("PLAN_CAPACITY_EXCEEDED")
    return groups


def _timing_claims(packet: FactPacket) -> list[ClaimPlan]:
    rules = _dedupe_rules(
        [
            *[
                item
                for item in packet.rule_evidence
                if str(item.get("id") or "").startswith(("DAYUN-", "CAL-"))
            ],
            *_domain_rules(packet),
        ]
    )
    timing_facts = _validated_timing_facts(packet)
    claims = []
    for index, facts in enumerate(_timing_groups(timing_facts)):
        topic = _timing_topic(facts)
        conditions, uncertainty = _timing_annotations(index)
        claims.append(
            _claim(
                f"{packet.resolved.domain}.{facts[0].id}",
                topic,
                _timing_conclusion(facts),
                list(facts),
                rules,
                conditions=conditions,
                uncertainty=uncertainty,
            )
        )
    return claims


def build_analysis_plan(packet: FactPacket) -> AnalysisPlan:
    """Convert a fact packet into claims grounded in that packet only."""
    base = _base_claims(packet)
    timing = (
        _timing_claims(packet)
        if packet.resolved.time_scope != "none"
        else []
    )
    depth = packet.resolved.requested_depth
    if depth == "direct":
        claims = base[:1]
    elif depth == "single_year":
        claims = [base[0], *timing]
    elif depth == "topic":
        claims = [base[0], *timing] if timing else base
    elif depth == "long_range":
        claims = [base[0], *timing]
    else:
        claims = [base[0], *timing]
    if len(claims) > _MAX_PLAN_CLAIMS:
        raise AnalysisPlanError("PLAN_CAPACITY_EXCEEDED")
    planned_fact_ids = {
        fact_id for claim in claims for fact_id in claim.fact_ids
    }
    required_ids = _required_timing_ids(packet)
    if required_ids - planned_fact_ids:
        raise AnalysisPlanError("PLAN_TIMING_FACTS_MISSING")
    return AnalysisPlan(resolved=packet.resolved, claims=claims)
