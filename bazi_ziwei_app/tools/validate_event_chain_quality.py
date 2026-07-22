"""Validate monthly event evidence-chain quality.

This script is a gate before expanding the event pool. It checks whether
evidence-chain events can be traced from traditional basis to modern scenarios,
instead of being only event names plus repeated copy.
"""

from __future__ import annotations

import argparse
import difflib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CHAIN_FIELDS = [
    "traditional_basis",
    "structure_basis",
    "palace_basis",
    "modern_mapping",
    "confidence_basis",
    "anti_triggers",
    "user_visible_basis",
    "required_evidence_count",
    "subtype_rules",
]

TRADITIONAL_BASIS_KEYS = [
    "ten_god_basis",
    "element_basis",
    "branch_relation_basis",
    "shensha_basis",
]

MODERN_MAPPING_ALIASES = {
    "positive": ("positive_forms", "positive_expression"),
    "neutral": ("neutral_forms", "neutral_expression"),
    "negative": ("negative_forms", "negative_expression"),
}

CONFIDENCE_KEYS = ["high", "medium", "low", "downgrade_reasons"]

RISK_CATEGORIES = {
    "财务支出",
    "合同法务",
    "交通车辆",
    "房产居住",
    "感情婚恋",
    "健康状态",
    "风险损耗",
}

TECHNICAL_TERMS = [
    "十神",
    "官杀",
    "印星",
    "比劫",
    "食伤",
    "财星",
    "日支",
    "月支",
    "喜用",
    "忌神",
    "冲克",
    "合冲刑害",
    "流月",
    "大运",
    "宫位",
    "天乙",
]

PLAIN_LANGUAGE_HINTS = [
    "现实",
    "工作",
    "客户",
    "门店",
    "客流",
    "供应商",
    "进货",
    "库存",
    "定价",
    "价格",
    "折扣",
    "宣传",
    "广告",
    "品牌",
    "账号",
    "粉丝",
    "钱款",
    "款项",
    "金额",
    "奖金",
    "薪资",
    "工资",
    "考核",
    "上级",
    "组织",
    "绩效",
    "提成",
    "业绩",
    "分成",
    "时间",
    "流程",
    "凭证",
    "合作",
    "关系",
    "家人",
    "长辈",
    "父母",
    "亲戚",
    "兄弟",
    "家庭",
    "朋友",
    "同辈",
    "健康",
    "身体",
    "睡眠",
    "沟通",
    "合同",
    "资料",
    "文件",
    "证件",
    "规则",
    "处罚",
    "表达",
    "传播",
    "财务",
    "资源",
    "人缘",
    "车辆",
    "出行",
    "行程",
    "路线",
    "罚单",
    "违章",
    "远行",
    "差旅",
    "房屋",
    "房子",
    "看房",
    "租房",
    "买房",
    "居住",
    "装修",
    "家具",
    "家电",
    "房东",
    "租客",
    "店铺",
    "名声",
    "评价",
    "流言",
    "争执",
    "宴席",
    "聚会",
    "支出",
    "成本",
    "小额",
    "损耗",
    "设备",
    "工具",
    "延误",
    "拖延",
    "滞后",
    "冲动",
    "维护",
    "人情",
    "建议",
    "注意",
    "需要",
    "可以",
    "如果",
    "帮助",
    "压力",
]


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return [value] if value else []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(_has_content(item) for item in value)
    if isinstance(value, dict):
        return any(_has_content(item) for item in value.values())
    return True


def _event_source_ids(item: dict[str, Any], rules: list[dict[str, Any]] | None = None) -> list[str]:
    source_ids: list[str] = []
    source_ids.extend(str(sid) for sid in _as_list(item.get("source_ids")) if str(sid).strip())
    traditional = item.get("traditional_basis", {})
    if isinstance(traditional, dict):
        source_ids.extend(str(sid) for sid in _as_list(traditional.get("source_ids")) if str(sid).strip())
    for rule in rules or []:
        source_ids.extend(str(sid) for sid in _as_list(rule.get("source_ids")) if str(sid).strip())
        for condition in _as_list(rule.get("trigger_conditions")):
            if isinstance(condition, dict):
                source_ids.extend(str(sid) for sid in _as_list(condition.get("source_ids")) if str(sid).strip())
    return sorted(set(source_ids))


def _is_chain_event(item: dict[str, Any]) -> bool:
    return any(field in item for field in CHAIN_FIELDS)


def _modern_mapping_forms(mapping: dict[str, Any], mood: str) -> list[Any]:
    for key in MODERN_MAPPING_ALIASES[mood]:
        forms = _as_list(mapping.get(key))
        if forms:
            return forms
    return []


def _visible_basis_is_plain(text: Any) -> bool:
    if not isinstance(text, str) or len(text.strip()) < 12:
        return False
    technical_hits = sum(1 for term in TECHNICAL_TERMS if term in text)
    plain_hits = sum(1 for term in PLAIN_LANGUAGE_HINTS if term in text)
    return plain_hits >= 1 and technical_hits <= 6


def _index_rules(trigger_rules: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in trigger_rules:
        event_type = rule.get("target_event_type")
        if event_type:
            indexed[str(event_type)].append(rule)
    return dict(indexed)


def _trigger_conditions(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    for rule in rules:
        for condition in _as_list(rule.get("trigger_conditions")):
            if isinstance(condition, dict) and condition.get("type"):
                conditions.append(condition)
    return conditions


def _condition_signature(condition: dict[str, Any]) -> str:
    value = condition.get("value", "")
    if isinstance(value, (list, tuple)):
        value_text = ",".join(str(item) for item in value)
    elif isinstance(value, dict):
        value_text = ",".join(f"{k}:{v}" for k, v in sorted(value.items()))
    else:
        value_text = str(value)
    return f"{condition.get('type')}={value_text}"


def _rules_are_too_weak(rules: list[dict[str, Any]]) -> tuple[bool, str]:
    conditions = _trigger_conditions(rules)
    if len(conditions) < 3:
        return True, "有效触发依据少于3条"

    condition_types = {str(condition.get("type")) for condition in conditions if condition.get("type")}
    if len(condition_types) < 2:
        return True, "触发依据维度过少"

    category_like = {"category", "category_match", "event_category", "baseline", "generic"}
    if condition_types and condition_types <= category_like:
        return True, "全部触发依据停留在类别级别"

    source_hits = 0
    for rule in rules:
        if _as_list(rule.get("source_ids")):
            source_hits += 1
        for condition in _trigger_conditions([rule]):
            if _as_list(condition.get("source_ids")):
                source_hits += 1
    if source_hits == 0:
        return True, "触发规则缺少来源依据"

    return False, ""


def _event_text_for_mapping(item: dict[str, Any]) -> str:
    mapping = item.get("modern_mapping", {})
    if not isinstance(mapping, dict):
        return ""
    parts: list[str] = []
    for mood in ("positive", "neutral", "negative"):
        parts.extend(str(part) for part in _modern_mapping_forms(mapping, mood))
    return " ".join(parts)


def _event_trigger_text(rules: list[dict[str, Any]]) -> str:
    signatures = sorted(_condition_signature(condition) for condition in _trigger_conditions(rules))
    return " ".join(signatures)


def _similar_pairs(
    entries: list[tuple[str, str]],
    *,
    kind: str,
    threshold: float,
    limit: int = 40,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for index, (event_a, text_a) in enumerate(entries):
        if not text_a:
            continue
        for event_b, text_b in entries[index + 1 :]:
            if not text_b:
                continue
            score = difflib.SequenceMatcher(None, text_a, text_b).ratio()
            if score >= threshold:
                pairs.append(
                    {
                        "event_a": event_a,
                        "event_b": event_b,
                        "kind": kind,
                        "score": round(score, 3),
                    }
                )
            if len(pairs) >= limit:
                return pairs
    return pairs


def validate_event_chain_quality(root: str | Path | None = None) -> dict[str, Any]:
    """Return an event evidence-chain quality report.

    The report separates blocking issues from advisory issues. Blocking issues
    prevent high-confidence Top-event use; similarity warnings guide cleanup and
    merging but do not fail the basic gate by themselves.
    """

    root_path = Path(root) if root is not None else ROOT
    rules_dir = root_path / "rules"

    ontology = _load_json(rules_dir / "monthly_event_ontology.json", {})
    trigger_rules = _load_json(rules_dir / "monthly_event_trigger_rules.json", [])
    variants = _load_json(rules_dir / "monthly_event_variants.json", {})
    indexed_rules = _index_rules(trigger_rules if isinstance(trigger_rules, list) else [])

    if not isinstance(ontology, dict):
        ontology = {}
    if not isinstance(variants, dict):
        variants = {}

    chain_events = {
        event_type: item
        for event_type, item in ontology.items()
        if isinstance(item, dict) and _is_chain_event(item)
    }

    missing_field_events: list[dict[str, Any]] = []
    empty_field_events: list[dict[str, Any]] = []
    weak_trigger_rule_events: list[dict[str, Any]] = []
    source_ids_missing_events: list[str] = []
    anti_trigger_weak_events: list[str] = []
    variant_weak_events: list[dict[str, Any]] = []
    not_allowed_top_events: set[str] = set()
    passed_events: list[str] = []

    trigger_similarity_entries: list[tuple[str, str]] = []
    mapping_similarity_entries: list[tuple[str, str]] = []
    basis_similarity_entries: list[tuple[str, str]] = []

    for event_type, item in chain_events.items():
        rules = indexed_rules.get(event_type, [])
        event_errors = False

        missing_fields = [field for field in CHAIN_FIELDS if field not in item]
        if missing_fields:
            missing_field_events.append({"event_type": event_type, "fields": missing_fields})
            not_allowed_top_events.add(event_type)
            event_errors = True

        empty_reasons: list[str] = []

        traditional = item.get("traditional_basis", {})
        if not isinstance(traditional, dict):
            empty_reasons.append("traditional_basis 不是对象")
        else:
            has_traditional_basis = any(_has_content(traditional.get(key)) for key in TRADITIONAL_BASIS_KEYS)
            if not has_traditional_basis:
                empty_reasons.append("traditional_basis 缺少十神/五行/地支关系/神煞依据")

        structure = item.get("structure_basis", {})
        if not isinstance(structure, dict) or not _has_content(structure.get("required_patterns")):
            empty_reasons.append("structure_basis.required_patterns 为空")

        modern_mapping = item.get("modern_mapping", {})
        if not isinstance(modern_mapping, dict):
            empty_reasons.append("modern_mapping 不是对象")
        else:
            for mood, cn_label in [("positive", "正向表达"), ("neutral", "中性表达"), ("negative", "负向表达")]:
                if not _has_content(_modern_mapping_forms(modern_mapping, mood)):
                    empty_reasons.append(f"modern_mapping 缺少{cn_label}")

        confidence = item.get("confidence_basis", {})
        if not isinstance(confidence, dict):
            empty_reasons.append("confidence_basis 不是对象")
        else:
            for key in CONFIDENCE_KEYS:
                if not _has_content(confidence.get(key)):
                    empty_reasons.append(f"confidence_basis.{key} 为空")
            downgrade_text = " ".join(str(part) for part in _as_list(confidence.get("downgrade_reasons")))
            for required in ["忌神", "冲", "单一维度", "宫位"]:
                if required not in downgrade_text:
                    empty_reasons.append(f"confidence_basis.downgrade_reasons 缺少 {required} 类降级说明")

        if "anti_triggers" not in item:
            empty_reasons.append("anti_triggers 字段缺失")
        elif item.get("category") in RISK_CATEGORIES and not _has_content(item.get("anti_triggers")):
            anti_trigger_weak_events.append(event_type)

        if not _visible_basis_is_plain(item.get("user_visible_basis")):
            empty_reasons.append("user_visible_basis 不够通俗或内容过短")

        required_count = item.get("required_evidence_count")
        if not isinstance(required_count, int) or required_count < 2:
            empty_reasons.append("required_evidence_count 小于2")
            not_allowed_top_events.add(event_type)

        if not _has_content(item.get("subtype_rules")):
            empty_reasons.append("subtype_rules 为空")

        source_ids = _event_source_ids(item, rules)
        if not source_ids:
            source_ids_missing_events.append(event_type)
            not_allowed_top_events.add(event_type)
            event_errors = True

        weak, reason = _rules_are_too_weak(rules)
        if weak:
            weak_trigger_rule_events.append({"event_type": event_type, "reason": reason})
            not_allowed_top_events.add(event_type)

        event_variants = _as_list(variants.get(event_type))
        if len(event_variants) < 1:
            variant_weak_events.append({"event_type": event_type, "reason": "缺少 variants"})
        else:
            incomplete_variants = []
            for variant in event_variants:
                if not isinstance(variant, dict) or not _has_content(variant.get("one_line")) or not _has_content(variant.get("advice")):
                    incomplete_variants.append(variant.get("variant_id") if isinstance(variant, dict) else "<非对象>")
            if incomplete_variants:
                variant_weak_events.append({"event_type": event_type, "reason": f"variant 内容不完整: {incomplete_variants[:3]}"})

        if empty_reasons:
            empty_field_events.append({"event_type": event_type, "fields": empty_reasons})
            not_allowed_top_events.add(event_type)
            event_errors = True

        trigger_similarity_entries.append((event_type, _event_trigger_text(rules)))
        mapping_similarity_entries.append((event_type, _event_text_for_mapping(item)))
        basis_similarity_entries.append((event_type, str(item.get("user_visible_basis", ""))))

        if not event_errors and not weak and event_type not in not_allowed_top_events:
            passed_events.append(event_type)

    high_similarity_events: list[dict[str, Any]] = []
    high_similarity_events.extend(_similar_pairs(trigger_similarity_entries, kind="trigger_rules", threshold=0.96))
    high_similarity_events.extend(_similar_pairs(mapping_similarity_entries, kind="modern_mapping", threshold=0.94))
    high_similarity_events.extend(_similar_pairs(basis_similarity_entries, kind="user_visible_basis", threshold=0.92))

    priority: list[str] = []
    for collection in [missing_field_events, empty_field_events, weak_trigger_rule_events, variant_weak_events]:
        for item in collection:
            event_type = item.get("event_type")
            if event_type and event_type not in priority:
                priority.append(event_type)
    for event_type in source_ids_missing_events:
        if event_type not in priority:
            priority.append(event_type)
    for event_type in anti_trigger_weak_events:
        if event_type not in priority:
            priority.append(event_type)
    for pair in high_similarity_events[:12]:
        for event_type in [pair.get("event_a"), pair.get("event_b")]:
            if event_type and event_type not in priority:
                priority.append(str(event_type))

    blocking_count = (
        len(missing_field_events)
        + len(empty_field_events)
        + len(source_ids_missing_events)
        + len(not_allowed_top_events)
    )

    return {
        "basic_passed": blocking_count == 0,
        "total_event_count": len(ontology),
        "chain_event_count": len(chain_events),
        "passed_count": len(passed_events),
        "missing_field_events": missing_field_events,
        "empty_field_events": empty_field_events,
        "weak_trigger_rule_events": weak_trigger_rule_events,
        "source_ids_missing_events": source_ids_missing_events,
        "anti_trigger_weak_events": anti_trigger_weak_events,
        "variant_weak_events": variant_weak_events,
        "high_similarity_events": high_similarity_events,
        "not_allowed_top_events": sorted(not_allowed_top_events),
        "priority_fix_events": priority[:40],
    }


def _brief_list(items: list[Any], limit: int = 12) -> str:
    if not items:
        return "无"
    shown = items[:limit]
    text = json.dumps(shown, ensure_ascii=False, indent=2)
    if len(items) > limit:
        text += f"\n... 另有 {len(items) - limit} 项"
    return text


def format_quality_report(report: dict[str, Any]) -> str:
    """Format the quality report as user-readable Chinese text."""

    lines = [
        "# 事件证据链质量校验报告",
        "",
        f"基础校验结论：{'通过' if report.get('basic_passed') else '未通过'}",
        f"总事件数：{report.get('total_event_count', 0)}",
        f"证据链事件数：{report.get('chain_event_count', 0)}",
        f"完整通过数量：{report.get('passed_count', 0)}",
        "",
        "## 缺字段事件列表",
        _brief_list(report.get("missing_field_events", [])),
        "",
        "## 空字段事件列表",
        _brief_list(report.get("empty_field_events", [])),
        "",
        "## trigger_rules 过弱事件列表",
        _brief_list(report.get("weak_trigger_rule_events", [])),
        "",
        "## source_ids 缺失事件列表",
        _brief_list(report.get("source_ids_missing_events", [])),
        "",
        "## anti_triggers 需要补强事件列表",
        _brief_list(report.get("anti_trigger_weak_events", [])),
        "",
        "## variants 需要补强事件列表",
        _brief_list(report.get("variant_weak_events", [])),
        "",
        "## 相似度过高事件列表",
        _brief_list(report.get("high_similarity_events", [])),
        "",
        "## 不允许进入 Top 事件的事件列表",
        _brief_list(report.get("not_allowed_top_events", [])),
        "",
        "## 建议优先修复的事件列表",
        _brief_list(report.get("priority_fix_events", [])),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="校验流月事件证据链质量。")
    parser.add_argument("--root", default=str(ROOT), help="项目根目录，默认自动定位当前项目。")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告。")
    parser.add_argument("--output", help="额外写入报告文件。")
    args = parser.parse_args()

    report = validate_event_chain_quality(args.root)
    text = json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_quality_report(report)
    print(text)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")

    return 0 if report.get("basic_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
