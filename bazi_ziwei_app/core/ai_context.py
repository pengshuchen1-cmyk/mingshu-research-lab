"""Deterministic intent routing and de-identified AI context construction."""

from __future__ import annotations

import re
from typing import Mapping, Sequence, overload

import core.yearly_engine as yearly_engine
from core.ai_intent import (
    CURRENT_MARRIAGE_STATUS_MARKER,
    is_current_marriage_question,
)
from core.ai_models import (
    AIRequestContext,
    AnalysisPlan,
    ChatMessage,
    FactPacket,
    RoutedQuestion,
)
from core.bazi_constants import BRANCH_HIDDEN_STEMS, STEM_ELEMENTS
from core.bazi_rulebook import load_rulebook
from core.chart_facts import ChartFacts
from core.ten_gods import get_ten_god


BORROWING_KEYWORDS = (
    "房贷", "按揭", "借钱", "负债", "融资", "抵押", "借贷", "贷款", "杠杆",
)
CATEGORY_KEYWORDS = (
    (
        "wealth",
        (
            "财运", "正财", "偏财", "财星", "赚钱", "收入", "投资", "创业", "现金流",
            "基金", "股票", "理财", "预算", "支出", "学费",
            *BORROWING_KEYWORDS,
        ),
    ),
    (
        "career",
        (
            "工作", "事业", "职业", "升职", "岗位", "行业", "AI",
            "工程师", "管理岗", "转岗", "团队", "职场", "薪资", "主管",
        ),
    ),
    (
        "relationship",
        (
            "桃花", "姻缘", "婚姻", "对象", "感情", "伴侣", "配偶",
            "结婚", "已婚", "未婚", "登记状态",
        ),
    ),
    ("family", ("父母", "家庭", "原生家庭", "长辈")),
    ("overview", ("概括", "整体", "整个命盘", "八字怎么样", "强弱和格局")),
)
TIMING_KEYWORDS = (
    "今年", "明年", "后年", "什么时候", "何时", "哪年", "几年后", "几岁",
    "流年", "流月", "每月", "每个月", "逐月", "上半年", "下半年", "岁以后",
    "未来", "大运", "行运", "起运",
)
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
    "health_advisory": (
        "STRENGTH-SEASON",
        "SAFETY-STATUS-UNKNOWN",
        "SAFETY-NONDETERMINISTIC",
    ),
    "children": ("SAFETY-STATUS-UNKNOWN", "SAFETY-NONDETERMINISTIC"),
    "education": (
        "STRENGTH-SEASON",
        "PATTERN-MONTH-QI",
        "SAFETY-NONDETERMINISTIC",
    ),
    "relocation": ("STRENGTH-SEASON", "SAFETY-NONDETERMINISTIC"),
    "property": (
        "WEALTH-CAPACITY",
        "WEALTH-RISK-ADVICE",
        "SAFETY-STATUS-UNKNOWN",
    ),
    "benefactor": ("PATTERN-MONTH-QI", "SAFETY-NONDETERMINISTIC"),
    "overview": (
        "STRENGTH-SEASON", "PATTERN-MONTH-QI",
        "WEALTH-REVENUE-RETENTION", "REL-STAGES",
    ),
    "timing": ("DAYUN-DIRECTION", "DAYUN-START-DIV3"),
    "other": ("SAFETY-NONDETERMINISTIC",),
}
REDACTION_MARKER = "[已隐去]"
_MAX_QUESTION_INPUT_CHARS = 2000
_MAX_HISTORY_INPUT_CHARS = 4000
_MAX_REDACTION_INPUT_CHARS = 4000

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
    re.compile(
        r"(?i)(?:配置内容|调试输出|Authorization\s*:?\s*Bearer|"
        r"stack\s*trace|config(?:uration)?)"
        r"[^。；;！？!?\r\n]*"
    ),
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
    # Chinese resident identity numbers are personal identifiers even when unlabeled.
    re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    # Exact machine-readable dates and exact clock times are not needed for advice.
    re.compile(r"(?<!\d)(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)"),
    re.compile(r"(?<!\d)(?:[01]?\d|2[0-3])时(?:[0-5]?\d分)?"),
    re.compile(
        r"(?:出生时间|生时|出生时辰)\s*"
        r"(?:是|为|[:：])\s*[^\s，,。；;！？!?\r\n]{1,32}"
    ),
    re.compile(
        r"(?:生日|出生日期|生辰)\s*(?:是|为|[:：])?\s*"
        r"[^\s，,。；;！？!?\r\n]{4,32}"
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
        r"(?<![\u3400-\u9fffA-Za-z0-9_])"
        r"[\u3400-\u9fff·]{2,8}从[\u3400-\u9fff·]{2,16}来"
        r"(?=[，,。；;！？!?])"
    ),
    re.compile(
        r"(?<![\u3400-\u9fffA-Za-z0-9_])"
        r"[\u3400-\u9fff·]{2,8}在[\u3400-\u9fff·]{2,16}说"
        r"(?=[，,。；;！？!?])"
    ),
    re.compile(
        r"(?:我是|本人是)\s*[\u3400-\u9fff·]{2,8}"
        r"(?=\s*[，,。；;！？!?])"
    ),
    *_BIRTH_EXPRESSION_PATTERNS,
)

_ENGLISH_IDENTITY_KEY = (
    r"(?:full[\s_-]*name|name|birth[\s_-]*(?:place|city)|"
    r"residence|home[\s_-]*(?:city|address))"
)
_ENGLISH_IDENTITY_LABEL = re.compile(
    rf"(?i){_ENGLISH_IDENTITY_KEY}\s*[:：=]\s*"
)
_SAFE_RESUME_CUE = re.compile(
    r"(?i)\b(?:wants?|needs?|seeks?|asks?)\s+"
    r"(?:advice|guidance|to\s+ask)(?:\s+(?:on|about))?\s*"
)
_CLAUSE_DELIMITER = re.compile(r"[，,。.；;！？!?\r\n]")
_IDENTITY_CLAUSE_CUES = (
    "姓名",
    "名字",
    "乳名",
    "小名",
    "曾用名",
    "原名",
    "笔名",
    "艺名",
    "网名",
    "昵称",
    "绰号",
    "外号",
    "别名",
    "人称",
    "称呼",
    "我叫",
    "本人叫",
)
_LOCATION_CLAUSE_CUES = (
    "出生地",
    "出生于",
    "出生在",
    "生于",
    "来自",
    "籍贯",
    "户籍",
    "户口",
    "现居",
    "居住",
    "居住于",
    "住在",
    "住址",
    "地址",
    "所在地",
    "常住地",
    "城市",
    "省市",
    "家乡",
    "故乡",
    "老家",
)
_SENSITIVE_CUE_WORDS = "|".join(
    re.escape(cue)
    for cue in sorted(
        (*_IDENTITY_CLAUSE_CUES, *_LOCATION_CLAUSE_CUES),
        key=len,
        reverse=True,
    )
)
_SENSITIVE_CLAUSE_CUE = re.compile(
    r"(?i)"
    rf"(?:{_SENSITIVE_CUE_WORDS})\s*(?:是|为|叫|在|[:：])?"
    r"|(?:日志|logs?)(?:内容)?\s*[:：=]"
    r"|\[(?:INFO|DEBUG|WARN(?:ING)?|ERROR|TRACE)\]"
    r"|(?:profile[\s_-]*id|database[\s_-]*id|db[\s_-]*id|"
    r"customer[\s_-]*id|用户(?:档案)?ID|档案ID|数据库ID|客户ID|"
    r"(?:openai[\s_-]*)?API[\s_-]*key|"
    r"internal[\s_-]*rule[\s_-]*version|内部规则版本)"
    r"\s*(?:(?:[:：=]\s*)|\s+)"
    r"|Authorization\s*:?\s*Bearer"
    r"|Bearer\s+[A-Za-z0-9._-]{8,}"
    r"|(?:access[\s_-]*token|token|secret|password|passwd|env)"
    r"\s*(?:(?:[:：=]\s*)|\s+)"
    r"|(?:配置内容|调试输出|堆栈|stack\s*trace|config(?:uration)?)"
    r"|(?<![A-Za-z0-9_])(?:model|timeout)\s+[A-Za-z0-9_.:/-]+"
    r"|(?<![A-Za-z0-9_])(?:message|target|user|city)\s*="
)
_BOUNDED_SINGLE_NAME_FIELD_CUE = re.compile(
    r"(?<![\u3400-\u9fffA-Za-z0-9_])"
    r"(?:(?:姓氏|姓|名)\s*(?:是|为|叫|[:：=])"
    r"|(?:姓|名)\s+)"
)
_GRAMMATICAL_IDENTITY_CUE = re.compile(
    r"(?<![\u3400-\u9fffA-Za-z0-9_])大名\s*(?:是|为|叫|[:：=])"
)
_SURNAME_SUBJECTS = (
    "当事人",
    "本人",
    "客户",
    "用户",
    "孩子",
    "父亲",
    "母亲",
    "丈夫",
    "妻子",
    "伴侣",
    "我",
    "你",
    "您",
    "他",
    "她",
    "其",
)
_NATURAL_SURNAME_FIELD_CUE = re.compile(
    r"(?<![\u3400-\u9fffA-Za-z0-9_])"
    rf"(?:(?:{'|'.join(_SURNAME_SUBJECTS)})姓|姓)"
    r"(?!氏)(?=[\u3400-\u9fff·A-Za-z])"
)
_GENERIC_KEY_VALUE_CUE = re.compile(
    rf"(?i)"
    rf"(?<![A-Za-z0-9_])"
    rf"(?!{_ENGLISH_IDENTITY_KEY}\s*[:：=])"
    rf"[A-Za-z_][A-Za-z0-9_.-]*\s*[:：=]"
)
_UNQUOTED_JSON_OBJECT_FIELD = re.compile(
    r"[^{}\"'\s，,。；;！？!?:：=]+\s*[:：=]"
)
_COMMON_SURNAME = (
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华"
    "金魏陶姜戚谢邹喻柏窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方"
    "俞任袁柳唐罗薛伍余米贝姚孟顾尹江钟刘叶杜夏汪田郭林高徐"
    "邱于董萧程邓傅曾卢蔡贾丁戴熊廖侯邵黎龚文毛赖段雷汤尹武"
)
_NATURAL_NAME = re.compile(
    rf"(?:^|[，,。；;！？!?\r\n]|请帮|帮|替|为)"
    rf"(?P<value>(?:欧阳|司马|上官|诸葛|[{_COMMON_SURNAME}])"
    rf"[\u3400-\u9fff·]{{1,3}})"
    r"(?=(?:准备|打算|目前|现在|如今|现阶段|常驻|现居|人在|"
    r"位于|计划|考虑|想|需要|建议|分析|咨询|询问|看看))",
    re.MULTILINE,
)
_STANDALONE_NATURAL_NAME = re.compile(
    rf"(?:^|(?<=[，,。；;！？!?\r\n]))\s*"
    rf"(?P<value>(?:欧阳|司马|上官|诸葛|[{_COMMON_SURNAME}])"
    rf"[\u3400-\u9fff·]{{1,2}})"
    r"\s*(?=$|[，,。；;！？!?\r\n])",
    re.MULTILINE,
)
_ADMIN_LOCATION = (
    r"(?:(?:北京|上海|天津|重庆|香港|澳门)(?:市)?"
    r"(?:[\u3400-\u9fff]{1,8}(?:区|县|镇|乡|村))?"
    r"|[\u3400-\u9fff]{2,10}(?:省|市|自治区|特别行政区|自治州|"
    r"地区|盟|区|县|州|旗|镇|乡|村))"
)
_NATURAL_LOCATION = re.compile(
    rf"(?:人在|常驻|现居|位于|住在|来自|准备在|去|回|到)"
    rf"\s*(?P<value>{_ADMIN_LOCATION})"
)
_STANDALONE_NATURAL_LOCATION = re.compile(
    rf"(?:^|[，,。；;！？!?\r\n])"
    rf"(?P<value>{_ADMIN_LOCATION})"
    r"(?=(?:转|换|找|做|从事|发展|创业|工作|事业|职业|就业|"
    r"求职|升职|管理岗|是否|适合|合适))",
    re.MULTILINE,
)
_HIGH_ENTROPY_TOKEN = re.compile(
    r"(?<![A-Za-z0-9._-])"
    r"[A-Za-z0-9_-]{28,}(?:\.[A-Za-z0-9_-]{8,}){0,2}"
    r"(?![A-Za-z0-9._-])"
)

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
        if cue:
            boundary = cue.end()
        spans.append((label.start(), boundary))
    return spans


def _containing_clause_span(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int]:
    """Return the clause surrounding one already identified sensitive span."""
    clause_start = 0
    for delimiter in _CLAUSE_DELIMITER.finditer(text, 0, start):
        clause_start = delimiter.end()
    following = _CLAUSE_DELIMITER.search(text, end)
    clause_end = following.start() if following else len(text)
    return clause_start, clause_end


def _has_quoted_key_value(text: str) -> bool:
    """Detect a quoted config key in bounded linear passes."""
    for quote_character in ('"', "'"):
        opening: int | None = None
        escaped = False
        for index, character in enumerate(text):
            if opening is not None and escaped:
                escaped = False
                continue
            if opening is not None and character == "\\":
                escaped = True
                continue
            if character != quote_character:
                continue
            if opening is None:
                previous = text[index - 1] if index else ""
                following = text[index + 1] if index + 1 < len(text) else ""
                if (
                    quote_character == "'"
                    and previous.isascii()
                    and previous.isalnum()
                    and following.isascii()
                    and following.isalnum()
                ):
                    continue
                opening = index
                continue

            probe = index + 1
            while probe < len(text) and text[probe].isspace():
                probe += 1
            if probe < len(text) and text[probe] in ":：=":
                return True
            opening = None
            escaped = False
    return False


def _complete_clause_boundaries(text: str) -> list[int]:
    """Find top-level delimiter endpoints, ignoring quoted or braced delimiters."""
    boundaries: list[int] = []
    depth = 0
    quote = ""
    escaped = False

    for index, character in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = ""
            continue
        if character in {'"', "'"}:
            previous = text[index - 1] if index else ""
            following = text[index + 1] if index + 1 < len(text) else ""
            if (
                character == "'"
                and previous.isascii()
                and previous.isalnum()
                and following.isascii()
                and following.isalnum()
            ):
                continue
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}" and depth:
            depth -= 1
        elif depth == 0 and _CLAUSE_DELIMITER.fullmatch(character):
            boundaries.append(index + 1)
    return boundaries


def _clause_spans(text: str) -> list[tuple[int, int]]:
    """Split clauses once, ignoring delimiters inside quoted or braced config text."""
    spans: list[tuple[int, int]] = []
    clause_start = 0
    for boundary in _complete_clause_boundaries(text):
        delimiter_start = boundary - 1
        if clause_start < delimiter_start:
            spans.append((clause_start, delimiter_start))
        clause_start = boundary
    if clause_start < len(text):
        spans.append((clause_start, len(text)))
    return spans


def _clause_has_config_syntax(clause: str) -> bool:
    return bool(
        _has_quoted_key_value(clause)
        or _GENERIC_KEY_VALUE_CUE.search(clause)
        or (
            "{" in clause
            and _UNQUOTED_JSON_OBJECT_FIELD.search(clause)
        )
    )


def _sensitive_clause_spans(text: str) -> list[tuple[int, int]]:
    """Claim the whole containing clause for sensitive provenance cues."""
    spans: list[tuple[int, int]] = []
    sensitive_patterns = (
        _SENSITIVE_CLAUSE_CUE,
        _BOUNDED_SINGLE_NAME_FIELD_CUE,
        _GRAMMATICAL_IDENTITY_CUE,
        _NATURAL_SURNAME_FIELD_CUE,
    )
    for start, end in _clause_spans(text):
        clause = text[start:end]
        if (
            _clause_has_config_syntax(clause)
            or any(pattern.search(clause) for pattern in sensitive_patterns)
        ):
            spans.append((start, end))
    return spans


def _provenance_segments(text: str) -> list[tuple[bool, str]]:
    """Split original text into sensitive and eligible spans before extraction."""
    spans = _identity_spans(text)
    spans.extend(_sensitive_clause_spans(text))
    for pattern in _DIRECT_SENSITIVE_PATTERNS:
        spans.extend(match.span() for match in pattern.finditer(text))
    spans.extend(match.span("value") for match in _NATURAL_NAME.finditer(text))
    spans.extend(
        match.span("value")
        for match in _STANDALONE_NATURAL_NAME.finditer(text)
    )
    spans.extend(match.span("value") for match in _NATURAL_LOCATION.finditer(text))
    spans.extend(
        match.span("value")
        for match in _STANDALONE_NATURAL_LOCATION.finditer(text)
    )
    spans.extend(match.span() for match in _HIGH_ENTROPY_TOKEN.finditer(text))
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
    if not text:
        return ""
    projected = _NORMALIZABLE_MONTH.sub(
        lambda match: _normalize_safe_span(match.group(0)),
        text,
    )
    projected = re.sub(
        r"(?:她|他)(?=(?:现在|目前|当前)?"
        r"(?:是否|有没有|已经|未婚|已婚|结婚))",
        "",
        projected,
    )
    return projected


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
            or is_current_marriage_question(text)
        )
        pieces.append(_project_safe_segment(text))
    projected = "".join(pieces)
    projected = re.sub(
        rf"(?:{re.escape(REDACTION_MARKER)}\s*[,，;；]?\s*){{2,}}",
        REDACTION_MARKER,
        projected,
    )
    if (
        has_current_marriage_status
        and CURRENT_MARRIAGE_STATUS_MARKER not in projected
    ):
        projected += f"；{CURRENT_MARRIAGE_STATUS_MARKER}"
    return projected.strip() or REDACTION_MARKER


def _bounded_complete_input(text: object, max_input_chars: int) -> str:
    """Bound raw input without projecting an incomplete trailing clause."""
    raw_text = str(text or "")
    limit = max(0, max_input_chars)
    if len(raw_text) <= limit:
        return raw_text.strip()

    bounded = raw_text[:limit]
    boundaries = _complete_clause_boundaries(bounded)
    if not boundaries:
        return ""
    return bounded[:boundaries[-1]].strip()


def redact_customer_text(
    text: str,
    *,
    max_input_chars: int = _MAX_REDACTION_INPUT_CHARS,
) -> str:
    """Project safe semantics from provenance-aware, non-sensitive source spans.

    Sensitive provenance spans are segmented before semantic projection, so their
    values cannot be recovered by later normalization.
    """
    bounded_text = _bounded_complete_input(text, max_input_chars)
    segments = _provenance_segments(bounded_text)
    return _project_safe_semantics(segments)[:4000]


def _strip_birth_expressions(value: object) -> str:
    """Remove Chinese birth-date/year expressions before extracting forecast years."""
    text = str(value or "")
    for pattern in _BIRTH_EXPRESSION_PATTERNS:
        text = pattern.sub("", text)
    return text


def _target_year_facts(question: str) -> list[dict[str, object]]:
    """Extract explicit forecast years and forward the canonical yearly fact."""
    text = redact_customer_text(_strip_birth_expressions(question))
    years = list(dict.fromkeys(int(value) for value in re.findall(r"((?:19|20)\d{2})(?=年)", text)))[:4]
    return [
        {
            "year": year,
            "year_pillar": yearly_engine.get_year_pillar(year),
        }
        for year in years
    ]


def _safe_dayun_periods(
    periods: Sequence[Mapping[str, object]] | None,
    day_master: str,
) -> list[dict[str, object]]:
    """Project only canonical, non-identifying dayun facts into cloud context."""
    safe: list[dict[str, object]] = []
    for raw in periods or ():
        pillar = str(raw.get("pillar") or "").strip()
        ten_god = str(raw.get("ten_god") or "").strip()
        try:
            start_age = int(raw["start_age"])
            end_age = int(raw["end_age"])
            start_year = int(raw["start_year"])
            end_year = int(raw["end_year"])
        except (KeyError, TypeError, ValueError):
            continue
        if not re.fullmatch(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]", pillar):
            continue
        safe.append(
            {
                "pillar": pillar,
                "start_age": start_age,
                "end_age": end_age,
                "start_year": start_year,
                "end_year": end_year,
                "ten_god": ten_god,
                "branch_hidden_stems": [
                    {
                        "stem": stem,
                        "element": STEM_ELEMENTS.get(stem, ""),
                        "ten_god": get_ten_god(day_master, stem),
                    }
                    for stem in BRANCH_HIDDEN_STEMS.get(pillar[1], [])
                ],
            }
        )
    return safe[:10]


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
            content = str(raw.get("content", ""))
        if role not in {"user", "assistant"} or not content:
            continue
        content = redact_customer_text(
            content,
            max_input_chars=_MAX_HISTORY_INPUT_CHARS,
        )
        content = content[:min(len(content), remaining, 4000)]
        selected.append(ChatMessage(role=role, content=content))
        remaining -= len(content)
    return list(reversed(selected))


def build_canonical_chart_facts(
    facts: ChartFacts,
    *,
    requires_timing: bool,
    question: str = "",
    target_years: Sequence[int] = (),
    dayun_periods: Sequence[Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Project canonical local facts for guards without routing a question."""
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
    if requires_timing:
        chart_facts["current_context"] = raw["current_context"]
        selected_years = list(dict.fromkeys(int(year) for year in target_years))
        chart_facts["target_years"] = (
            [
                {
                    "year": year,
                    "year_pillar": yearly_engine.get_year_pillar(year),
                }
                for year in selected_years
            ]
            if selected_years
            else _target_year_facts(question)
        )
        projected_periods = _safe_dayun_periods(
            dayun_periods,
            str(raw["day_master"]),
        )
        if projected_periods:
            chart_facts["dayun_periods"] = projected_periods
    return chart_facts


def _build_grounded_context(
    packet: FactPacket,
    plan: AnalysisPlan,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    canonical_chart_facts: Mapping[str, object] | None,
) -> AIRequestContext:
    if packet.resolved != plan.resolved:
        raise ValueError("grounded_context_resolution_mismatch")
    chart_facts = (
        dict(canonical_chart_facts)
        if canonical_chart_facts is not None
        else {
            "fact_items": [
                item.model_dump(mode="json")
                for item in packet.facts
            ]
        }
    )
    return AIRequestContext(
        question=packet.resolved.safe_question,
        category=packet.resolved.domain,
        requires_timing=packet.resolved.time_scope != "none",
        chart_facts=chart_facts,
        rule_evidence=list(packet.rule_evidence),
        history=_safe_history(history),
        resolved_question=packet.resolved,
        fact_packet=packet,
        analysis_plan=plan,
    )


@overload
def build_ai_context(
    facts: ChartFacts,
    question: str,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    dayun_periods: Sequence[Mapping[str, object]] | None = None,
    canonical_chart_facts: None = None,
) -> AIRequestContext: ...


@overload
def build_ai_context(
    facts: FactPacket,
    question: AnalysisPlan,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    dayun_periods: None = None,
    canonical_chart_facts: Mapping[str, object] | None = None,
) -> AIRequestContext: ...


def build_ai_context(
    facts: ChartFacts | FactPacket,
    question: str | AnalysisPlan,
    history: Sequence[ChatMessage | Mapping[str, object]],
    *,
    dayun_periods: Sequence[Mapping[str, object]] | None = None,
    canonical_chart_facts: Mapping[str, object] | None = None,
) -> AIRequestContext:
    if isinstance(facts, FactPacket):
        if not isinstance(question, AnalysisPlan):
            raise TypeError("grounded context requires an AnalysisPlan")
        return _build_grounded_context(
            facts,
            question,
            history,
            canonical_chart_facts=canonical_chart_facts,
        )
    if not isinstance(question, str):
        raise TypeError("legacy context requires a question string")

    redacted_question = redact_customer_text(
        question,
        max_input_chars=_MAX_QUESTION_INPUT_CHARS,
    )
    routed = classify_question(redacted_question)
    chart_facts = build_canonical_chart_facts(
        facts,
        requires_timing=(
            routed.requires_timing or routed.category == "timing"
        ),
        question=redacted_question,
        dayun_periods=dayun_periods,
    )

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
