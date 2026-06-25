"""专项报告公共工具。"""

from __future__ import annotations

from core.rule_engine import build_context_from_chart, load_rules, match_rules


DISCLAIMER = "本报告基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。"


def _section(title: str, text: str) -> dict:
    """生成报告段落。"""
    return {"title": title, "text": text}


def _matched_texts(chart: dict, rule_file: str) -> list[str]:
    """返回命中的规则文案。"""
    rules = load_rules(rule_file)
    context = build_context_from_chart(chart)
    matched = match_rules(context, rules)
    if not matched:
        matched = rules.get("rules", [])[:1]
    return [f"{item.get('text', '')} {item.get('advice', '')}".strip() for item in matched]


def _ten_god_counts(chart: dict) -> dict:
    """读取十神统计。"""
    return chart.get("ten_god_counts", {})


def _has_any(counts: dict, names: set[str]) -> bool:
    """判断是否存在某类十神。"""
    return any(counts.get(name, 0) > 0 for name in names)


def _future_three_years(prefix: str) -> str:
    """生成未来三年趋势占位说明。"""
    return (
        f"未来三年可按年度运程逐年观察。{prefix}建议重点看流年十神、喜忌关系和高关注月份，"
        "把年度提示转化为现实中的计划、预算和沟通安排。"
    )


def build_special_markdown(report: dict) -> str:
    """把专项报告转为 Markdown。"""
    lines = [f"# {report.get('title', '专项报告')}", ""]
    if report.get("evidence"):
        lines.extend(["## 命盘依据", *[f"- {item}" for item in report.get("evidence", [])], ""])
    for item in report.get("sections", []):
        lines.extend([f"## {item.get('title', '')}", item.get("text", ""), ""])
    lines.extend(["## 行动建议", report.get("advice", ""), "", "## 免责声明", report.get("disclaimer", DISCLAIMER), ""])
    return "\n".join(lines)
