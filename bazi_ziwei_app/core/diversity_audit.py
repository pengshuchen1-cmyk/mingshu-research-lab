"""40 命例的确定性、完整性、性能与文案差异审计。"""

from __future__ import annotations

import json
import math
import re
import time
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any, Iterable


SECTION_KEYS = (
    "identity",
    "five_dimensions",
    "career",
    "wealth",
    "relationship",
    "yearly",
    "monthly",
)
THRESHOLDS = {"fail_above": 0.85, "review_from": 0.70, "p95_max": 0.70}
_SAMPLE_ID = re.compile(r"样例[-－—]?\s*\d{1,3}", re.IGNORECASE)
_DATE = re.compile(r"\b(?:19|20)\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?\b")
_TIME = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")
_COMPACT_NOISE = re.compile(r"[^\u3400-\u9fffA-Za-z0-9]+")
_TEXT_SKIP_KEYS = {
    "profile", "name", "case_id", "source_ids", "source_titles", "disclaimer",
    "medical_disclaimer", "boundary_note", "birth_date", "birth_hour", "birth_minute",
    "birth_longitude", "original_birth_datetime", "adjusted_birth_datetime",
}
_NUMERIC_TEXT_KEYS = {
    "score", "net_score", "support_score", "pressure_score", "count", "trigger_count",
}


def normalize_personalized_text(text: object) -> str:
    """移除样例身份和时间噪音，保留命盘结构、依据与行动内容。"""
    normalized = unicodedata.normalize("NFKC", str(text or ""))
    normalized = _SAMPLE_ID.sub("", normalized)
    normalized = _DATE.sub("", normalized)
    normalized = _TIME.sub("", normalized)
    return _COMPACT_NOISE.sub("", normalized).lower()


def _ngrams(text: str, size: int = 3) -> Counter[str]:
    if not text:
        return Counter()
    if len(text) <= size:
        return Counter({text: 1})
    return Counter(text[index : index + size] for index in range(len(text) - size + 1))


def _multiset_dice(left: Counter[str], right: Counter[str]) -> float:
    total = sum(left.values()) + sum(right.values())
    if total == 0:
        return 1.0
    overlap = sum((left & right).values())
    return (2.0 * overlap) / total


def _weighted_multiset_dice(
    left: Counter[str], right: Counter[str], weights: dict[str, float]
) -> float:
    total = sum(count * weights.get(gram, 0.0) for gram, count in left.items())
    total += sum(count * weights.get(gram, 0.0) for gram, count in right.items())
    if total == 0:
        return 1.0
    overlap = sum(
        min(count, right.get(gram, 0)) * weights.get(gram, 0.0)
        for gram, count in left.items()
    )
    return (2.0 * overlap) / total


def _prepare_text(value: object) -> dict[str, Any]:
    normalized = normalize_personalized_text(value)
    return {
        "normalized": normalized,
        "blocks": tuple(normalized[index : index + 256] for index in range(0, len(normalized), 256)),
        "ngrams": _ngrams(normalized),
    }


def _compare_prepared(
    left: dict[str, Any], right: dict[str, Any], *, weights: dict[str, float] | None = None
) -> dict[str, float]:
    # 长报告逐字比较会让 SequenceMatcher 在重复模板上退化；固定文本块仍比较
    # 完整正文的顺序，同时把序列规模压到可重复跑 5,460 对的范围。
    sequence = SequenceMatcher(None, left["blocks"], right["blocks"]).ratio()
    ngram = (
        _weighted_multiset_dice(left["ngrams"], right["ngrams"], weights)
        if weights is not None
        else _multiset_dice(left["ngrams"], right["ngrams"])
    )
    score = (0.85 * ngram + 0.15 * sequence) if weights is not None else max(sequence, ngram)
    return {
        "score": round(score, 6),
        "sequence": round(sequence, 6),
        "char_3gram_dice": round(ngram, 6),
    }


def compare_texts(left: object, right: object) -> dict[str, float]:
    return _compare_prepared(_prepare_text(left), _prepare_text(right))


def percentile(values: Iterable[float], percentile_value: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    rank = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[min(rank, len(ordered) - 1)]


def _flatten_text(value: Any, *, key: str = "") -> list[str]:
    if key in _TEXT_SKIP_KEYS:
        return []
    if isinstance(value, dict):
        parts: list[str] = []
        for child_key, child in value.items():
            parts.extend(_flatten_text(child, key=str(child_key)))
        return parts
    if isinstance(value, (list, tuple)):
        parts = []
        for child in value:
            parts.extend(_flatten_text(child, key=key))
        return parts
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if key in _NUMERIC_TEXT_KEYS and isinstance(value, (int, float)) and not isinstance(value, bool):
        return [f"{key}={value}"]
    return []


def _joined_text(value: Any) -> str:
    return "\n".join(_flatten_text(value))


def joined_audit_text(value: Any) -> str:
    """测试与报告脚本共用的稳定文本投影。"""
    return _joined_text(value)


def build_identity_audit_text(identity: dict[str, Any], term_views: list[dict[str, Any]]) -> str:
    """只比较身份结论和术语在本盘中的作用，不把大众词典定义算作差异。"""
    personalized_terms = [
        {
            "term_id": term.get("term_id", ""),
            "label": term.get("label", ""),
            "personalized": term.get("personalized", {}),
        }
        for term in term_views
        if isinstance(term.get("personalized"), dict) and term.get("personalized")
    ]
    return _joined_text({"identity": identity, "personalized_terms": personalized_terms})


def build_monthly_audit_text(
    monthly: list[dict[str, Any]], monthly_events: list[dict[str, Any]]
) -> str:
    """比较用户实际可见的流月结论，不把内部评分池、规则编号和调试证据算入正文。"""
    visible_months: list[dict[str, Any]] = []
    for index, event_result in enumerate(monthly_events):
        month = monthly[index] if index < len(monthly) else {}
        visible_events = []
        for event in (event_result.get("top_events") or [])[:3]:
            visible_events.append(
                {
                    "label": event.get("label", ""),
                    "probability_level": event.get("probability_level", ""),
                    "summary": event.get("plain_summary") or event.get("one_line") or "",
                    "reason": event.get("reason", ""),
                    "real_world_signals": event.get("real_world_signals", []),
                    "risk_points": event.get("risk_points", []),
                    "basis": event.get("user_visible_basis") or event.get("basis") or "",
                    "advice": event.get("advice", ""),
                }
            )
        visible_months.append(
            {
                "month_name": month.get("month_name", event_result.get("month", "")),
                "pillar": month.get("pillar", event_result.get("pillar", "")),
                "relation": month.get("relation_to_favorable", event_result.get("relation_to_favorable", "")),
                "theme": month.get("theme", ""),
                "risk_text": month.get("risk_text", ""),
                "advice_text": month.get("advice_text", ""),
                "events": visible_events,
            }
        )
    return _joined_text(visible_months)


def _build_delivery_models(chart: dict, overview: dict) -> tuple[dict, list[dict], list[dict], dict]:
    from core.bazi_term_glossary import build_term_view, collect_term_ids
    from core.presentation_models import build_chart_public_view
    from ui.life_overview_page import _build_dimension_views, _build_life_identity_card

    identity = _build_life_identity_card(chart, overview)
    evidence = [str(item) for item in overview.get("evidence", [])]
    term_ids = collect_term_ids(
        identity["term_ids"],
        [identity.get("summary", ""), overview.get("overall_pattern", ""), *evidence],
        chart,
    )
    term_views = [build_term_view(term_id, chart) for term_id in term_ids]
    dimension_views = _build_dimension_views(overview)
    public_view = build_chart_public_view(identity, term_views, dimension_views)
    return identity, term_views, dimension_views, public_view


def build_case_bundle(case: dict[str, Any], *, target_year: int = 2026) -> dict[str, Any]:
    """运行一个样例的完整可交付链路，不写数据库、不访问网络。"""
    from core.bazi_engine import build_bazi_chart
    from core.life_overview_engine import analyze_life_overview
    from core.monthly_engine import analyze_monthly_fortune
    from core.monthly_event_activation_bridge import build_year_monthly_event_results
    from core.yearly_engine import analyze_yearly_fortune
    from report.career_report import generate_career_report
    from report.love_report import generate_love_report
    from report.wealth_report import generate_wealth_report

    profile = dict(case["profile"])
    core_started = time.perf_counter()
    chart = build_bazi_chart(profile)
    core_seconds = time.perf_counter() - core_started
    if chart.get("error"):
        raise RuntimeError(str(chart["error"]))

    overview = analyze_life_overview(chart)
    identity, term_views, dimension_views, public_view = _build_delivery_models(chart, overview)
    career = generate_career_report(chart)
    wealth = generate_wealth_report(chart)
    relationship = generate_love_report(chart, profile)
    yearly = analyze_yearly_fortune(chart, target_year)
    monthly = analyze_monthly_fortune(chart, target_year)
    monthly_events = build_year_monthly_event_results(chart, monthly, yearly_data=yearly)

    texts = {
        "identity": build_identity_audit_text(identity, term_views),
        "five_dimensions": _joined_text(dimension_views),
        "career": _joined_text(career),
        "wealth": _joined_text(wealth),
        "relationship": _joined_text(relationship),
        "yearly": _joined_text(yearly),
        "monthly": build_monthly_audit_text(monthly, monthly_events),
    }
    delivery_snapshot = {
        "chart_pillars": {
            key: chart["pillars"][key]["pillar"] for key in ("year", "month", "day", "hour")
        },
        "day_master": chart["day_master"],
        "strength": chart["day_master_strength"],
        "public_view": public_view,
        "career": career,
        "wealth": wealth,
        "relationship": relationship,
        "yearly": yearly,
        "monthly": monthly,
        "monthly_events": monthly_events,
    }
    return {
        "case_id": case["case_id"],
        "core_seconds": core_seconds,
        "chart": chart,
        "overview": overview,
        "identity": identity,
        "term_views": term_views,
        "dimension_views": dimension_views,
        "public_view": public_view,
        "career": career,
        "wealth": wealth,
        "relationship": relationship,
        "yearly": yearly,
        "monthly": monthly,
        "monthly_events": monthly_events,
        "texts": texts,
        "delivery_snapshot": delivery_snapshot,
    }


def _bundle_errors(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    pillars = bundle.get("chart", {}).get("pillars", {})
    if any(not pillars.get(key, {}).get("pillar") for key in ("year", "month", "day", "hour")):
        errors.append("四柱不完整")
    if len(bundle.get("public_view", {}).get("five_dimensions", [])) != 5:
        errors.append("五维展示不完整")
    for report_key in ("career", "wealth", "relationship"):
        if not bundle.get(report_key):
            errors.append(f"{report_key} 专项报告为空")
    if not bundle.get("yearly"):
        errors.append("年度报告为空")
    if len(bundle.get("monthly", [])) != 12:
        errors.append("流月数量不是 12")
    events = bundle.get("monthly_events", [])
    if len(events) != 12 or any(not month.get("top_events") for month in events):
        errors.append("月度重点事件不完整")
    if any(not str(text).strip() for text in bundle.get("texts", {}).values()):
        errors.append("个性化审计文本存在空板块")
    return errors


def audit_case_usability(
    cases: list[dict[str, Any]],
    *,
    target_year: int = 2026,
    verify_determinism: bool = True,
) -> dict[str, Any]:
    case_results: list[dict[str, Any]] = []
    core_times: list[float] = []
    full_times: list[float] = []
    for case in cases:
        errors: list[str] = []
        deterministic = False
        json_safe = False
        bundle: dict[str, Any] | None = None
        full_seconds = 0.0
        started = time.perf_counter()
        try:
            bundle = build_case_bundle(case, target_year=target_year)
            full_seconds = time.perf_counter() - started
            errors.extend(_bundle_errors(bundle))
            encoded = json.dumps(bundle["delivery_snapshot"], ensure_ascii=False, sort_keys=True)
            json_safe = json.loads(encoded) == bundle["delivery_snapshot"]
            if not json_safe:
                errors.append("公开交付模型 JSON 往返不一致")
            if verify_determinism:
                repeated = build_case_bundle(case, target_year=target_year)
                deterministic = repeated["delivery_snapshot"] == bundle["delivery_snapshot"]
                if not deterministic:
                    errors.append("相同输入重复运行结果不一致")
            else:
                deterministic = True
        except Exception as exc:  # 审计报告必须继续收集其余样例
            errors.append(f"{type(exc).__name__}: {exc}")
            if not full_seconds:
                full_seconds = time.perf_counter() - started
        core_seconds = float(bundle.get("core_seconds", 0.0)) if bundle else 0.0
        core_times.append(core_seconds)
        full_times.append(full_seconds)
        case_results.append(
            {
                "case_id": case.get("case_id", ""),
                "passed": not errors,
                "deterministic": deterministic,
                "json_safe": json_safe,
                "core_seconds": round(core_seconds, 6),
                "full_seconds": round(full_seconds, 6),
                "errors": errors,
            }
        )
    return {
        "case_count": len(cases),
        "passed_count": sum(item["passed"] for item in case_results),
        "failed_count": sum(not item["passed"] for item in case_results),
        "deterministic_count": sum(item["deterministic"] for item in case_results),
        "json_safe_count": sum(item["json_safe"] for item in case_results),
        "core_p95_seconds": round(percentile(core_times, 0.95), 6),
        "full_p95_seconds": round(percentile(full_times, 0.95), 6),
        "cases": case_results,
    }


def audit_section_texts(section: str, texts: dict[str, str]) -> dict[str, Any]:
    prepared = {case_id: _prepare_text(text) for case_id, text in texts.items()}
    document_frequency: Counter[str] = Counter()
    for item in prepared.values():
        document_frequency.update(item["ngrams"].keys())
    document_count = max(1, len(prepared))
    weights = {
        gram: math.log((document_count + 1) / (frequency + 1))
        for gram, frequency in document_frequency.items()
    }
    pairs: list[dict[str, Any]] = []
    for left_id, right_id in combinations(sorted(texts), 2):
        metrics = _compare_prepared(prepared[left_id], prepared[right_id], weights=weights)
        normalized_equal = prepared[left_id]["normalized"] == prepared[right_id]["normalized"]
        if normalized_equal:
            classification = "失败：正文完全相同"
        elif metrics["score"] > THRESHOLDS["fail_above"]:
            classification = "失败：相似度过高"
        elif metrics["score"] >= THRESHOLDS["review_from"]:
            classification = "人工复核"
        else:
            classification = "通过"
        pairs.append(
            {
                "section": section,
                "left": left_id,
                "right": right_id,
                **metrics,
                "classification": classification,
            }
        )
    scores = [item["score"] for item in pairs]
    p95 = round(percentile(scores, 0.95), 6)
    return {
        "pair_count": len(pairs),
        "exact_duplicate_count": sum(item["classification"] == "失败：正文完全相同" for item in pairs),
        "fail_count": sum(item["classification"].startswith("失败") for item in pairs),
        "review_count": sum(item["classification"] == "人工复核" for item in pairs),
        "p95": p95,
        "max_score": max(scores, default=0.0),
        "p95_passed": p95 <= THRESHOLDS["p95_max"],
        "pairs": pairs,
    }


def _event_type_set(month: dict[str, Any]) -> set[str]:
    return {
        str(event.get("event_type"))
        for event in month.get("top_events", [])[:3]
        if event.get("event_type")
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def audit_monthly_event_overlap(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    cross_values: list[float] = []
    for month_index in range(12):
        month_sets = [
            (bundle["case_id"], _event_type_set(bundle["monthly_events"][month_index]))
            for bundle in bundles
            if len(bundle.get("monthly_events", [])) > month_index
        ]
        for (_left_id, left), (_right_id, right) in combinations(month_sets, 2):
            cross_values.append(_jaccard(left, right))

    per_chart: dict[str, float] = {}
    for bundle in bundles:
        sets = [_event_type_set(month) for month in bundle.get("monthly_events", [])]
        repeats = [_jaccard(left, right) for left, right in combinations(sets, 2)]
        per_chart[bundle["case_id"]] = max(repeats, default=0.0)
    return {
        "cross_chart_same_month_average": round(sum(cross_values) / len(cross_values), 6) if cross_values else 0.0,
        "cross_chart_pair_count": len(cross_values),
        "per_chart_max_month_repeat": round(max(per_chart.values(), default=0.0), 6),
        "per_chart": per_chart,
        "cross_chart_passed": (sum(cross_values) / len(cross_values) if cross_values else 0.0) <= 0.35,
        "per_chart_passed": max(per_chart.values(), default=0.0) <= 0.50,
    }


def audit_bundle_diversity(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    sections: dict[str, dict[str, Any]] = {}
    all_pairs: list[dict[str, Any]] = []
    for section in SECTION_KEYS:
        result = audit_section_texts(
            section,
            {bundle["case_id"]: bundle["texts"][section] for bundle in bundles},
        )
        sections[section] = result
        all_pairs.extend(result["pairs"])
    top = sorted(all_pairs, key=lambda item: (-item["score"], item["section"], item["left"], item["right"]))[:20]
    return {
        "thresholds": dict(THRESHOLDS),
        "sections": sections,
        "top_similar_pairs": top,
        "monthly_event_overlap": audit_monthly_event_overlap(bundles),
    }
