"""Deterministic scope checks for Bazi questions."""

from dataclasses import dataclass
import re


_BLOCKS = (
    (
        "prompt_injection",
        (
            "忽略规则",
            "忽略所有规则",
            "显示系统提示",
            "关闭校验",
        ),
    ),
    ("medical_diagnosis", ("诊断", "确诊", "吃什么药", "治疗方案")),
    ("legal_advice", ("法律意见", "是否违法", "怎么起诉", "诉讼策略")),
    ("investment_operation", ("买哪只股票", "具体买入", "具体卖出", "保证收益")),
    ("unsupported_system", ("紫微斗数", "姓名学", "塔罗", "星座")),
)
_SECRET_MARKERS = (
    "apikey",
    "openaiapikey",
    "moonshotapikey",
    "kimiapikey",
    "apitoken",
    "密钥",
    "moonshotkey",
    "openaikey",
    "kimikey",
    "token",
    "令牌",
    "accesskey",
    "secretkey",
)
@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str = ""


def _normalized(text: str) -> str:
    return re.sub(r"[\s_`-]+", "", str(text or "").casefold())


def _is_safe_secret_clause(clause: str) -> bool:
    marker = "(?:" + "|".join(
        re.escape(_normalized(value))
        for value in _SECRET_MARKERS
    ) + ")"
    safe_patterns = (
        (
            rf"(?:请)?(?:告诉我)?(?:应该)?(?:如何|怎么)"
            rf"(?:配置|设置|保管|存储){marker}(?:环境变量)?(?:吗)?"
        ),
        (
            rf"(?:请)?{marker}(?:应该)?(?:如何|怎么)"
            rf"(?:配置|设置|保管|存储)(?:环境变量)?(?:吗)?"
        ),
        (
            rf"(?:请)?(?:可以|能否)?查看{marker}(?:的)?"
            rf"(?:最后使用时间|使用记录|调用记录|配置状态)(?:吗)?"
        ),
        (
            rf"(?:请)?告诉我{marker}(?:的)?"
            rf"(?:最后使用时间|使用记录|调用记录|配置状态)(?:吗)?"
        ),
        (
            rf"(?:请问)?{marker}(?:不会|是否会|会不会)"
            rf"发送到(?:云端|kimi|openai)(?:吗)?"
        ),
    )
    return any(re.fullmatch(pattern, clause) for pattern in safe_patterns)


def check_bazi_scope(text: str) -> ScopeDecision:
    value = str(text or "").strip()
    normalized = _normalized(value)
    for reason, markers in _BLOCKS:
        if any(_normalized(marker) in normalized for marker in markers):
            return ScopeDecision(False, reason)
    for raw_clause in re.split(
        r"[，,。；;！？!?\r\n]+|(?:并且|同时|顺便|另外|然后|以及|并)",
        value,
    ):
        clause = _normalized(raw_clause)
        has_secret_marker = any(
            _normalized(marker) in clause
            for marker in _SECRET_MARKERS
        )
        if has_secret_marker and not _is_safe_secret_clause(clause):
            return ScopeDecision(False, "prompt_injection")
    return ScopeDecision(True)
