"""Shared deterministic intent predicates for local and cloud Bazi answers."""

from __future__ import annotations

import re


CURRENT_MARRIAGE_STATUS_MARKER = "当前婚姻状态"
CURRENT_MARRIAGE_DISCLAIMER = "单凭八字，不能确认现实中的婚姻登记状态。"

_CURRENT_MARRIAGE_STATUS = re.compile(
    r"(?:"
    r"(?:现在|目前|当前|如今|现阶段|此刻).{0,8}"
    r"(?:婚姻(?:登记)?(?:状态|状况)|登记状态|"
    r"是否(?:已经)?结婚|有没有结婚|结婚了吗|"
    r"是否(?:属于)?已婚|已婚吗|未婚还是已婚|未婚|已婚|"
    r"有无配偶|有没有配偶|是否有配偶|有配偶吗)"
    r"|是否已婚|已婚了吗|未婚还是已婚|"
    r"有无配偶|有没有配偶|是否有配偶|有配偶吗"
    r")"
)


def is_current_marriage_question(text: object) -> bool:
    value = str(text or "")
    return (
        CURRENT_MARRIAGE_STATUS_MARKER in value
        or bool(_CURRENT_MARRIAGE_STATUS.search(value))
    )
