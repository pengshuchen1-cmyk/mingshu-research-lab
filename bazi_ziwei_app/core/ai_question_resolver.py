"""Deterministically resolve Bazi question time scopes."""

from __future__ import annotations

import re
from datetime import datetime

from core.ai_intent import is_current_marriage_question
from core.ai_models import ResolvedQuestion
from core.ai_scope_gate import check_bazi_scope
from core.yearly_engine import get_year_pillar


_DOMAIN_TERMS = (
    ("wealth", ("财运", "正财", "偏财", "赚钱", "收入", "投资", "创业", "房贷", "抵押")),
    ("career", ("事业", "工作", "职业", "升职", "行业", "岗位", "官运")),
    ("relationship", ("姻缘", "桃花", "婚姻", "对象", "感情", "结婚", "配偶")),
    ("family", ("原生家庭", "父母", "长辈", "家庭")),
    ("health_advisory", ("健康", "身体", "作息", "精力")),
    ("children", ("子女", "孩子", "生育", "养育")),
    ("education", ("学业", "学习", "考试", "升学")),
    ("relocation", ("迁移", "外地", "出国", "搬家", "异地")),
    ("property", ("房产", "买房", "置业", "住房")),
    ("benefactor", ("贵人", "助力", "提携", "平台资源", "合作资源")),
)

_CN = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}

_MONTHLY_TERMS = ("每个月", "每月", "逐月", "流月")
_WHEN_LUCK_WORD = r"(?:什么时候|啥时候|何时|几时|哪几年|哪一年)"
_LUCK_TOPIC = r"(?:财运|事业运|婚运)"
_WHEN_LUCK_EXPRESSION = "".join(
    (
        r"(?:",
        _WHEN_LUCK_WORD,
        r"[^，。；！？!?]{0,12}?",
        r"(?:走|有|进入|开始走|开始有)?",
        _LUCK_TOPIC,
        r"|(?:走财运|赚钱)[^，。；！？!?]{0,12}?",
        r"(?:什么时候|啥时候|何时|几时|哪几年|哪一年|是在几年)",
        r"|",
        _LUCK_TOPIC,
        r"[^，。；！？!?]{0,8}?",
        _WHEN_LUCK_WORD,
        r"(?:来|到|开始|出现)?",
        r")",
    )
)
_WHEN_LUCK_REQUEST = re.compile(_WHEN_LUCK_EXPRESSION)
_EXPLICIT_DAYUN_REQUEST = re.compile(r"(?:大运|行运|起运)")
_WHEN_LUCK_NEGATION = (
    r"(?:不是(?:想|要|希望|需要)?|并非(?:想|要|希望|需要)?|"
    r"不需要|不要|无需|无须|不用|不想|不必|甭|不|别)(?:再)?"
)
_WHEN_LUCK_NEGATION_OPERATOR = re.compile(_WHEN_LUCK_NEGATION)
_WHEN_LUCK_DOUBLE_NEGATION = re.compile(
    r"(?:"
    r"(?:并)?不是不(?:想|要|希望|需要)?"
    r"|并非不(?:想|要|希望|需要)?"
    r"|(?:不得不|不能不|不会不|不可能不)(?:想|要|希望|需要)?"
    r")"
)
_WHEN_LUCK_POSITIVE_OPERATOR = re.compile(
    r"(?:还是|但|不过|改为|改成|请|想|希望|需要|要|麻烦)"
)
_WHEN_LUCK_INTENT_VERB = re.compile(
    r"(?:问|看|分析|判断|了解|讨论|回答|知道|告诉|说|关心|聊|考虑)"
)
_NEGATED_MONTHLY_REQUEST = re.compile(
    r"(?:不需要|不想|无需|不要|不看|不用|别)(?:看)?\s*"
    r"(?:(?:今年|明年|后年|(?:19|20)\d{2}年?|上半年|下半年|"
    r"[一二三四五六七八九十\d]+月)\s*)*"
    r"(?:每个月|每月|逐月|流月)"
)
_POST_MONTHLY_NEGATION = re.compile(
    r"(?:每个月|每月|逐月|流月)[^，。；！？!?]{0,12}"
    r"(?:不需要|不想|无需|不要|不看|不用|别)(?:看)?"
    r"(?:每个月|每月|逐月|流月)(?:看)?"
)
_BIRTH_CONTEXT_TERMS = ("出生", "生日", "生于", "诞生")
_FOLLOW_UP_CUES = ("那", "继续", "后面", "刚才")
_FOLLOW_UP_CANCEL = re.compile(
    r"(?:"
    r"(?:不需要|不要|无需|无须|不用|不想|不必|别)"
    r"(?:再)?(?:帮我|给我|去|来|先|一下|\s)*"
    r"(?:问|看|分析|判断|了解|讨论|回答|继续|知道|告诉|说)"
    r"|(?:^|[，,。；;！？!?\r\n])(?:那)?(?:就)?"
    r"(?:不用|不要|不继续|别继续|算了|到此为止)(?:了)?(?:吧)?$"
    r")"
)
_FOLLOW_UP_SCOPE_RESET = re.compile(r"(?:整体|总体|综合|概括|大体)")
_CLAUSE_BOUNDARY = re.compile(r"[，,。；;！？!?\r\n]")


def _number(value: str) -> int:
    if value.isdigit():
        return int(value)
    if value == "十":
        return 10
    if value.startswith("十"):
        return 10 + _CN[value[-1]]
    if value.endswith("十"):
        return _CN[value[0]] * 10
    if "十" in value:
        left, right = value.split("十", 1)
        return _CN[left] * 10 + _CN[right]
    return _CN[value]


def _domain(text: str, previous: ResolvedQuestion | None) -> str:
    for name, terms in _DOMAIN_TERMS:
        if any(term in text for term in terms):
            return name
    return previous.domain if previous and len(text) <= 20 else "overview"


def _has_explicit_domain(text: str) -> bool:
    return any(term in text for _, terms in _DOMAIN_TERMS for term in terms)


def _years(text: str, current_year: int) -> tuple[list[int], bool]:
    range_match = re.search(
        r"((?:19|20)\d{2})\s*(?:年)?\s*(?:到|至|—|-)\s*((?:19|20)\d{2})",
        text,
    )
    if range_match:
        start, end = map(int, range_match.groups())
        return (list(range(start, end + 1)), False) if start <= end else ([], True)
    explicit = [int(value) for value in re.findall(r"((?:19|20)\d{2})(?=年)", text)]
    if explicit:
        return list(dict.fromkeys(explicit)), False
    if "明年" in text:
        return [current_year + 1], False
    if "后年" in text:
        return [current_year + 2], False
    after = re.search(r"([一二三四五六七八九十\d]+)年后", text)
    if after:
        return [current_year + _number(after.group(1))], False
    future = re.search(r"未来([一二三四五六七八九十\d]+)年", text)
    if future:
        number = _number(future.group(1))
        # Keep a 61-item sentinel so the caller can report the contract
        # violation without allocating an unbounded range from user input.
        number = min(61, number)
        return list(range(current_year, current_year + number)), False
    if "今年" in text or "上半年" in text or "下半年" in text:
        return [current_year], False
    return [], False


def _has_explicit_year_range(text: str) -> bool:
    return bool(
        re.search(
            r"(?:19|20)\d{2}\s*(?:年)?\s*(?:到|至|—|-)\s*(?:19|20)\d{2}",
            text,
        )
    )


def _discrete_year_receipt(years: list[int]) -> str:
    entries = [f"{year}年（{get_year_pillar(year)}）" for year in years]
    receipt = f"本次按{'、'.join(entries)}分析。"
    if len(receipt) <= 240:
        return receipt
    return f"本次按{len(years)}个离散年份分析；请缩小年份数量以展示完整干支回执。"


def _continuous_year_range_receipt(years: list[int]) -> str:
    start, end = years[0], years[-1]
    prefix = (
        f"本次按{start}年（{get_year_pillar(start)}）至{end}年"
        f"（{get_year_pillar(end)}）的连续年份范围（共{len(years)}年）"
    )
    entries = "、".join(
        f"{year}年（{get_year_pillar(year)}）" for year in years
    )
    detailed = f"{prefix}逐年分析：{entries}。"
    return detailed if len(detailed) <= 240 else f"{prefix}分析。"


def _month_receipt_label(months: list[int]) -> str:
    if months == list(range(1, 7)):
        return "上半年（1—6月）"
    if months == list(range(7, 13)):
        return "下半年（7—12月）"
    if months == list(range(1, 13)):
        return "每月（1—12月）"
    return "、".join(f"{month}月" for month in months)


def _explicit_forecast_month(text: str) -> int | None:
    for match in re.finditer(r"([一二三四五六七八九十\d]+)月", text):
        surrounding = text[max(0, match.start() - 6):min(len(text), match.end() + 6)]
        if any(term in surrounding for term in _BIRTH_CONTEXT_TERMS):
            continue
        month = _number(match.group(1))
        if 1 <= month <= 12:
            return month
    return None


def _asks_dayun_timing(text: str) -> bool:
    matches = list(_WHEN_LUCK_REQUEST.finditer(text))
    if not matches:
        return False
    for index, request in enumerate(matches):
        boundaries = list(
            _CLAUSE_BOUNDARY.finditer(text, 0, request.start())
        )
        clause_start = boundaries[-1].end() if boundaries else 0
        if index > 0 and matches[index - 1].end() > clause_start:
            clause_start = matches[index - 1].end()
        suffix_boundary = _CLAUSE_BOUNDARY.search(text, request.end())
        clause_end = (
            suffix_boundary.start() if suffix_boundary else len(text)
        )
        if (
            index + 1 < len(matches)
            and matches[index + 1].start() < clause_end
        ):
            clause_end = matches[index + 1].start()
        prefix = text[clause_start:request.start()]
        suffix = text[request.end():clause_end]
        negated = (
            _has_negated_when_luck_intent(prefix, direction="prefix")
            or _has_negated_when_luck_intent(
                suffix,
                direction="suffix",
            )
        )
        if not negated:
            return True
    return False


def _asks_explicit_dayun(text: str) -> bool:
    requests = list(_EXPLICIT_DAYUN_REQUEST.finditer(text))
    if not requests:
        return False
    for request in requests:
        boundaries = list(
            _CLAUSE_BOUNDARY.finditer(text, 0, request.start())
        )
        clause_start = boundaries[-1].end() if boundaries else 0
        suffix_boundary = _CLAUSE_BOUNDARY.search(text, request.end())
        clause_end = (
            suffix_boundary.start() if suffix_boundary else len(text)
        )
        if not (
            _has_negated_when_luck_intent(
                text[clause_start:request.start()],
                direction="prefix",
            )
            or _has_negated_when_luck_intent(
                text[request.end():clause_end],
                direction="suffix",
            )
        ):
            return True
    return False


def _has_negated_when_luck_intent(
    fragment: str,
    *,
    direction: str,
) -> bool:
    """Bind a request to the nearest intent verb on the relevant side."""
    verbs = list(_WHEN_LUCK_INTENT_VERB.finditer(fragment))
    if not verbs:
        return False
    if direction == "suffix":
        verb = verbs[0]
        phrase_start = 0
    else:
        verb = verbs[-1]
        phrase_start = verbs[-2].end() if len(verbs) > 1 else 0
    operator_phrase = fragment[phrase_start:verb.start()]
    if _WHEN_LUCK_DOUBLE_NEGATION.search(operator_phrase):
        return False
    negations = list(_WHEN_LUCK_NEGATION_OPERATOR.finditer(operator_phrase))
    if not negations:
        return False
    latest_negation = negations[-1]
    return not _WHEN_LUCK_POSITIVE_OPERATOR.search(
        operator_phrase[latest_negation.end():]
    )


def _is_follow_up_cancelled(text: str) -> bool:
    if _FOLLOW_UP_SCOPE_RESET.search(text):
        return True
    if _FOLLOW_UP_CANCEL.search(text):
        return True
    compact = re.sub(r"[\s，,。；;！？!?]+", "", text)
    return bool(
        re.search(
            r"(?:那|刚才那个|这个|那个)?(?:先|暂时)?(?:就)?"
            r"(?:不用|不要|不继续|别继续|不看|别看|算了|到此为止)"
            r"(?:了|啦|吧)?(?:谢谢(?:你)?)?$",
            compact,
        )
    )


def resolve_question(
    question: str,
    *,
    now: datetime,
    previous: ResolvedQuestion | None = None,
) -> ResolvedQuestion:
    text = str(question or "").strip()
    scope = check_bazi_scope(text)
    follow_up_cue = bool(
        previous and any(cue in text for cue in _FOLLOW_UP_CUES)
    )
    follow_up_cancelled = _is_follow_up_cancelled(text)
    explicit_domain_terms = _has_explicit_domain(text)
    explicit_marriage_status = is_current_marriage_question(text)
    inherited_marriage_status = bool(
        previous
        and previous.current_marriage_status_requested
        and follow_up_cue
        and not explicit_domain_terms
        and not follow_up_cancelled
    )
    current_marriage_status_requested = (
        explicit_marriage_status or inherited_marriage_status
    )
    domain = (
        "relationship"
        if current_marriage_status_requested
        else _domain(text, previous)
    )
    explicit_domain = (
        explicit_marriage_status
        or explicit_domain_terms
    )
    domain_inherited = bool(previous and not explicit_domain and len(text) <= 20)
    years, reversed_range = _years(text, now.year)
    explicit_year_range = _has_explicit_year_range(text)
    too_many_years = len(years) > 60
    if too_many_years:
        years = []
    invalid_year_range = reversed_range or too_many_years
    years_inherited = False
    if (
        not years
        and not reversed_range
        and not too_many_years
        and previous
        and follow_up_cue
        and not follow_up_cancelled
    ):
        years = list(previous.target_years)
        years_inherited = True

    months: list[int] = []
    monthly_request = (
        any(term in text for term in _MONTHLY_TERMS)
        and not _NEGATED_MONTHLY_REQUEST.search(text)
        and not _POST_MONTHLY_NEGATION.search(text)
    )
    if "上半年" in text:
        months = list(range(1, 7))
    elif "下半年" in text:
        months = list(range(7, 13))
    elif monthly_request:
        months = list(range(1, 13))
    else:
        explicit_month = _explicit_forecast_month(text)
        if explicit_month is not None:
            months = [explicit_month]
    if months and not years and not invalid_year_range:
        years = list(previous.target_years) if previous and previous.target_years else [now.year]

    age_match = re.search(r"(\d{1,3})(?:周|虚)?岁", text)
    ages = [int(age_match.group(1))] if age_match else []
    age_mode = (
        "solar_age" if age_match and "周岁" in age_match.group(0)
        else "nominal_age" if age_match and "虚岁" in age_match.group(0)
        else "unspecified"
    )
    age_requested = bool(ages) or "几岁" in text
    asks_dayun_timing = _asks_dayun_timing(text)
    asks_explicit_dayun = _asks_explicit_dayun(text)

    ambiguity = ""
    if too_many_years:
        ambiguity = "目标年份数量超过60个，请缩小时间范围。"
    elif reversed_range:
        ambiguity = "年份范围的起止顺序需要确认。"
    elif months and len(years) > 1:
        ambiguity = "跨年逐月问题需要先选择一个目标年份。"
    elif ages and age_mode == "unspecified":
        ambiguity = "该年龄问题需要确认按周岁还是虚岁理解。"
    elif age_requested and not ages:
        ambiguity = "该年龄问题需要确认具体年龄及按周岁还是虚岁理解。"

    if months:
        time_scope, depth = "month_range", "monthly"
    elif age_requested:
        time_scope, depth = "age", "long_range"
    elif len(years) > 1:
        time_scope, depth = "year_range", "long_range"
    elif years:
        time_scope, depth = "target_year", "single_year"
    elif (
        asks_explicit_dayun
        or asks_dayun_timing
    ):
        time_scope = "dayun"
        depth = "long_range" if asks_dayun_timing else "topic"
    elif (
        previous
        and follow_up_cue
        and previous.time_scope == "dayun"
        and not follow_up_cancelled
    ):
        time_scope = "dayun"
        depth = previous.requested_depth
    else:
        time_scope = "none"
        depth = "topic" if len(text) > 24 else "direct"

    receipt = ""
    if years and not invalid_year_range and not ambiguity:
        if len(years) == 1:
            receipt = f"本次按{years[0]}年（{get_year_pillar(years[0])}）分析。"
        elif explicit_year_range or "未来" in text:
            receipt = _continuous_year_range_receipt(years)
        else:
            receipt = _discrete_year_receipt(years)
    if months and years and not ambiguity:
        receipt = f"本次按{years[0]}年（{get_year_pillar(years[0])}）{_month_receipt_label(months)}分析。"

    return ResolvedQuestion(
        safe_question=text,
        domain=domain,
        subdomains=["timing"] if time_scope != "none" else [],
        follow_up_reference=(
            previous.domain
            if previous and not explicit_domain and (domain_inherited or years_inherited)
            else ""
        ),
        time_scope=time_scope,
        target_years=years,
        target_months=months,
        age_values=ages,
        age_mode=age_mode,
        requested_depth=depth,
        ambiguity=ambiguity,
        interpretation_receipt=receipt,
        out_of_scope=not scope.allowed,
        scope_reason=scope.reason,
        current_marriage_status_requested=current_marriage_status_requested,
    )
