"""Build locally renderable, evidence-grounded Bazi analysis plans."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date

from .ai_models import AnalysisPlan, ClaimPlan, FactItem, FactPacket


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
        "topic": "整体怎么看",
        "conclusion": "先说整体：这张盘要重点看日主强弱、格局，以及四柱之间怎么配合。",
        "condition": "事业、感情和财运要分开看，也要对照你的真实经历，不能用一句话包打天下。",
        "advice": "你可以先说最想解决的是事业、感情还是财运，我们再往下细看。",
        "limit": "八字只能提供传统角度的参考，不能证明现实中一定发生过什么。",
    },
    "wealth": {
        "topic": "钱财情况",
        "conclusion": (
            "看财运不能只看有没有赚钱机会，还要看你接不接得住，"
            "以及赚到的钱能不能留下来。"
        ),
        "condition": "先看收入稳不稳、成本多不多、风险能不能承受，再决定要不要行动。",
        "advice": "先把预算、最坏情况和退出办法算清楚，再决定投多少。",
        "limit": "八字看不出现实资产数额，也不能保证你一定赚钱。",
    },
    "career": {
        "topic": "事业怎么走",
        "conclusion": (
            "看事业，重点不是给你贴职业标签，而是看你习惯怎么做事、"
            "在什么环境里更容易发挥。"
        ),
        "condition": "真正选工作时，还要看你的技能、平台、团队和精力是否跟得上。",
        "advice": "先用小项目、作品或短期目标试一试，比只凭感觉选方向更稳。",
        "limit": "八字不知道你现在的真实职位，也不能保证升职或录用。",
    },
    "relationship": {
        "topic": "感情关系",
        "conclusion": (
            "看感情，可以聊你容易被什么吸引、怎样相处更容易稳定，"
            "但不能只凭八字判断你现在是否已婚或恋爱。"
        ),
        "condition": "关系能不能走下去，最终还要看双方意愿、沟通、边界和实际行动。",
        "advice": "少猜对方怎么想，多看真实沟通和承诺有没有落实。",
        "limit": "八字不知道你的现实婚姻状态，不能代替当事人的真实情况。",
    },
    "family": {
        "topic": "家庭相处",
        "conclusion": "看家庭，主要是看你在家里习惯扮演什么角色、怎么沟通，以及边界容易卡在哪里。",
        "condition": "具体关系好不好，还是取决于共同经历、生活安排和沟通方式。",
        "advice": "先分清是长期相处模式，还是偶尔一次冲突，再决定怎么处理。",
        "limit": "八字不能代替你的家庭经历，也不能断定现实关系是什么样。",
    },
    "health_advisory": {
        "topic": "身体和状态",
        "conclusion": "健康方面只从五行和季节提醒你留意作息、压力和精力变化，不拿八字诊断疾病。",
        "condition": "要不要调整生活习惯，还得看你的睡眠、饮食、运动和真实感受。",
        "advice": "如果不舒服一直持续，记下症状并及时找正规医生。",
        "limit": "我们不知道你的真实健康状况，这里不能代替医疗判断。",
    },
    "children": {
        "topic": "子女话题",
        "conclusion": "聊子女时，只能从时柱、十神和藏干说一些传统倾向，不能拿它预测具体结果。",
        "condition": "生育和养育会受到健康、个人选择、关系和家庭资源等很多因素影响。",
        "advice": "涉及生育健康或养育决定时，以真实沟通和专业意见为准。",
        "limit": "八字不知道现实生育情况，也不能断定数量、性别或结果。",
    },
    "education": {
        "topic": "学习方式",
        "conclusion": "看学业，重点是你可能更习惯怎么学、需要什么帮助，而不是直接断定成绩。",
        "condition": "真正学得怎么样，还要看基础、投入时间、教学环境和复习效果。",
        "advice": "用阶段测验和错题复盘看看方法有没有用，再调整节奏。",
        "limit": "八字不能代替成绩和能力评估，也不能保证考试或录取结果。",
    },
    "relocation": {
        "topic": "搬迁和异地发展",
        "conclusion": "看迁移，只能看你在哪些阶段更容易想换环境，以及变化来时是否接得住。",
        "condition": "真要搬家或去外地，还得同时解决工作、住处、成本、手续和支持网络。",
        "advice": "先算清成本，有条件可以试住，并准备备选工作和退出方案。",
        "limit": "八字不能证明你一定会搬迁，也不能保证异地发展顺利。",
    },
    "property": {
        "topic": "买房和置业",
        "conclusion": (
            "看房产，不能只问有没有买房运，更要看你的收入能不能扛住"
            "首付、月供和长期压力。"
        ),
        "condition": "准备行动前，要把首付、月供、应急储备、合同和退出办法都算进去。",
        "advice": "先做现金流压力测试，再单独核对产权、合同、利率和交易成本。",
        "limit": "八字不知道你现实中有多少资产，也不能保证买房结果。",
    },
    "benefactor": {
        "topic": "贵人和帮助",
        "conclusion": (
            "所谓贵人，不一定是突然出现的人，更常见的是某类角色、"
            "平台或合作机会愿意帮你一把。"
        ),
        "condition": "别人愿不愿意帮，通常还要看你有没有拿出能力、信用和互惠价值。",
        "advice": "把作品和能力准备好，需求说清楚，再用实际合作判断对方是否靠谱。",
        "limit": "八字不能保证某个人一定出现，也不能断定别人一定会帮你。",
    },
    "timing": {
        "topic": "什么时候更值得留意",
        "conclusion": "看时间，只说已经算出的这段大运、流年或流月，不猜材料里没有的年份。",
        "condition": "时间提示要拿现实中的资源和事情进展来对照，不能只看一个年份标签。",
        "advice": "在关键时间点回头检查进展，同时给自己留一个调整方案。",
        "limit": "没有提供的时间不补猜，提到某个阶段也不代表事情一定发生。",
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
    fact_text = "；".join(
        item.text.strip().rstrip("。；")
        for item in facts
        if item.text.strip().rstrip("。；")
    )
    while "。；" in fact_text or "。。" in fact_text:
        fact_text = fact_text.replace("。；", "；").replace("。。", "。")
    parts = [conclusion]
    if fact_text:
        parts.append(f"具体看这点：{fact_text}")
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
            "这张盘怎么看",
            "下面只说已经算出的内容，没有的信息不猜。",
            _dedupe_facts(chart_facts, 1),
            domain_rules,
            conditions=_conditions(
                content,
                "这些信息要和你问的事情、真实经历放在一起看",
            ),
            uncertainty=[f"限制：{content['limit']}"],
        ),
        _claim(
            f"{packet.resolved.domain}.action",
            "具体怎么做",
            "八字说的是倾向，真正有用的是拿它对照现实，找到现在能做、之后也能回头检查的办法。",
            _dedupe_facts(domain_facts, 1),
            safety_rules,
            conditions=_conditions(content, "行动前先看看现实条件是否允许"),
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
        return "这个阶段只按已经算出的时间信息来看。"
    return f"下面按时间先后看这{len(facts)}个阶段。"


def _timing_annotations(index: int) -> tuple[list[str], list[str]]:
    conditions = (
        ["条件：这里只看你问到、并且已经算出的时间范围。"]
        if index == 0
        else []
    )
    uncertainty = (
        ["限制：提到某个时间点，不等于事情一定会发生。"]
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
