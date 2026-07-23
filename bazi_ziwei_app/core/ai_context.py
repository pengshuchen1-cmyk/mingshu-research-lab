"""Deterministic intent routing and de-identified AI context construction."""

from __future__ import annotations

import re
from typing import Mapping, Sequence

from core.ai_models import AIRequestContext, ChatMessage, RoutedQuestion
from core.bazi_rulebook import load_rulebook
from core.bazi_constants import EARTHLY_BRANCHES, HEAVENLY_STEMS
from core.chart_facts import ChartFacts


CATEGORY_KEYWORDS = (
    ("wealth", ("财运", "赚钱", "收入", "投资", "创业", "借贷", "抵押", "现金流")),
    ("career", ("工作", "事业", "职业", "升职", "岗位", "行业", "AI")),
    ("relationship", ("桃花", "姻缘", "婚姻", "对象", "感情", "伴侣", "结婚", "已婚", "未婚")),
    ("family", ("父母", "家庭", "原生家庭", "长辈")),
    ("overview", ("概括", "整体", "整个命盘", "八字怎么样", "强弱和格局")),
)
TIMING_KEYWORDS = ("今年", "明年", "后年", "什么时候", "流年", "流月", "每月", "未来")
DOMAIN_RULE_IDS = {
    "wealth": (
        "WEALTH-STAR-VISIBILITY", "WEALTH-CAPACITY",
        "WEALTH-REVENUE-RETENTION", "WEALTH-RISK-ADVICE",
    ),
    "career": ("STRENGTH-SEASON", "PATTERN-MONTH-QI", "WEALTH-CAPACITY"),
    "relationship": (
        "REL-SPOUSE-STAR", "REL-PALACE-STABILITY", "REL-STAGES", "REL-STATUS-UNKNOWN",
    ),
    "family": ("REL-PALACE-STABILITY", "SAFETY-NONDETERMINISTIC"),
    "overview": (
        "STRENGTH-SEASON", "PATTERN-MONTH-QI",
        "WEALTH-REVENUE-RETENTION", "REL-STAGES",
    ),
    "timing": ("DAYUN-DIRECTION", "DAYUN-START-DIV3"),
    "other": ("SAFETY-NONDETERMINISTIC",),
}
REDACTION_MARKER = "[已隐去]"

_CHINESE_MONTH = r"(?:1[0-2]|0?[1-9]|十[一二]?|[一二三四五六七八九])"
_BIRTH_EXPRESSION_PATTERNS = (
    re.compile(
        rf"(?:生日|出生日期|生辰)\s*(?:是|为|[:：])?\s*"
        rf"(?:(?:农历|阴历|阳历|公历)\s*)?"
        rf"(?:19|20)\d{{2}}年(?:\s*{_CHINESE_MONTH}月)?"
        rf"(?:\s*\d{{1,2}}[日号])?"
    ),
    re.compile(
        rf"(?:19|20)\d{{2}}年\s*{_CHINESE_MONTH}月\s*\d{{1,2}}[日号]"
        rf"\s*(?:出生|生人|生的?)"
    ),
    re.compile(
        rf"(?:19|20)\d{{2}}年\s*{_CHINESE_MONTH}月\s*"
        rf"(?:出生|生人|生的?)"
    ),
    re.compile(
        r"(?:我是|本人)?\s*(?:19|20)\d{2}年\s*"
        r"(?:出生|生人|生的?|属[鼠牛虎兔龙蛇马羊猴鸡狗猪])"
    ),
    re.compile(r"生于\s*(?:19|20)\d{2}年"),
    re.compile(r"(?:出生年份|出生年|生年)\s*(?:是|为|[:：])?\s*(?:19|20)\d{2}年?"),
)

_DIRECT_SENSITIVE_PATTERNS = (
    # Identifier/secret values are a single token and may be Chinese safe words.
    re.compile(
        r"(?i)(?:profile[\s_-]*id|database[\s_-]*id|db[\s_-]*id|"
        r"customer[\s_-]*id|用户(?:档案)?ID|档案ID|数据库ID|客户ID|"
        r"(?:openai[\s_-]*)?API[\s_-]*key|"
        r"internal[\s_-]*rule[\s_-]*version|内部规则版本|user|city)"
        r"\s*(?:(?:[:：=]\s*)|\s+)[^\s，,。；;！？!?\r\n]+"
    ),
    re.compile(r"(?i)(?<![a-z0-9_-])sk-[a-z0-9_-]{8,}(?![a-z0-9_-])"),
    re.compile(
        r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    re.compile(r"(?<!\d)(?:\+?86[\s-]?)?1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}(?!\d)"),
    # Exact machine-readable dates and exact clock times are not needed for advice.
    re.compile(r"(?<!\d)(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)"),
    re.compile(r"(?<!\d)(?:[01]?\d|2[0-3])时(?:[0-5]?\d分)?"),
    re.compile(
        r"(?:出生时间|生时|出生时辰)\s*"
        r"(?:是|为|[:：])\s*[^\s，,。；;！？!?\r\n]{1,32}"
    ),
    re.compile(
        r"(?:出生地|籍贯)\s*(?:是|为|在|[:：])?\s*"
        r"[^\s，,。；;！？!?\r\n]{2,24}"
    ),
    re.compile(r"出生于\s*[^\s，,。；;！？!?\r\n]{2,24}"),
    re.compile(
        r"(?:现居|居住于|住在|居住地|常住地)\s*(?:是|为|在|[:：])?\s*"
        r"[^\s，,。；;！？!?\r\n]{2,24}"
    ),
    re.compile(
        r"(?:longitude|经度|东经)\s*[:：=]?\s*[+-]?\d{1,3}(?:\.\d+)?(?:°|度)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:姓名|名字|称呼)\s*(?:是|为|叫|[:：])?\s*"
        r"[\u3400-\u9fff·]{2,16}"
    ),
    re.compile(r"(?:我叫|本人叫|叫)\s*[\u3400-\u9fff·]{2,8}"),
    re.compile(
        r"(?:我是|本人是)\s*[\u3400-\u9fff·]{2,8}"
        r"(?=\s*[，,。；;！？!?])"
    ),
    *_BIRTH_EXPRESSION_PATTERNS,
)

_ENGLISH_IDENTITY_LABEL = re.compile(
    r"(?i)(?:full[\s_-]*name|name|birth[\s_-]*(?:place|city)|"
    r"residence|home[\s_-]*(?:city|address))\s*[:：=]\s*"
)
_SAFE_RESUME_CUE = re.compile(
    r"(?i)\b(?:wants?|needs?|seeks?|asks?)\s+"
    r"(?:advice|guidance|to\s+ask)(?:\s+(?:on|about))?\s*"
)
_CLAUSE_DELIMITER = re.compile(r"[，,。；;！？!?\r\n]")
_SENSITIVE_CLAUSE_CUE = re.compile(
    r"(?i)"
    r"(?:姓名|名字|称呼|绰号|人称|别名|昵称|我叫|本人叫|我是|本人是|"
    r"出生地|出生于|籍贯|现居|居住于|住在|居住地|常住地|来自)"
    r"\s*(?:是|为|叫|在|[:：])?"
    r"|(?:日志|logs?)(?:内容)?\s*[:：=]"
    r"|\[(?:INFO|DEBUG|WARN(?:ING)?|ERROR|TRACE)\]"
    r"|(?:profile[\s_-]*id|database[\s_-]*id|db[\s_-]*id|"
    r"customer[\s_-]*id|用户(?:档案)?ID|档案ID|数据库ID|客户ID|"
    r"(?:openai[\s_-]*)?API[\s_-]*key|"
    r"internal[\s_-]*rule[\s_-]*version|内部规则版本)"
    r"\s*(?:(?:[:：=]\s*)|\s+)"
    r"|(?<![A-Za-z0-9_])(?:message|target|user|city)\s*="
)

_SAFE_SEMANTIC_TERMS = (
    "现在是否已经结婚",
    "当前是否已经结婚",
    "当前婚姻状态",
    "现在已经结婚",
    "目前是否结婚",
    "现在有没有结婚",
    "目前结婚了吗",
    "现在结婚了吗",
    "当前结婚了吗",
    "现在已婚吗",
    "目前已婚吗",
    "当前已婚吗",
    "现在未婚",
    "目前未婚",
    "当前未婚",
    "现在已婚",
    "目前已婚",
    "当前已婚",
    "转向人工智能行业",
    "人工智能行业",
    "人工智能创业",
    "转向AI行业",
    "现金流紧张",
    "现金流压力",
    "抵押房子",
    "抵押贷款",
    "房屋抵押",
    "事业转换",
    "事业转型",
    "事业调整",
    "职业转换",
    "职业转型",
    "工作转换",
    "行业转换",
    "行业转型",
    "原生家庭",
    "姻缘方面",
    "婚姻方面",
    "事业方面",
    "财运方面",
    "关系方面",
    "AI创业",
    "AI行业",
    "现金流",
    "高杠杆",
    "什么时候",
    "适不适合",
    "可不可以",
    "能不能",
    "该不该",
    "要不要",
    "怎么办",
    "为什么",
    "想问",
    "借贷",
    "贷款",
    "杠杆",
    "抵押",
    "房子",
    "人工智能",
    "创业",
    "行业",
    "姻缘",
    "婚姻",
    "桃花",
    "感情",
    "伴侣",
    "结婚",
    "关系",
    "事业",
    "职业",
    "工作",
    "财运",
    "财富",
    "赚钱",
    "收入",
    "投资",
    "家庭",
    "父母",
    "今年",
    "明年",
    "后年",
    "未来",
    "每月",
    "流年",
    "流月",
    "上半年",
    "下半年",
    "因为",
    "由于",
    "所以",
    "如果",
    "导致",
    "为何",
    "怎么",
    "怎样",
    "如何",
    "什么",
    "是否",
    "解释",
    "需要",
    "注意",
    "条件",
    "原因",
    "影响",
    "风险",
    "机会",
    "建议",
    "调整",
    "转换",
    "转型",
    "发展",
    "紧张",
    "压力",
    "规划",
    "选择",
    "适合",
)
_SAFE_SPAN_PATTERN = re.compile(
    "|".join(
        (
            re.escape(REDACTION_MARKER),
            rf"(?:19|20)\d{{2}}年\s*{_CHINESE_MONTH}月",
            r"(?:19|20)\d{2}年",
            rf"(?:今年|明年|后年|流月|每月)\s*{_CHINESE_MONTH}月",
            *(
                re.escape(term)
                for term in sorted(_SAFE_SEMANTIC_TERMS, key=len, reverse=True)
            ),
        )
    ),
    re.IGNORECASE,
)
_SAFE_BRIDGE_CORES = frozenset(
    {
        "",
        "的",
        "了",
        "呢",
        "吗",
        "吧",
        "和",
        "与",
        "及",
        "或",
        "在",
        "想",
        "做",
        "要",
        "更",
        "请",
        "看",
        "问",
        "从",
        "向",
        "转",
        "到",
        "先",
        "再",
    }
)
_SEMANTIC_EDGE_CHARS = " \t\r\n，,。；;！？!?、：:"
_MONTH_NUMBERS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
}
_NORMALIZABLE_MONTH = re.compile(
    rf"(?P<prefix>(?:19|20)\d{{2}}年|今年|明年|后年|流月|每月)"
    rf"\s*(?P<month>{_CHINESE_MONTH})月"
)
_CURRENT_MARRIAGE_STATUS = re.compile(
    r"(?:现在|目前|当前)"
    r"(?:是否已经结婚|是否结婚|有没有结婚|结婚了吗|已经结婚|已婚吗|未婚|已婚)"
)


def _safe_semantic_gap(gap: str) -> str:
    """Keep only short grammatical bridges between independently safe spans."""
    core = gap.strip(_SEMANTIC_EDGE_CHARS)
    if core in _SAFE_BRIDGE_CORES:
        return gap
    return REDACTION_MARKER


def _normalize_safe_span(value: str) -> str:
    match = _NORMALIZABLE_MONTH.fullmatch(value)
    if not match:
        return value
    month = match.group("month")
    normalized_month = _MONTH_NUMBERS.get(month, int(month) if month.isdigit() else month)
    return f"{match.group('prefix')}{normalized_month}月"


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def _identity_spans(text: str) -> list[tuple[int, int]]:
    """Bound labeled English identity values without swallowing a safe resumed query."""
    spans: list[tuple[int, int]] = []
    for label in _ENGLISH_IDENTITY_LABEL.finditer(text):
        line_end_match = re.search(r"[\r\n]", text[label.end():])
        line_end = (
            label.end() + line_end_match.start()
            if line_end_match
            else len(text)
        )
        punctuation = re.search(r"[，,。；;！？!?]", text[label.end():line_end])
        boundary = label.end() + punctuation.start() if punctuation else line_end
        cue = _SAFE_RESUME_CUE.search(text, label.end(), boundary)
        if cue and _SAFE_SPAN_PATTERN.match(text, cue.end()):
            boundary = cue.end()
        spans.append((label.start(), boundary))
    return spans


def _sensitive_clause_spans(text: str) -> list[tuple[int, int]]:
    """Claim the whole containing clause for sensitive provenance cues."""
    delimiters = list(_CLAUSE_DELIMITER.finditer(text))
    spans: list[tuple[int, int]] = []
    for cue in _SENSITIVE_CLAUSE_CUE.finditer(text):
        start = 0
        end = len(text)
        for delimiter in delimiters:
            if delimiter.end() <= cue.start():
                start = delimiter.end()
                continue
            if delimiter.start() >= cue.end():
                end = delimiter.start()
                break
        spans.append((start, end))
    return spans


def _provenance_segments(text: str) -> list[tuple[bool, str]]:
    """Split original text into sensitive and eligible spans before extraction."""
    spans = _identity_spans(text)
    spans.extend(_sensitive_clause_spans(text))
    for pattern in _DIRECT_SENSITIVE_PATTERNS:
        spans.extend(match.span() for match in pattern.finditer(text))
    merged = _merge_spans(spans)
    if not merged:
        return [(False, text)]

    segments: list[tuple[bool, str]] = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            segments.append((False, text[cursor:start]))
        segments.append((True, text[start:end]))
        cursor = end
    if cursor < len(text):
        segments.append((False, text[cursor:]))
    return segments


def _project_safe_segment(text: str) -> str:
    matches = list(_SAFE_SPAN_PATTERN.finditer(text))
    if not matches:
        return REDACTION_MARKER

    pieces: list[str] = []
    cursor = 0
    for match in matches:
        gap = text[cursor:match.start()]
        if gap:
            pieces.append(_safe_semantic_gap(gap))
        pieces.append(_normalize_safe_span(match.group(0)))
        cursor = match.end()
    suffix = text[cursor:]
    if suffix:
        pieces.append(_safe_semantic_gap(suffix))
    return "".join(pieces)


def _project_safe_semantics(segments: Sequence[tuple[bool, str]]) -> str:
    """Extract only from non-sensitive provenance spans, then normalize semantics."""
    pieces: list[str] = []
    has_current_marriage_status = False
    for sensitive, text in segments:
        if sensitive:
            pieces.append(REDACTION_MARKER)
            continue
        has_current_marriage_status = (
            has_current_marriage_status
            or bool(_CURRENT_MARRIAGE_STATUS.search(text))
        )
        pieces.append(_project_safe_segment(text))
    projected = "".join(pieces)
    projected = re.sub(
        rf"(?:{re.escape(REDACTION_MARKER)}\s*[,，;；]?\s*){{2,}}",
        REDACTION_MARKER,
        projected,
    )
    if has_current_marriage_status and "当前婚姻状态" not in projected:
        projected += "；当前婚姻状态"
    return projected.strip() or REDACTION_MARKER


def redact_customer_text(text: str) -> str:
    """Project safe semantics from provenance-aware, non-sensitive source spans.

    Sensitive labeled fields and log spans are segmented before semantic matching, so
    values that collide with safe terms can never be recovered by the allowlist.
    """
    segments = _provenance_segments(str(text or "").strip())
    return _project_safe_semantics(segments)[:4000]


def _strip_birth_expressions(value: object) -> str:
    """Remove Chinese birth-date/year expressions before extracting forecast years."""
    text = str(value or "")
    for pattern in _BIRTH_EXPRESSION_PATTERNS:
        text = pattern.sub("", text)
    return text


def _target_year_facts(question: str) -> list[dict[str, object]]:
    """Extract explicit forecast years and calculate only their year pillars."""
    text = redact_customer_text(_strip_birth_expressions(question))
    years = list(dict.fromkeys(int(value) for value in re.findall(r"((?:19|20)\d{2})(?=年)", text)))[:4]
    return [
        {
            "year": year,
            "year_pillar": (
                HEAVENLY_STEMS[(year - 4) % 10]
                + EARTHLY_BRANCHES[(year - 4) % 12]
            ),
        }
        for year in years
    ]


def classify_question(question: str) -> RoutedQuestion:
    text = str(question or "").strip()
    requires_timing = any(keyword in text for keyword in TIMING_KEYWORDS) or bool(
        re.search(r"(?:19|20)\d{2}年", text)
    )
    category = None
    for candidate, keywords in CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            category = candidate
            break
    if category is None:
        category = "timing" if requires_timing else "other"
    return RoutedQuestion(category=category, requires_timing=requires_timing)


def _safe_history(history: Sequence[ChatMessage | Mapping[str, object]]) -> list[ChatMessage]:
    selected: list[ChatMessage] = []
    remaining = 6000
    for raw in reversed(history):
        if len(selected) >= 6 or remaining <= 0:
            break
        if isinstance(raw, ChatMessage):
            role, content = raw.role, raw.content
        else:
            role = str(raw.get("role", ""))
            content = str(raw.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        content = redact_customer_text(content)
        content = content[:min(len(content), remaining, 4000)]
        selected.append(ChatMessage(role=role, content=content))
        remaining -= len(content)
    return list(reversed(selected))


def build_ai_context(
    facts: ChartFacts,
    question: str,
    history: Sequence[ChatMessage | Mapping[str, object]],
) -> AIRequestContext:
    redacted_question = redact_customer_text(question)[:500]
    routed = classify_question(redacted_question)
    raw = facts.to_dict()
    chart_facts: dict[str, object] = {
        "pillars": raw["pillars"],
        "gender": raw["gender"],
        "day_master": raw["day_master"],
        "hidden_stems": raw["hidden_stems"],
        "ten_gods": raw["ten_gods"],
        "element_counts": raw["element_counts"],
        "strength": raw["strength"],
        "pattern": raw["pattern"],
        "wealth": raw["wealth"],
        "relationship": raw["relationship"],
        "dayun": raw["dayun"],
    }
    if routed.requires_timing or routed.category == "timing":
        chart_facts["current_context"] = raw["current_context"]
        chart_facts["target_years"] = _target_year_facts(redacted_question)

    selected_ids = list(facts.rule_ids)
    selected_ids.extend(DOMAIN_RULE_IDS[routed.category])
    if routed.requires_timing:
        selected_ids.extend(DOMAIN_RULE_IDS["timing"])
    selected_ids.extend(("SAFETY-NONDETERMINISTIC", "SAFETY-STATUS-UNKNOWN"))
    book = load_rulebook()
    rule_evidence = []
    for rule_id in dict.fromkeys(selected_ids):
        try:
            rule = book.by_id(rule_id)
        except KeyError:
            continue
        rule_evidence.append({"id": rule.id, "statement": rule.statement})

    return AIRequestContext(
        question=redacted_question,
        category=routed.category,
        requires_timing=routed.requires_timing,
        chart_facts=chart_facts,
        rule_evidence=rule_evidence,
        history=_safe_history(history),
    )
