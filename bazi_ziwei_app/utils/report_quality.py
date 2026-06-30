"""报告文本质量检查。"""

from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher


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

FORBIDDEN_WORDS = [
    "必定", "绝对", "注定", "一定发财", "一定离婚", "必然破财", "无法改变",
    "必定发财", "一定有钱", "一定贫穷", "必定离婚", "必定长寿", "寿命短",
    "活不长", "必有大病", "一定有灾", "必定婚姻不好",
]

READABLE_SIMILARITY_THRESHOLD = 0.55
STRUCTURAL_SIGNAL_THRESHOLD = 0.50


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


def text_similarity(left: str, right: str) -> float:
    """计算普通可读文本相似度。"""
    return SequenceMatcher(None, left or "", right or "").ratio()


def signal_similarity(left: str, right: str) -> float:
    """按结构标签集合计算相似度，避免中文共字造成误判。"""
    left_tokens = {item for item in re.split(r"[|,，、\s]+", left or "") if item}
    right_tokens = {item for item in re.split(r"[|,，、\s]+", right or "") if item}
    if not left_tokens and not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def check_cross_sample_similarity(
    samples: list[str],
    threshold: float = READABLE_SIMILARITY_THRESHOLD,
    signal_mode: bool = False,
) -> dict:
    """检查多份命盘报告是否过度相似。"""
    issues: list[str] = []
    suggestions: list[str] = []
    if len(samples or []) < 2:
        return _result([], [])
    metric = signal_similarity if signal_mode else text_similarity
    max_score = 0.0
    max_pair = ""
    for left in range(len(samples)):
        for right in range(left + 1, len(samples)):
            score = metric(samples[left], samples[right])
            if score > max_score:
                max_score = score
                max_pair = f"{left + 1} vs {right + 1}"
    if max_score > threshold:
        issues.append(f"不同命盘报告相似度过高：{max_score:.3f}（{max_pair}）。")
        suggestions.append("请增加日主、强弱、喜忌、十神落位、夫妻宫、时柱和事件焦点等命盘差异依据。")
    return {
        **_result(issues, suggestions),
        "max_similarity": round(max_score, 3),
        "max_pair": max_pair,
        "threshold": threshold,
    }


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


def check_life_overview_completeness(life_overview: dict) -> dict:
    """
    检查命盘总体结论完整度。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    if not life_overview:
        return _result(["命盘总体结论为空。"], ["请生成命盘总体结论。"])

    required_keys = ["wealth_overview", "romance_overview", "health_overview", "career_overview"]
    missing = [k for k in required_keys if k not in life_overview]
    if missing:
        issues.append(f"命盘总览缺少：{'、'.join(missing)}。")

    if not life_overview.get("evidence"):
        issues.append("命盘总览缺少判断依据 (evidence)。")
    if not life_overview.get("source_ids"):
        issues.append("命盘总览缺少参考来源 (source_ids)。")
    if not life_overview.get("source_titles"):
        issues.append("命盘总览缺少参考书名 (source_titles)。")

    health = life_overview.get("health_overview", {})
    disclaimer = health.get("medical_disclaimer", "")
    if not disclaimer:
        issues.append("健康总览缺少医学免责声明。")

    text = str(life_overview)
    forbidden = check_forbidden_words(text)
    issues.extend(forbidden["issues"])

    if issues:
        suggestions.extend(["请确保命盘总览包含四个维度、判断依据和参考来源。",
                            "健康部分必须包含医学免责声明。",
                            "避免使用绝对化断言。"])
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
