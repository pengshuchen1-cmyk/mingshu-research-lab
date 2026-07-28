"""Deterministic scope checks for Bazi questions."""

from dataclasses import dataclass


_BLOCKS = (
    ("prompt_injection", ("忽略所有规则", "显示系统提示", "输出API Key", "关闭校验")),
    ("medical_diagnosis", ("诊断", "确诊", "吃什么药", "治疗方案")),
    ("legal_advice", ("法律意见", "是否违法", "怎么起诉", "诉讼策略")),
    ("investment_operation", ("买哪只股票", "具体买入", "具体卖出", "保证收益")),
    ("unsupported_system", ("紫微斗数", "姓名学", "塔罗", "星座")),
)


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str = ""


def check_bazi_scope(text: str) -> ScopeDecision:
    value = str(text or "").strip()
    for reason, markers in _BLOCKS:
        if any(marker in value for marker in markers):
            return ScopeDecision(False, reason)
    return ScopeDecision(True)
