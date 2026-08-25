"""Shared deterministic intent predicates for local and cloud Bazi answers."""

from __future__ import annotations

import re

CURRENT_MARRIAGE_STATUS_MARKER = "当前婚姻状态"
CURRENT_MARRIAGE_DISCLAIMER = "单凭八字，不能确认现实中的婚姻登记状态。"

_CURRENT_MARRIAGE_QUERY = re.compile(
    r"(?:"
    r"婚姻(?:登记)?(?:状态|状况)\s*(?:如何|怎样|怎么样|是什么|吗)"
    r"|登记状态\s*(?:如何|怎样|怎么样|是什么|吗)"
    r"|是否(?:已经)?结婚|有没有结婚|结婚了吗"
    r"|是否(?:属于)?已婚(?:人士|状态)?|已婚了吗|已婚吗"
    r"|(?:是)?未婚还是已婚"
    r"|有无配偶|有没有配偶|是否有配偶|有配偶吗"
    r")"
)
_CURRENT_MARRIAGE_STATUS_STATEMENT = re.compile(
    r"(?:现在|目前|当前|如今|现阶段|此刻).{0,8}"
    r"(?:未婚|已婚|有配偶|无配偶)"
)
_RELATIONSHIP_QUERY = re.compile(
    r"(?:想|只想|要|请)?(?:问|看|分析|了解|聊).{0,12}"
    r"(?:姻缘|婚姻|感情|关系|配偶)"
)
_NON_RELATIONSHIP_TOPIC = re.compile(
    r"(?:财运|正财|偏财|赚钱|收入|投资|创业|房贷|抵押|"
    r"事业|工作|职业|升职|行业|岗位|官运|"
    r"原生家庭|父母|长辈|家庭|健康|身体|作息|精力|"
    r"子女|孩子|生育|养育|学业|学习|考试|升学|"
    r"迁移|外地|出国|搬家|异地|房产|买房|置业|住房|"
    r"贵人|助力|提携|平台资源|合作资源)"
)
_CLAUSE_BOUNDARY = re.compile(r"[，,。；;！？!?\r\n]")
_NEGATION_OPERATOR = re.compile(
    r"(?:不需要|不要|无需|无须|不用|不想|不必|不|别)(?:再)?"
)
_POSITIVE_INTENT_OPERATOR = re.compile(
    r"(?:还是|但|不过|改为|改成|请|想|希望|需要|要|麻烦)"
)
_STATUS_INTENT_VERB = re.compile(
    r"(?:问|看|分析|判断|讨论|了解|知道|确认|回答)"
)


def _last_status_request(value: str) -> re.Match[str] | None:
    candidates = list(_CURRENT_MARRIAGE_QUERY.finditer(value))
    candidates.extend(
        re.finditer(re.escape(CURRENT_MARRIAGE_STATUS_MARKER), value)
    )
    return max(candidates, key=lambda match: match.start()) if candidates else None


def _containing_clause(
    value: str,
    request: re.Match[str],
) -> tuple[str, str]:
    prefix_boundaries = list(_CLAUSE_BOUNDARY.finditer(value, 0, request.start()))
    clause_start = (
        prefix_boundaries[-1].end()
        if prefix_boundaries
        else 0
    )
    suffix_boundary = _CLAUSE_BOUNDARY.search(value, request.end())
    clause_end = suffix_boundary.start() if suffix_boundary else len(value)
    return (
        value[clause_start:request.start()],
        value[request.end():clause_end],
    )


def _has_negated_status_intent(
    fragment: str,
    *,
    status_request_follows: bool,
) -> bool:
    """Bind the latest intent verb to operators in its local verb phrase."""
    intent_verbs = list(_STATUS_INTENT_VERB.finditer(fragment))
    if not intent_verbs:
        return False

    intent_verb = intent_verbs[-1]
    phrase_start = intent_verbs[-2].end() if len(intent_verbs) > 1 else 0
    operator_phrase = fragment[phrase_start:intent_verb.start()]
    negations = list(_NEGATION_OPERATOR.finditer(operator_phrase))
    if not negations:
        return False

    latest_negation = negations[-1]
    if _POSITIVE_INTENT_OPERATOR.search(
        operator_phrase[latest_negation.end():]
    ):
        return False

    if (
        status_request_follows
        and _NON_RELATIONSHIP_TOPIC.search(fragment[intent_verb.end():])
    ):
        return False
    return True


def is_current_marriage_question(text: object) -> bool:
    value = str(text or "").strip()
    request = _last_status_request(value)
    if request is not None:
        clause_prefix, clause_suffix = _containing_clause(value, request)
        if (
            _has_negated_status_intent(
                clause_prefix,
                status_request_follows=True,
            )
            or _has_negated_status_intent(
                clause_suffix,
                status_request_follows=False,
            )
        ):
            return False
        if _NON_RELATIONSHIP_TOPIC.search(value, request.end()):
            return False
        return True
    return bool(
        _CURRENT_MARRIAGE_STATUS_STATEMENT.search(value)
        and _RELATIONSHIP_QUERY.search(value)
    )
