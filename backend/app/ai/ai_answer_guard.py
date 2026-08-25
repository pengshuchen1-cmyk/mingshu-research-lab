"""Local factual and language guard for model-generated Bazi answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .ai_intent import (
    CURRENT_MARRIAGE_DISCLAIMER,
)
from .ai_models import AIRequestContext, BaziAIAnswer

DETERMINISTIC_PHRASES = (
    "一定会", "注定", "百分之百", "必然离婚", "肯定发财",
    "保证成功", "抵押房子一定能成", "必定", "绝对成功",
    "毫无疑问", "铁定",
)
_ABSOLUTE_CLAIM = re.compile(
    r"(?:必成|必发(?:财|达|家)|必赚(?:钱|到)|必赢|"
    r"保证[^，,。；;！？!?\r\n]{0,12}(?:成功|收益))"
)
_NEGATING_SUFFIXES = (
    "不能够", "不可能", "不能", "无法", "并非", "并不",
    "没有", "不太", "不可", "不", "未", "非",
)
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STRENGTH_TERMS = ("身强", "身弱", "中和", "从旺", "从弱")
PATTERN_TERMS = (
    "正官格", "七杀格", "正印格", "偏印格", "食神格", "伤官格",
    "正财格", "偏财格", "比肩格", "劫财格", "建禄格", "月刃格", "从旺格", "从弱格",
)
WEALTH_ELEMENT_BY_DAY_ELEMENT = {
    "木": "土", "火": "金", "土": "水", "金": "木", "水": "火",
}
_CURRENT_MARRIAGE_PREDICATE = re.compile(
    r"(?:"
    r"婚姻(?:登记)?(?:状态|状况)(?:为|是)(?:已婚|未婚)"
    r"|(?:属于|是|处于|仍是)(?:已婚|未婚)(?:人士|状态)?"
    r"|(?:已经结婚|结婚了|没有结婚|尚未结婚|仍未结婚)"
    r"|(?:有|无|没有)配偶"
    r"|(?:处于|仍处于|进入|维持)婚姻关系"
    r")"
)
_CURRENT_MARRIAGE_TENDENCY = re.compile(
    r"(?:更?偏向|倾向于?|大概率|很可能|较可能|可能|或许|未必|"
    r"不一定|不像)(?:认为|是|为)?[^，,。；;！？!?\r\n]{0,8}"
    r"(?:已经结婚|结婚|已婚|未婚|有配偶|无配偶|处于婚姻关系)"
)
_CLAUSE_SPLIT = re.compile(r"[，,。；;！？!?\r\n]+")
ELEMENTS = "木火土金水"
TEN_GODS = (
    "比肩", "劫财", "食神", "伤官", "正财",
    "偏财", "正官", "七杀", "正印", "偏印",
)
POSITION_KEYS = {"年": "year", "月": "month", "日": "day", "时": "hour"}


@dataclass(frozen=True)
class GuardResult:
    accepted: bool
    violations: tuple[str, ...]


def _string_facts(value: object) -> set[str]:
    values: set[str] = set()
    if isinstance(value, str):
        if len(value.strip()) >= 2:
            values.add(value.strip())
    elif isinstance(value, dict):
        for item in value.values():
            values.update(_string_facts(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.update(_string_facts(item))
    return values


def _has_unqualified_current_marriage_claim(text: str) -> bool:
    for clause in _CLAUSE_SPLIT.split(text):
        if not _CURRENT_MARRIAGE_PREDICATE.search(clause):
            continue
        if not _CURRENT_MARRIAGE_TENDENCY.search(clause):
            return True
    return False


def _is_negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 4):start]
    if any(prefix.endswith(value) for value in _NEGATING_SUFFIXES):
        return True
    clause_prefix = re.split(r"[，,。；;！？!?\r\n]+", text[:start])[-1]
    return bool(
        re.search(
            r"(?:不存在|谈不上)(?:任何|所谓|什么)?\s*$",
            clause_prefix,
        )
    )


def _has_deterministic_claim(text: str) -> bool:
    for phrase in DETERMINISTIC_PHRASES:
        for match in re.finditer(re.escape(phrase), text):
            if not _is_negated(text, match.start()):
                return True
    return any(
        not _is_negated(text, match.start())
        for match in _ABSOLUTE_CLAIM.finditer(text)
    )


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _overlaps_any(
    span: tuple[int, int],
    excluded_spans: list[tuple[int, int]],
) -> bool:
    start, end = span
    return any(
        start < excluded_end and end > excluded_start
        for excluded_start, excluded_end in excluded_spans
    )


def _claimed_elements(
    text: str,
    label_pattern: str,
    excluded_spans: list[tuple[int, int]] | None = None,
) -> set[str]:
    values: set[str] = set()
    excluded = excluded_spans or []
    for match in re.finditer(
        rf"(?:{label_pattern})(?:的?五行)?(?:为|是|属|：|:)?"
        rf"([{ELEMENTS}、，和及与]+)",
        text,
    ):
        if (
            _is_negated(text, match.start())
            or _overlaps_any(match.span(), excluded)
        ):
            continue
        values.update(char for char in match.group(1) if char in ELEMENTS)
    return values


def _ten_god_counts(ten_gods: dict) -> dict[str, int]:
    counts = {name: 0 for name in TEN_GODS}
    for raw in ten_gods.values():
        item = _mapping(raw)
        visible = str(item.get("gan") or "")
        if visible in counts:
            counts[visible] += 1
        hidden = item.get("hidden_stems")
        if isinstance(hidden, list):
            for raw_hidden in hidden:
                ten_god = str(_mapping(raw_hidden).get("ten_god") or "")
                if ten_god in counts:
                    counts[ten_god] += 1
    return counts


def _numeric_equal(claimed: str, expected: object) -> bool:
    try:
        return abs(float(claimed) - float(expected)) < 1e-9
    except (TypeError, ValueError):
        return False


def _contains_start_age(start: str, claimed: str) -> bool:
    before_start = start.split("起运", 1)[0]
    ages = re.findall(r"(\d+(?:\.\d+)?)\s*岁", before_start)
    ages.extend(
        re.findall(
            r"(?:约)?(\d+(?:\.\d+)?)\s*年(?:\d+\s*个月)?",
            before_start,
        )
    )
    return any(_numeric_equal(claimed, age) for age in ages)


def _has_canonical_fact_contradiction(
    combined: str,
    facts: dict[str, object],
) -> tuple[str, ...]:
    """Validate explicit machine-checkable claims in the natural answer.

    Free-form interpretation remains allowed. Once the model states a concrete
    value that the canonical projection can check, a mismatch is rejected.
    """
    violations: list[str] = []
    strength = _mapping(facts.get("strength"))
    favorable = set(strength.get("favorable_elements") or [])
    unfavorable = set(strength.get("unfavorable_elements") or [])
    claimed_non_favorable: set[str] = set()
    claimed_not_unfavorable: set[str] = set()
    negated_disposition_spans: list[tuple[int, int]] = []
    for match in re.finditer(
        rf"(?:(?:此命|命局|此局)\s*)?(?:并不|不太|不)\s*喜(?:用)?"
        rf"(?:为|是|属|：|:)?\s*([{ELEMENTS}、和及与]+)",
        combined,
    ):
        negated_disposition_spans.append(match.span())
        claimed_non_favorable.update(
            char for char in match.group(1) if char in ELEMENTS
        )
    for match in re.finditer(
        rf"(?:(?:此命|命局|此局)\s*)?(?:并不|不太|不)\s*忌(?:用)?"
        rf"(?:为|是|属|：|:)?\s*([{ELEMENTS}、和及与]+)",
        combined,
    ):
        negated_disposition_spans.append(match.span())
        claimed_not_unfavorable.update(
            char for char in match.group(1) if char in ELEMENTS
        )
    claimed_favorable = _claimed_elements(
        combined,
        r"喜用五行|喜用神|喜神|用神|有利五行",
        negated_disposition_spans,
    )
    claimed_unfavorable = _claimed_elements(
        combined,
        r"忌用五行|忌神|不利五行",
        negated_disposition_spans,
    )
    for match in re.finditer(
        rf"(?<![欢不太])(?:(?:此命|命局|此局)\s*)?喜(?:用)?"
        rf"(?:为|是|属|：|:)?\s*([{ELEMENTS}、和及与]+)",
        combined,
    ):
        if _overlaps_any(match.span(), negated_disposition_spans):
            continue
        claimed_favorable.update(
            char for char in match.group(1) if char in ELEMENTS
        )
    for match in re.finditer(
        rf"(?<![不太])(?:(?:此命|命局|此局)\s*)?忌(?:用)?"
        rf"(?:为|是|属|：|:)?\s*([{ELEMENTS}、和及与]+)",
        combined,
    ):
        if _overlaps_any(match.span(), negated_disposition_spans):
            continue
        claimed_unfavorable.update(
            char for char in match.group(1) if char in ELEMENTS
        )
    for elements, disposition in re.findall(
        rf"以\s*([{ELEMENTS}、和及与]+)\s*为\s*(喜(?:用)?|忌(?:用)?)",
        combined,
    ):
        target = (
            claimed_favorable
            if disposition.startswith("喜")
            else claimed_unfavorable
        )
        target.update(char for char in elements if char in ELEMENTS)
    if claimed_favorable and (
        not favorable or not claimed_favorable.issubset(favorable)
    ):
        violations.append("favorable_element_contradiction")
    if claimed_unfavorable and (
        not unfavorable or not claimed_unfavorable.issubset(unfavorable)
    ):
        violations.append("unfavorable_element_contradiction")
    if claimed_non_favorable and (
        not favorable or bool(claimed_non_favorable & favorable)
    ):
        violations.append("favorable_element_contradiction")
    if claimed_not_unfavorable and (
        not unfavorable or bool(claimed_not_unfavorable & unfavorable)
    ):
        violations.append("unfavorable_element_contradiction")

    element_counts = _mapping(facts.get("element_counts"))
    for element, claimed in re.findall(
        rf"(?:五行中)?([{ELEMENTS}])(?:元素)?(?:的)?"
        r"(?:数量|个数|计数|共有|共|有|为|是)"
        r"(?:为|是)?\s*(\d+(?:\.\d+)?)",
        combined,
    ):
        if element not in element_counts or not _numeric_equal(
            claimed, element_counts[element]
        ):
            violations.append("element_count_contradiction")
            break

    ten_gods = _mapping(facts.get("ten_gods"))
    ten_god_pattern = "|".join(TEN_GODS)
    for position, claimed in re.findall(
        rf"([年月日时])干(?:的?十神)?(?:为|是|属)\s*({ten_god_pattern})",
        combined,
    ):
        expected = str(_mapping(ten_gods.get(POSITION_KEYS[position])).get("gan") or "")
        if not expected or claimed != expected:
            violations.append("ten_god_contradiction")
            break
    try:
        from ..bazi.ten_gods import get_ten_god
    except Exception:
        get_ten_god = None
    day_master = str(facts.get("day_master") or "")
    for stem, claimed in re.findall(
        rf"(?:藏干)?([{STEMS}])(?:的?十神)?(?:为|是|属|对应)\s*"
        rf"({ten_god_pattern})",
        combined,
    ):
        expected = get_ten_god(day_master, stem) if get_ten_god else ""
        if not expected or claimed != expected:
            violations.append("ten_god_contradiction")
            break
    counts = _ten_god_counts(ten_gods)
    for ten_god, claimed in re.findall(
        rf"({ten_god_pattern})(?:星)?(?:共有|共计|共|有|为|是)\s*"
        r"(\d+)\s*个?",
        combined,
    ):
        if not ten_gods or int(claimed) != counts[ten_god]:
            violations.append("ten_god_count_contradiction")
            break

    dayun = _mapping(facts.get("dayun"))
    expected_direction = str(dayun.get("direction") or "")
    claimed_directions = re.findall(
        r"(?:大运|起运)(?:的)?方向(?:为|是|：|:)?\s*(顺排|逆排|顺行|逆行)",
        combined,
    )
    if claimed_directions and (
        not expected_direction
        or any(
            ("顺" in claimed) != ("顺" in expected_direction)
            for claimed in claimed_directions
        )
    ):
        violations.append("dayun_contradiction")
    expected_start = str(dayun.get("start") or "")
    claimed_ages = re.findall(r"(\d+(?:\.\d+)?)\s*岁(?:左右|前后)?起运", combined)
    if claimed_ages and (
        not expected_start
        or any(not _contains_start_age(expected_start, age) for age in claimed_ages)
    ):
        violations.append("dayun_contradiction")
    current = _mapping(facts.get("current_context"))
    current_luck = str(
        current.get("current_dayun_pillar")
        or current.get("dayun_pillar")
        or current.get("luck_pillar")
        or ""
    )
    claimed_luck = re.findall(
        rf"(?:当前|现在|本步)(?:大运|行运)(?:柱)?(?:为|是|：|:)?"
        rf"\s*([{STEMS}][{BRANCHES}])",
        combined,
    )
    if claimed_luck and (
        not current_luck or any(item != current_luck for item in claimed_luck)
    ):
        violations.append("dayun_contradiction")

    raw_dayun_periods = facts.get("dayun_periods")
    dayun_periods = [
        _mapping(item)
        for item in raw_dayun_periods
        if isinstance(raw_dayun_periods, list) and isinstance(item, dict)
    ] if isinstance(raw_dayun_periods, list) else []

    def period_matches(
        *,
        pillar: str,
        ten_god: str = "",
        start_year: str = "",
        end_year: str = "",
        start_age: str = "",
    ) -> bool:
        for period in dayun_periods:
            if str(period.get("pillar") or "") != pillar:
                continue
            if ten_god and str(period.get("ten_god") or "") != ten_god:
                continue
            if start_year and not _numeric_equal(
                start_year, period.get("start_year")
            ):
                continue
            if end_year and not _numeric_equal(end_year, period.get("end_year")):
                continue
            if start_age and not _numeric_equal(start_age, period.get("start_age")):
                continue
            return True
        return False

    dayun_ten_god_pattern = "|".join(TEN_GODS)
    for pillar, ten_god in re.findall(
        rf"([{STEMS}][{BRANCHES}])(?:属于|为|是)?"
        rf"\s*({dayun_ten_god_pattern})大运",
        combined,
    ):
        if not period_matches(pillar=pillar, ten_god=ten_god):
            violations.append("dayun_contradiction")
            break
    for start_year, end_year, pillar, ten_god in re.findall(
        rf"((?:19|20)\d{{2}})\s*[—–~-]\s*((?:19|20)\d{{2}})年"
        rf"(?:的|为)?\s*([{STEMS}][{BRANCHES}])"
        rf"(?:({dayun_ten_god_pattern}))?大运",
        combined,
    ):
        if not period_matches(
            pillar=pillar,
            ten_god=ten_god,
            start_year=start_year,
            end_year=end_year,
        ):
            violations.append("dayun_contradiction")
            break
    for year, pillar, ten_god in re.findall(
        rf"((?:19|20)\d{{2}})年[^，,。；;！？!?\r\n]{{0,16}}?"
        rf"(?:开始|进入|转入|步入|起)[^，,。；;！？!?\r\n]{{0,10}}?"
        rf"([{STEMS}][{BRANCHES}])(?:({dayun_ten_god_pattern}))?大运",
        combined,
    ):
        if not period_matches(
            pillar=pillar,
            ten_god=ten_god,
            start_year=year,
        ):
            violations.append("dayun_contradiction")
            break
    for pillar, ten_god, year in re.findall(
        rf"([{STEMS}][{BRANCHES}])(?:({dayun_ten_god_pattern}))?大运"
        rf"[^，,。；;！？!?\r\n]{{0,16}}?"
        rf"(?:从|于)?((?:19|20)\d{{2}})年(?:开始|起|进入|转入)",
        combined,
    ):
        if not period_matches(
            pillar=pillar,
            ten_god=ten_god,
            start_year=year,
        ):
            violations.append("dayun_contradiction")
            break
    for age, pillar, ten_god in re.findall(
        rf"(\d{{1,3}})岁(?:左右|前后)?"
        rf"[^，,。；;！？!?\r\n]{{0,12}}?(?:开始|进入|转入|步入|起)"
        rf"[^，,。；;！？!?\r\n]{{0,10}}?"
        rf"([{STEMS}][{BRANCHES}])(?:({dayun_ten_god_pattern}))?大运",
        combined,
    ):
        if not period_matches(
            pillar=pillar,
            ten_god=ten_god,
            start_age=age,
        ):
            violations.append("dayun_contradiction")
            break

    target_years = facts.get("target_years")
    year_pillars: dict[str, str] = {}
    if current.get("year") and current.get("year_pillar"):
        year_pillars[str(current["year"])] = str(current["year_pillar"])
    if isinstance(target_years, list):
        for raw in target_years:
            target = _mapping(raw)
            if target.get("year") and target.get("year_pillar"):
                year_pillars[str(target["year"])] = str(target["year_pillar"])
    for year, pillar in re.findall(
        rf"((?:19|20)\d{{2}})年(?:的)?(?:流年|年)柱(?:为|是|：|:)?"
        rf"\s*([{STEMS}][{BRANCHES}])",
        combined,
    ):
        if year not in year_pillars or pillar != year_pillars[year]:
            violations.append("timing_fact_contradiction")
            break
    pillars = facts.get("pillars")
    natal_pillars = {
        "月": (
            str(pillars[1])
            if isinstance(pillars, list) and len(pillars) >= 2
            else ""
        ),
        "日": (
            str(pillars[2])
            if isinstance(pillars, list) and len(pillars) >= 3
            else ""
        ),
    }
    current_keys = {"月": "month_pillar", "日": "day_pillar"}
    current_spans: list[tuple[int, int]] = []
    for match in re.finditer(
        rf"(当前|当月|本月|今日|当天)([月日])?柱"
        rf"(?:为|是|：|:)?\s*([{STEMS}][{BRANCHES}])",
        combined,
    ):
        scope, explicit_label, claimed = match.groups()
        label = explicit_label or (
            "月" if scope in {"当月", "本月"} else
            "日" if scope in {"今日", "当天"} else ""
        )
        if not label:
            continue
        current_spans.append(match.span())
        expected = str(current.get(current_keys[label]) or "")
        if not expected or claimed != expected:
            violations.append("timing_fact_contradiction")
    for match in re.finditer(
        rf"([月日])柱(?:为|是|：|:)?\s*([{STEMS}][{BRANCHES}])",
        combined,
    ):
        if any(
            start <= match.start() and match.end() <= end
            for start, end in current_spans
        ):
            continue
        label, claimed = match.groups()
        expected = natal_pillars[label]
        if not expected or claimed != expected:
            violations.append("natal_pillar_contradiction")

    day_pillar = (
        str(pillars[2])
        if isinstance(pillars, list) and len(pillars) >= 3
        else ""
    )
    spouse_palace = day_pillar[1:2]
    spouse_claims = re.findall(
        rf"(?:夫妻宫|婚姻宫|配偶宫)(?:地支)?(?:为|是|：|:)?\s*([{BRANCHES}])",
        combined,
    )
    if spouse_claims and (
        not spouse_palace or any(item != spouse_palace for item in spouse_claims)
    ):
        violations.append("relationship_fact_contradiction")
    relationship = _mapping(facts.get("relationship"))
    signals = relationship.get("stability_signals")
    signal_text = json.dumps(signals or [], ensure_ascii=False)
    explicit_clash = re.search(
        rf"(?:(?:命盘|本命|盘中|夫妻宫|婚姻宫)(?:存在|有)"
        rf"[^，。；\r\n]{{0,8}}冲|[{BRANCHES}][{BRANCHES}]冲)",
        combined,
    )
    explicit_no_clash = re.search(
        r"(?:命盘|本命|盘中|夫妻宫|婚姻宫)(?:不存在|没有|无)"
        r"[^，。；\r\n]{0,8}冲",
        combined,
    )
    if explicit_clash and "冲为无" in signal_text:
        violations.append("relationship_fact_contradiction")
    if explicit_no_clash and (
        "冲为无" not in signal_text and "无冲" not in signal_text
    ):
        violations.append("relationship_fact_contradiction")
    explicit_combine = re.search(
        rf"(?:(?:命盘|本命|盘中|夫妻宫|婚姻宫)(?:存在|有)"
        rf"[^，。；\r\n]{{0,8}}合|[{BRANCHES}][{BRANCHES}]合)",
        combined,
    )
    explicit_no_combine = re.search(
        r"(?:命盘|本命|盘中|夫妻宫|婚姻宫)(?:不存在|没有|无)"
        r"[^，。；\r\n]{0,8}合",
        combined,
    )
    if explicit_combine and "合为无" in signal_text:
        violations.append("relationship_fact_contradiction")
    if explicit_no_combine and (
        "合为无" not in signal_text and "无合" not in signal_text
    ):
        violations.append("relationship_fact_contradiction")
    peach_counts = re.findall(
        r"桃花(?:星)?(?:共有|共计|共|有|为|是)\s*(\d+)\s*个?",
        combined,
    )
    canonical_peach_count = relationship.get("peach_count")
    if peach_counts and (
        canonical_peach_count is None
        or any(
            not _numeric_equal(claimed, canonical_peach_count)
            for claimed in peach_counts
        )
    ):
        violations.append("relationship_fact_contradiction")
    return tuple(dict.fromkeys(violations))


def _validate_combined_text(
    combined: str,
    context: AIRequestContext,
    *,
    require_marriage_disclaimer: bool,
) -> tuple[str, ...]:
    violations: list[str] = []
    if _has_deterministic_claim(combined):
        violations.append("deterministic_claim")
    violations.extend(
        _has_canonical_fact_contradiction(combined, context.chart_facts)
    )
    if require_marriage_disclaimer and (
        context.category == "relationship"
        and context.current_marriage_status_requested
    ) and (
        not combined.strip().startswith(
            CURRENT_MARRIAGE_DISCLAIMER
        )
        or _has_unqualified_current_marriage_claim(combined)
    ):
        violations.append("current_marriage_status_claim")

    chart_payload = json.dumps(context.chart_facts, ensure_ascii=False)
    authorized_pillars = set(re.findall(f"[{STEMS}][{BRANCHES}]", chart_payload))
    mentioned_pillars = set(re.findall(f"[{STEMS}][{BRANCHES}]", combined))
    rule_text = "。".join(item["statement"] for item in context.rule_evidence)
    unauthorized = {
        pillar for pillar in mentioned_pillars
        if pillar not in authorized_pillars and pillar not in rule_text
    }
    day_master = str(context.chart_facts.get("day_master", ""))
    mentioned_day_masters = set(re.findall(f"([{STEMS}])日主", combined))
    if unauthorized or any(stem != day_master for stem in mentioned_day_masters):
        violations.append("chart_fact_contradiction")

    expected_gender = str(context.chart_facts.get("gender", ""))
    mentioned_genders = {term for term in ("男命", "女命") if term in combined}
    expected_gender_term = "女命" if expected_gender == "female" else "男命"
    if mentioned_genders and mentioned_genders != {expected_gender_term}:
        violations.append("gender_contradiction")

    pattern = context.chart_facts.get("pattern", {})
    expected_pattern = str(pattern.get("classification", "")) if isinstance(pattern, dict) else str(pattern)
    mentioned_patterns = {term for term in PATTERN_TERMS if term in combined}
    if mentioned_patterns and any(term not in expected_pattern for term in mentioned_patterns):
        violations.append("pattern_contradiction")

    try:
        from ..bazi.bazi_constants import STEM_ELEMENTS

        wealth_element = WEALTH_ELEMENT_BY_DAY_ELEMENT.get(STEM_ELEMENTS.get(day_master, ""), "")
    except Exception:
        wealth_element = ""
    claimed_wealth_elements = {
        value
        for match in re.findall(
            r"财星(?:的?五行)?(?:为|是|属)([木火土金水])(?:也为([木火土金水]))?",
            combined,
        )
        for value in match
        if value
    }
    if claimed_wealth_elements and claimed_wealth_elements != {wealth_element}:
        violations.append("wealth_element_contradiction")

    spouse_claims = {
        value
        for match in re.findall(
            r"(?:配偶星|妻星|夫星)(?:为|是|属)(财星|官杀|官星|印星|食伤|比劫)"
            r"(?:也为(财星|官杀|官星|印星|食伤|比劫))?",
            combined,
        )
        for value in match
        if value
    }
    spouse_claims.update(
        re.findall(r"以(财星|官杀|官星|印星|食伤|比劫)为(?:配偶星|妻星|夫星)", combined)
    )
    spouse_claims = {"官杀" if value == "官星" else value for value in spouse_claims}
    expected_spouse = "官杀" if expected_gender == "female" else "财星"
    wrong_relation_label = (
        ("妻星" in combined and expected_gender == "female")
        or ("夫星" in combined and expected_gender == "male")
    )
    if wrong_relation_label or (spouse_claims and spouse_claims != {expected_spouse}):
        violations.append("spouse_star_contradiction")

    strength = context.chart_facts.get("strength", {})
    if isinstance(strength, dict):
        expected_strength = str(strength.get("classification", ""))
        mentioned_strength = {term for term in STRENGTH_TERMS if term in combined}
        if mentioned_strength and mentioned_strength != {expected_strength}:
            violations.append("strength_contradiction")

    return tuple(dict.fromkeys(violations))


def validate_ai_text(text: str, context: AIRequestContext) -> GuardResult:
    """Validate factual and deterministic claims in one natural-text segment."""
    violations = _validate_combined_text(
        text,
        context,
        require_marriage_disclaimer=False,
    )
    return GuardResult(accepted=not violations, violations=violations)


def validate_ai_answer(answer: BaziAIAnswer, context: AIRequestContext) -> GuardResult:
    combined = "。".join(
        [
            answer.analysis_conclusion,
            *answer.chart_evidence,
            *answer.rule_evidence,
            *answer.timing_conditions,
            *answer.practical_advice,
            *answer.uncertainty_limitations,
        ]
    )
    violations = list(
        _validate_combined_text(
            combined,
            context,
            require_marriage_disclaimer=True,
        )
    )
    chart_payload = json.dumps(context.chart_facts, ensure_ascii=False)
    authorized_pillars = set(
        re.findall(f"[{STEMS}][{BRANCHES}]", chart_payload)
    )
    day_master = str(context.chart_facts.get("day_master", ""))
    strength = context.chart_facts.get("strength", {})
    authorized_facts = _string_facts(context.chart_facts)
    authorized_facts.update(authorized_pillars)
    if day_master:
        authorized_facts.add(f"{day_master}日主")
    if isinstance(strength, dict) and strength.get("classification"):
        authorized_facts.add(str(strength["classification"]))
    if answer.chart_evidence and not all(
        any(fact in item or item in fact for fact in authorized_facts)
        for item in answer.chart_evidence
    ):
        violations.append("unmapped_chart_evidence")
    rule_statements = [item["statement"] for item in context.rule_evidence]
    if answer.rule_evidence and not all(
        any(statement in item or item in statement for statement in rule_statements)
        for item in answer.rule_evidence
    ):
        violations.append("unmapped_rule_evidence")

    unique = tuple(dict.fromkeys(violations))
    return GuardResult(accepted=not unique, violations=unique)
