"""报告文本质量检查。"""

from __future__ import annotations

import re
from collections import Counter


LOW_INFORMATION_PHRASES = [
    "平稳观察",
    "稳步积累",
    "稳步观察",
    "不宜简单判断好坏",
    "需要注意变化",
    "现实反馈",
]

YEARLY_REQUIRED_FIELDS = [
    "career_text",
    "wealth_text",
    "relationship_text",
    "health_text",
    "risk_text",
    "advice_text",
]

FORBIDDEN_WORDS = ["必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变"]


def _result(issues: list[str], suggestions: list[str]) -> dict:
    """统一返回格式。"""
    return {
        "passed": not issues,
        "issues": issues,
        "suggestions": suggestions,
    }


def _sentences(text: str) -> list[str]:
    """按中文标点和换行切分句子。"""
    parts = re.split(r"[。！？!?\n]+", text or "")
    return [re.sub(r"^\s*[-*]\s*", "", item).strip() for item in parts if item.strip()]


def check_text_repetition(text: str) -> dict:
    """
    检查报告中重复句子、重复短语、低信息量模板句。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    sentences = _sentences(text)
    counts = Counter(sentences)
    repeated = [sentence for sentence, count in counts.items() if count > 3]
    if repeated:
        issues.append("报告中存在同一句出现超过3次的重复内容。")
        suggestions.append("请改写重复句，增加对应年度、月份、十神或事件标签的具体差异。")

    low_info_hits = {
        phrase: (text or "").count(phrase)
        for phrase in LOW_INFORMATION_PHRASES
        if (text or "").count(phrase) > 3
    }
    if low_info_hits:
        issues.append("报告中低信息量模板句出现过多。")
        suggestions.append("请减少泛泛的观察语，补充事业、财务、关系、健康和行动建议。")

    return _result(issues, suggestions)


def check_monthly_diversity(monthly_data: list[dict]) -> dict:
    """
    检查12个月的主题、事件标签、建议是否过度重复。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    if len(monthly_data or []) != 12:
        issues.append("流月数据不是12个月。")
        suggestions.append("请确保 analyze_monthly_fortune 返回完整12个月。")
        return _result(issues, suggestions)

    themes = [item.get("theme", "") for item in monthly_data]
    tag_sets = ["、".join(item.get("event_tags", [])) for item in monthly_data]
    advice_texts = [item.get("advice_text", "") for item in monthly_data]

    if len(set(themes)) < 8:
        issues.append("12个月流月主题重复度过高。")
        suggestions.append("请结合流月干支、十神、喜忌和冲动关系生成不同主题。")
    if len(set(tag_sets)) < 8:
        issues.append("12个月事件标签重复度过高。")
        suggestions.append("请从事件规则库匹配不同事业、财务、关系和状态标签。")
    if len(set(advice_texts)) < 8:
        issues.append("12个月行动建议重复度过高。")
        suggestions.append("请让建议跟随十神、喜忌和事件标签变化。")

    for item in monthly_data:
        if len(item.get("likely_events", [])) < 3:
            issues.append(f"{item.get('month_name', '某月')}缺少3条以上大概率事件。")
            suggestions.append("请为每个月补充至少3条具体事件倾向。")
            break

    return _result(issues, suggestions)


def check_yearly_detail(yearly_data: dict) -> dict:
    """
    检查年度运程是否包含事业、财运、关系、健康、风险、建议等详细字段。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    for key in YEARLY_REQUIRED_FIELDS:
        if not yearly_data.get(key):
            issues.append(f"年度运程缺少 {key}。")
    for key in ["suitable_actions", "actions_to_avoid", "high_attention_months", "opportunity_months"]:
        if key not in yearly_data:
            issues.append(f"年度运程缺少 {key}。")

    if issues:
        suggestions.append("请补齐年度总览、事业、财运、关系、健康、风险、建议和月份提示字段。")
    return _result(issues, suggestions)


def check_forbidden_words(text: str) -> dict:
    """
    检查报告中是否出现禁用绝对化词汇。
    """
    hits = [word for word in FORBIDDEN_WORDS if word in (text or "")]
    issues = [f"报告中出现禁用词：{'、'.join(hits)}。"] if hits else []
    suggestions = ["请改成“大概率、倾向、容易、建议”等趋势参考表达。"] if hits else []
    return _result(issues, suggestions)


def check_required_fields(data: dict, fields: list[str], label: str = "报告") -> dict:
    """
    检查字典字段完整度。
    """
    missing = [field for field in fields if not data.get(field)]
    issues = [f"{label}缺少字段：{'、'.join(missing)}。"] if missing else []
    suggestions = [f"请补齐{label}必要字段。"] if missing else []
    return _result(issues, suggestions)


def check_yearly_series_diversity(yearly_data: list[dict]) -> dict:
    """
    检查未来十年流年差异度。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    briefs = [item.get("brief_text") or item.get("overall_text", "") for item in yearly_data or []]
    if len(briefs) < 2:
        issues.append("流年数据不足，无法检查未来十年差异度。")
    elif len(set(briefs)) < max(2, len(briefs) // 2):
        issues.append("未来流年文案重复度过高。")
        suggestions.append("请结合年份干支、十神、喜忌和地支关系生成不同提示。")
    return _result(issues, suggestions)


def check_special_report_completeness(report: dict, required_titles: list[str]) -> dict:
    """
    检查专项报告完整度。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    section_titles = [item.get("title", "") for item in report.get("sections", [])]
    missing = [title for title in required_titles if title not in section_titles]
    if not report.get("title"):
        issues.append("专项报告缺少标题。")
    if not report.get("advice"):
        issues.append("专项报告缺少行动建议。")
    if missing:
        issues.append(f"专项报告缺少段落：{'、'.join(missing)}。")
    text = str(report)
    forbidden = check_forbidden_words(text)
    issues.extend(forbidden["issues"])
    if issues:
        suggestions.append("请补齐专项报告结构，并避免绝对化表达。")
    return _result(issues, suggestions)
