"""Build locally renderable, evidence-grounded Bazi analysis plans."""

from __future__ import annotations

from collections.abc import Sequence

from core.ai_models import AnalysisPlan, ClaimPlan, FactItem, FactPacket


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

_FACT_KIND_PRIORITY = {
    "month": 0,
    "year": 1,
    "age": 2,
    "dayun": 3,
}


def _clip(value: str, limit: int) -> str:
    text = value.strip()
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


def _local_paragraph(
    conclusion: str,
    facts: list[FactItem],
    conditions: list[str],
    uncertainty: list[str],
) -> str:
    fact_text = "；".join(_clip(item.text, 260) for item in facts)
    parts = [conclusion]
    if fact_text:
        parts.append(f"命盘事实：{fact_text}")
    parts.extend(conditions)
    parts.extend(uncertainty)
    return _clip(" ".join(part.strip() for part in parts if part.strip()), 1200)


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
    }
    preferred = preferred_ids.get(packet.resolved.domain)
    if preferred:
        matched = [item for item in packet.facts if item.id == preferred]
        if matched:
            return matched
    return list(packet.facts)


def _domain_rules(packet: FactPacket) -> list[dict[str, str]]:
    prefixes = _DOMAIN_RULE_PREFIXES.get(packet.resolved.domain, ())
    domain = [
        item
        for item in packet.rule_evidence
        if str(item.get("id") or "").startswith(prefixes)
    ]
    if domain:
        return _dedupe_rules(domain)
    non_safety = [
        item
        for item in packet.rule_evidence
        if not str(item.get("id") or "").startswith("SAFETY-")
    ]
    return _dedupe_rules(non_safety or packet.rule_evidence)


def _safety_rules(packet: FactPacket) -> list[dict[str, str]]:
    safety = [
        item
        for item in packet.rule_evidence
        if str(item.get("id") or "").startswith("SAFETY-")
    ]
    return _dedupe_rules(safety or _domain_rules(packet))


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
            _dedupe_facts(domain_facts, 2),
            domain_rules,
            conditions=_conditions(content),
            uncertainty=[f"限制：{content['limit']}"],
        ),
        _claim(
            f"{packet.resolved.domain}.structure",
            "命盘结构",
            "本次结论只从事实包中的结构信息展开，不补算未提供内容。",
            _dedupe_facts(chart_facts, 2),
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
            _dedupe_facts(domain_facts, 2),
            safety_rules,
            conditions=_conditions(content, "行动前先核对现实约束"),
            uncertainty=[f"限制：{content['limit']}"],
        ),
    ]


def _timing_claims(packet: FactPacket) -> list[ClaimPlan]:
    content = _DOMAIN_CONTENT[packet.resolved.domain]
    base_fact = _domain_facts(packet)[0]
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
    timing_facts = sorted(
        [
            item
            for item in packet.facts
            if item.kind in _FACT_KIND_PRIORITY
        ],
        key=lambda item: (_FACT_KIND_PRIORITY[item.kind], item.id),
    )
    claims = []
    for item in timing_facts:
        label = {
            "month": "流月观察",
            "year": "流年观察",
            "age": "年龄范围",
            "dayun": "大运阶段",
        }[item.kind]
        claims.append(
            _claim(
                f"{packet.resolved.domain}.{item.id}",
                label,
                f"该阶段只按已提供的{label}事实观察主题条件。",
                _dedupe_facts([item, base_fact], 2),
                rules,
                conditions=_conditions(
                    content,
                    "仅在该事实覆盖的时间范围内观察",
                ),
                uncertainty=[
                    f"限制：{content['limit']}",
                    "限制：时间标签不等于事件必然发生。",
                ],
            )
        )
    return claims


def build_analysis_plan(packet: FactPacket) -> AnalysisPlan:
    """Convert a fact packet into claims grounded in that packet only."""
    base = _base_claims(packet)
    timing = _timing_claims(packet)
    depth = packet.resolved.requested_depth
    if depth == "direct":
        claims = base[:1]
    elif depth == "single_year":
        claims = [base[0], *(timing[:2] or base[1:2])]
    elif depth == "topic":
        claims = base
    elif depth == "long_range":
        claims = [*base, *timing]
    else:
        monthly = [claim for claim in timing if ".month." in claim.id]
        other_timing = [claim for claim in timing if ".month." not in claim.id]
        claims = [base[0], *monthly, *other_timing]
    return AnalysisPlan(resolved=packet.resolved, claims=claims[:60])
