"""Compile a resolved question into privacy-safe, locally traceable facts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Mapping

from core.ai_context import DOMAIN_RULE_IDS, redact_customer_text
from core.ai_domain_facts import domain_fact_items
from core.ai_models import FactItem, FactPacket, ResolvedQuestion
from core.bazi_rulebook import load_rulebook
from core.chart_facts import ChartFacts, chart_facts_from_chart
from core.luck_engine import get_luck_cycles
from core.monthly_engine import analyze_monthly_fortune
from core.yearly_engine import analyze_yearly_fortune, get_year_pillar


class FactCompilationError(ValueError):
    pass


def _clip(value: object, limit: int = 500) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def _fact(
    item_id: str,
    kind: str,
    text: str,
    source: str,
) -> FactItem:
    return FactItem(
        id=item_id,
        kind=kind,
        text=_clip(text),
        source=source,
    )


def _base_fact_items(facts: ChartFacts) -> list[FactItem]:
    items = [
        _fact(
            "chart.pillars",
            "chart",
            f"四柱为{'、'.join(pillar for pillar in facts.pillars if pillar)}。",
            "chart",
        ),
        _fact(
            "chart.day_master_strength",
            "chart",
            (
                f"日主为{facts.day_master}，强弱为{facts.strength}；"
                f"喜用五行为{'、'.join(facts.favorable_elements)}；"
                f"需审慎观察的五行为{'、'.join(facts.unfavorable_elements)}。"
            ),
            "chart",
        ),
    ]
    if facts.pattern:
        items.append(_fact("chart.pattern", "chart", facts.pattern, "chart"))
    if facts.wealth:
        items.append(_fact("chart.wealth", "chart", facts.wealth, "chart"))
    return [item for item in items if item.text]


def _parse_birth_date(chart: Mapping[str, object]) -> date | None:
    profile = chart.get("profile")
    if not isinstance(profile, Mapping):
        return None
    raw = profile.get("birth_date")
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None


def _anniversary(birth: date, year: int) -> date:
    try:
        return birth.replace(year=year)
    except ValueError:
        return birth.replace(year=year, day=28)


def _age_ranges(
    chart: Mapping[str, object],
    resolved: ResolvedQuestion,
) -> list[tuple[int, date, date, str]]:
    birth = _parse_birth_date(chart)
    if birth is None:
        return []
    ranges = []
    for age in resolved.age_values:
        if resolved.age_mode == "solar_age":
            start = _anniversary(birth, birth.year + age)
            end = _anniversary(birth, birth.year + age + 1) - timedelta(days=1)
            label = f"{age}周岁"
        elif resolved.age_mode == "nominal_age":
            target_year = birth.year + age - 1
            start = date(target_year, 1, 1)
            end = date(target_year, 12, 31)
            label = f"{age}虚岁"
        else:
            continue
        ranges.append((age, start, end, label))
    return ranges


def _age_items(
    chart: Mapping[str, object],
    resolved: ResolvedQuestion,
) -> list[FactItem]:
    return [
        _fact(
            f"age.{resolved.age_mode}.{age}",
            "age",
            f"{label}对应本地公历范围：{start.isoformat()}至{end.isoformat()}。",
            "chart",
        )
        for age, start, end, label in _age_ranges(chart, resolved)
    ]


def _periods(luck: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw = luck.get("dayun_list")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, Mapping)]


def _period_is_relevant(
    period: Mapping[str, object],
    resolved: ResolvedQuestion,
) -> bool:
    if resolved.time_scope == "dayun":
        return True
    try:
        start_age = int(period["start_age"])
        end_age = int(period["end_age"])
        start_year = int(period["start_year"])
        end_year = int(period["end_year"])
    except (KeyError, TypeError, ValueError):
        return False
    if any(start_age <= age <= end_age for age in resolved.age_values):
        return True
    return any(start_year <= year <= end_year for year in resolved.target_years)


def _dayun_items(
    luck: Mapping[str, object],
    resolved: ResolvedQuestion,
) -> list[FactItem]:
    items = []
    for index, period in enumerate(_periods(luck), start=1):
        if not _period_is_relevant(period, resolved):
            continue
        try:
            pillar = str(period["pillar"]).strip()
            start_age = int(period["start_age"])
            end_age = int(period["end_age"])
            start_date = date.fromisoformat(str(period["start_date"]))
            end_date = date.fromisoformat(str(period["end_date"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not pillar:
            continue
        ten_god = str(period.get("ten_god") or "").strip()
        suffix = f"；天干十神为{ten_god}" if ten_god else ""
        items.append(
            _fact(
                f"dayun.{index}",
                "dayun",
                (
                    f"{pillar}大运：{start_age}—{end_age}岁；"
                    f"本地公历区间{start_date.isoformat()}至{end_date.isoformat()}"
                    f"{suffix}。"
                ),
                "dayun",
            )
        )
    return items


def _year_items(
    chart: dict,
    luck: Mapping[str, object],
    year: int,
) -> list[FactItem]:
    pillar = get_year_pillar(year)
    yearly = analyze_yearly_fortune(chart, year, dict(luck))
    if not isinstance(yearly, Mapping):
        return []
    parts = [f"{year}年流年为{pillar}"]
    for key, label in (
        ("ten_god", "天干十神"),
        ("branch_ten_god", "地支主气十神"),
        ("relation_to_favorable", "与命盘喜忌关系"),
        ("overall_level", "本地层级"),
    ):
        value = str(yearly.get(key) or "").strip()
        if value:
            parts.append(f"{label}为{value}")
    return [
        _fact(
            f"year.{year}",
            "year",
            "；".join(parts) + "。",
            "year",
        )
    ]


def _month_items(
    chart: dict,
    year: int,
    target_months: list[int],
) -> list[FactItem]:
    monthly = analyze_monthly_fortune(chart, year)
    if not isinstance(monthly, list):
        return []
    selected = set(target_months)
    items = []
    for raw in monthly:
        if not isinstance(raw, Mapping):
            continue
        try:
            month = int(raw["month"])
        except (KeyError, TypeError, ValueError):
            continue
        if month not in selected:
            continue
        pillar = str(raw.get("pillar") or "").strip()
        if not pillar:
            continue
        parts = [f"{year}年{month}月流月为{pillar}"]
        for key, label in (
            ("ten_god", "天干十神"),
            ("relation_to_favorable", "与命盘喜忌关系"),
            ("theme", "本地主题"),
        ):
            value = str(raw.get(key) or "").strip()
            if value:
                parts.append(f"{label}为{value}")
        items.append(
            _fact(
                f"month.{year}.{month}",
                "month",
                "；".join(parts) + "。",
                "month",
            )
        )
    return items


def _rules_for_domain(
    rule_ids: tuple[str, ...],
    resolved: ResolvedQuestion,
) -> list[dict[str, str]]:
    selected = list(rule_ids)
    selected.extend(DOMAIN_RULE_IDS.get(resolved.domain, ()))
    for subdomain in resolved.subdomains:
        selected.extend(DOMAIN_RULE_IDS.get(subdomain, ()))
    selected.extend(("SAFETY-NONDETERMINISTIC", "SAFETY-STATUS-UNKNOWN"))
    book = load_rulebook()
    evidence = []
    for rule_id in dict.fromkeys(selected):
        try:
            rule = book.by_id(rule_id)
        except KeyError:
            continue
        evidence.append({"id": rule.id, "statement": rule.statement})
    return evidence


def _dedupe(items: list[FactItem]) -> list[FactItem]:
    unique = {}
    for item in items:
        unique.setdefault(item.id, item)
    return list(unique.values())


def compile_fact_packet(chart: dict, resolved: ResolvedQuestion) -> FactPacket:
    if resolved.ambiguity:
        raise FactCompilationError(resolved.ambiguity)
    facts = chart_facts_from_chart(chart)
    items = _base_fact_items(facts)
    luck = get_luck_cycles(chart.get("profile", {}), chart)
    items.extend(_age_items(chart, resolved))
    items.extend(_dayun_items(luck, resolved))
    for year in resolved.target_years:
        items.extend(_year_items(chart, luck, year))
        if resolved.target_months:
            items.extend(_month_items(chart, year, resolved.target_months))
    items.extend(domain_fact_items(chart, resolved.domain))
    rules = _rules_for_domain(facts.rule_ids, resolved)
    safe_resolved = resolved.model_copy(
        update={"safe_question": redact_customer_text(resolved.safe_question)}
    )
    return FactPacket(
        resolved=safe_resolved,
        facts=_dedupe(items),
        rule_evidence=rules,
    )
