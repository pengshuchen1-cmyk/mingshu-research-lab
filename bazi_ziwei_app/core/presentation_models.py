"""JSON-safe presentation models for public guidance and chart entry states."""

from __future__ import annotations

from datetime import date
import math
import re
from typing import Any

from core.bazi_term_glossary import BASE_TERM_IDS, GROUP_TERM_IDS
from core.popular_advice_engine import build_daily_advice, build_yearly_popular_advice
from core.ten_god_explanations import TEN_GOD_TERM_IDS


_PUBLIC_DIMENSION_KEYS = {
    "wealth",
    "relationship",
    "health",
    "career",
    "overall_balance",
}
_AUDIT_ONLY_KEYS = {
    "source_titles",
    "source_ids",
    "relationship_signature",
}
_PII_KEYS = {
    "name",
    "display_name",
    "birth_date",
    "birth_time",
    "birth_hour",
    "birth_minute",
    "birth_place",
    "birth_longitude",
    "longitude",
    "latitude",
    "sample_id",
    "user_id",
}
_PII_KEY_ALIASES = {
    "姓名",
    "出生日期",
    "出生时间",
    "出生时辰",
    "出生地点",
    "地点",
    "位置",
    "地址",
    "location",
    "address",
    "date_of_birth",
}
_PRIVATE_CONTAINER_KEYS = {"profile", "raw_chart"}
_TERM_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DATE_VALUE_PATTERN = re.compile(
    r"^(?P<year>\d{4})[-/.年](?P<month>\d{1,2})[-/.月](?P<day>\d{1,2})日?$"
)
_FIVE_ELEMENTS = ("木", "火", "土", "金", "水")
_STRUCTURAL_PUBLIC_FIELDS = {
    "kind",
    "day_master",
    "day_element",
    "strength",
    "dominant_elements",
    "pattern",
    "term_ids",
    "term_id",
    "label",
    "group",
    "accessibility_label",
    "count",
    "positions",
    "element_role",
    "favorable_relation",
    "favorable_elements",
    "unfavorable_elements",
    "distribution",
    "current_judgment",
    "current_pattern",
    "related_elements",
    "key",
    "score",
    "level",
    "detail_label",
}


def _string_list(value: Any) -> list[str]:
    """Return JSON-safe display text without carrying source object references."""
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if item is not None]


def _json_safe_copy(value: Any) -> Any:
    """Copy supported JSON values and remove non-finite numbers."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (list, tuple)):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_copy(item) for key, item in value.items()}
    return str(value)


def _normalize_key(key: Any) -> str:
    text = str(key).strip().replace("-", "_")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return text.lower()


def _is_audit_only_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return (
        normalized in _AUDIT_ONLY_KEYS
        or normalized.startswith("source_title")
        or normalized.startswith("source_id")
        or normalized.startswith("relationship_signature")
    )


def _is_pii_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return (
        normalized in _PII_KEYS
        or normalized in _PII_KEY_ALIASES
        or normalized.endswith("_name")
        or normalized.startswith("birth_")
        or normalized.endswith("_birth")
        or normalized.endswith("_place")
        or normalized.endswith("_location")
        or normalized.endswith("_address")
    )


def _is_forbidden_public_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return (
        _is_audit_only_key(normalized)
        or _is_pii_key(normalized)
        or normalized in _PRIVATE_CONTAINER_KEYS
    )


def _date_variants(text: str) -> set[str]:
    match = _DATE_VALUE_PATTERN.fullmatch(text.strip())
    if not match:
        return {text}
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return {text}
    return {
        text,
        f"{year:04d}-{month:02d}-{day:02d}",
        f"{year:04d}/{month:02d}/{day:02d}",
        f"{year:04d}.{month:02d}.{day:02d}",
        f"{year:04d}年{month:02d}月{day:02d}日",
        f"{year:04d}-{month}-{day}",
        f"{year:04d}/{month}/{day}",
        f"{year:04d}.{month}.{day}",
        f"{year:04d}年{month}月{day}日",
    }


def _collect_scalar_texts(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            result.update(_collect_scalar_texts(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            result.update(_collect_scalar_texts(item))
    elif value is not None:
        text = str(value).strip()
        if text:
            result.update(_date_variants(text))
    return result


def _collect_sensitive_values(value: Any) -> set[str]:
    """Collect raw profile values so copied display text can be scrubbed."""
    result: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if _is_pii_key(key):
                result.update(_collect_scalar_texts(item))
            else:
                result.update(_collect_sensitive_values(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            result.update(_collect_sensitive_values(item))
    return result


def _strict_text(value: Any, fallback: str = "") -> str:
    return value.strip() if isinstance(value, str) else fallback


def _strict_string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _project_personalized_term(personalized: dict) -> dict:
    """Project only documented personalized facts with strict shallow types."""
    projected: dict[str, Any] = {}
    count = personalized.get("count")
    if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
        projected["count"] = count
    for key in ("positions", "favorable_elements", "unfavorable_elements", "related_elements"):
        if key in personalized:
            projected[key] = _strict_string_list(personalized.get(key))
    for key in (
        "element_role",
        "favorable_relation",
        "interpretation",
        "day_master",
        "day_element",
        "current_judgment",
        "current_pattern",
    ):
        text = _strict_text(personalized.get(key))
        if text:
            projected[key] = text
    distribution = personalized.get("distribution")
    if isinstance(distribution, dict):
        safe_distribution: dict[str, float] = {}
        for element in _FIVE_ELEMENTS:
            number = _finite_number(distribution.get(element))
            if number is not None and number >= 0:
                safe_distribution[element] = number
        projected["distribution"] = safe_distribution
    return projected


def _scrub_sensitive_text(text: str, sensitive_values: set[str]) -> str:
    cleaned = text
    for value in sorted(sensitive_values, key=len, reverse=True):
        cleaned = cleaned.replace(value, "")
    return cleaned.strip(" ｜|，,；;：:。")


def _sanitize_public_payload(
    value: Any, sensitive_values: set[str], *, scrub_text: bool = True
) -> Any:
    """Recursively enforce the public-key denylist after whitelist projection."""
    if isinstance(value, dict):
        return {
            str(key): _sanitize_public_payload(
                item,
                sensitive_values,
                scrub_text=_normalize_key(key) not in _STRUCTURAL_PUBLIC_FIELDS,
            )
            for key, item in value.items()
            if not _is_forbidden_public_key(key)
        }
    if isinstance(value, list):
        return [
            _sanitize_public_payload(item, sensitive_values, scrub_text=scrub_text)
            for item in value
        ]
    if isinstance(value, str):
        return _scrub_sensitive_text(value, sensitive_values) if scrub_text else value
    return _json_safe_copy(value)


def _resolve_identity_term_ids(raw_term_ids: Any, chip_ids: list[str]) -> list[str]:
    """Map web identity aliases to canonical IDs present in the same payload."""
    available = set(chip_ids)
    resolved: list[str] = []
    strength_id = next(
        (
            term_id
            for term_id in chip_ids
            if term_id == "strength" or term_id.startswith("strength-")
        ),
        None,
    )
    for raw_id in _strict_string_list(raw_term_ids):
        canonical: str | None = raw_id if raw_id in available else None
        if canonical is None and (
            raw_id.startswith("day-element-") or raw_id.startswith("element-")
        ):
            canonical = "five-elements" if "five-elements" in available else None
        if canonical is None and raw_id == "strength":
            canonical = strength_id
        if canonical and canonical not in resolved:
            resolved.append(canonical)
    return resolved


def _safe_term_id(term_id: Any) -> str:
    normalized = str(term_id or "").strip()
    if not _TERM_ID_PATTERN.fullmatch(normalized):
        raise ValueError("术语编号必须是稳定的短横线英文键。")
    return normalized


def _term_group(term_id: str) -> str:
    if term_id in GROUP_TERM_IDS:
        return "ten_god_group"
    if term_id in set(TEN_GOD_TERM_IDS.values()):
        return "ten_god"
    if term_id in BASE_TERM_IDS or term_id == "strength":
        return "foundation"
    return "related"


def build_personal_identity_card_view(identity_card: dict) -> dict:
    """Project the web identity card into its name-free public DTO."""
    if not isinstance(identity_card, dict):
        raise ValueError("个人身份卡展示数据无效。")
    sensitive_values = _collect_sensitive_values(identity_card)
    projected = {
        "kind": "personal_identity_card",
        "day_master": _strict_text(identity_card.get("day_master")),
        "day_element": _strict_text(identity_card.get("day_element")),
        "strength": _strict_text(identity_card.get("strength")),
        "dominant_elements": _strict_string_list(identity_card.get("dominant_elements")),
        "pattern": _strict_text(identity_card.get("pattern")),
        "summary": _strict_text(identity_card.get("summary")),
        "term_ids": _strict_string_list(identity_card.get("term_ids")),
    }
    return _sanitize_public_payload(projected, sensitive_values)


def build_term_chip_view(term_view: dict) -> dict:
    """Build the stable, accessible public chip DTO from an internal term view."""
    if not isinstance(term_view, dict):
        raise ValueError("术语展示数据无效。")
    term_id = _safe_term_id(term_view.get("term_id"))
    label = _strict_text(term_view.get("label"), term_id)
    return {
        "kind": "term_chip",
        "term_id": term_id,
        "label": label,
        "group": _term_group(term_id),
        "accessibility_label": f"查看命理术语：{label}",
    }


def build_term_detail_view(term_view: dict) -> dict:
    """Whitelist a term definition and its optional personalized display facts."""
    if not isinstance(term_view, dict):
        raise ValueError("术语详情展示数据无效。")
    sensitive_values = _collect_sensitive_values(term_view)
    term_id = _safe_term_id(term_view.get("term_id"))
    projected = {
        "kind": "term_detail",
        "term_id": term_id,
        "label": _strict_text(term_view.get("label"), term_id),
        "definition": _strict_text(term_view.get("definition")),
        "observation_scope": _strict_text(term_view.get("observation_scope")),
        "boundary": _strict_text(term_view.get("boundary")),
    }
    personalized = term_view.get("personalized")
    if isinstance(personalized, dict):
        public_personalized = _project_personalized_term(personalized)
        if public_personalized:
            projected["personalized"] = public_personalized
    return _sanitize_public_payload(projected, sensitive_values)


def build_five_dimension_insight_view(dimension: dict) -> dict:
    """Build one full-text five-dimension DTO with a stable public key."""
    if not isinstance(dimension, dict):
        raise ValueError("五维展示数据无效。")
    key = str(dimension.get("key") or "").strip()
    if key not in _PUBLIC_DIMENSION_KEYS:
        raise ValueError("五维稳定键无效。")
    sensitive_values = _collect_sensitive_values(dimension)
    score_value = dimension.get("score", 0)
    try:
        raw_score = math.nan if isinstance(score_value, bool) else float(score_value)
    except (TypeError, ValueError, OverflowError):
        raw_score = math.nan
    score = max(0, min(100, int(round(raw_score)))) if math.isfinite(raw_score) else 0
    projected = {
        "kind": "five_dimension_insight",
        "key": key,
        "label": _strict_text(dimension.get("label")),
        "score": score,
        "level": _strict_text(dimension.get("level")),
        "summary": _strict_text(dimension.get("summary")),
        "detail_label": _strict_text(dimension.get("detail_label"), "证据"),
        "evidence": _strict_string_list(dimension.get("evidence")),
        "strengths": _strict_string_list(dimension.get("strengths")),
        "risks": _strict_string_list(dimension.get("risks")),
        "advice": _strict_string_list(dimension.get("advice")),
    }
    return _sanitize_public_payload(projected, sensitive_values)


def build_chart_public_view(
    identity_card: dict,
    term_views: list[dict],
    dimension_views: list[dict],
) -> dict:
    """Return the complete Mini Program chart view without audit data or raw PII."""
    sources: list[Any] = [identity_card, term_views, dimension_views]
    sensitive_values: set[str] = set()
    for source in sources:
        sensitive_values.update(_collect_sensitive_values(source))
    term_chips = [build_term_chip_view(term) for term in term_views]
    identity_view = build_personal_identity_card_view(identity_card)
    identity_view["term_ids"] = _resolve_identity_term_ids(
        identity_card.get("term_ids"),
        [str(chip["term_id"]) for chip in term_chips],
    )
    public = {
        "kind": "chart_public_view",
        "identity_card": identity_view,
        "term_chips": term_chips,
        "term_details": [build_term_detail_view(term) for term in term_views],
        "five_dimensions": [
            build_five_dimension_insight_view(dimension) for dimension in dimension_views
        ],
    }
    return _sanitize_public_payload(public, sensitive_values)


def build_term_disclosure_semantics(
    term_id: str, active_term_id: str | None, *, label: str
) -> dict:
    """Provide stable DOM relationships for web and Mini Program adapters."""
    safe_id = _safe_term_id(term_id)
    return {
        "button_id": f"term-chip-{safe_id}",
        "controls_id": f"term-detail-{safe_id}",
        "aria_expanded": "true" if active_term_id == safe_id else "false",
        "accessibility_label": f"查看命理术语：{label}",
    }


def transition_term_disclosure(
    active_term_id: str | None, requested_term_id: str
) -> dict:
    """Toggle one term and name the trigger that must regain focus on close."""
    requested = _safe_term_id(requested_term_id)
    if active_term_id == requested:
        return {
            "active_term_id": None,
            "restore_focus_to": f"term-chip-{requested}",
        }
    return {"active_term_id": requested, "restore_focus_to": None}


def build_daily_guidance_view(
    target_date: date | None = None, *, advice: dict | None = None
) -> dict:
    """Build the public, non-personal daily guidance contract."""
    daily = advice if advice is not None else build_daily_advice(target_date)
    actions = _string_list(daily.get("suitable_actions"))
    reminders = _string_list(daily.get("actions_to_avoid"))
    colors = _string_list(daily.get("lucky_colors"))
    element_theme = str(daily["element_theme"])
    wearing_advice = str(daily["wearing_advice"])
    primary_action = actions[0] if actions else "整理当下重点"
    return {
        "kind": "daily_guidance",
        "is_personal": False,
        "date": str(daily["date"]),
        "day_pillar": str(daily["day_pillar"]),
        "title": str(daily["title"]),
        "element_theme": element_theme,
        "wearing_colors": colors,
        "wearing_advice": wearing_advice,
        "cautions": reminders,
        "primary_action": primary_action,
        "theme": element_theme,
        "focus": primary_action,
        "action": wearing_advice,
        "reminder": reminders[0] if reminders else "避免过度消耗",
        "details": {
            "colors": list(colors),
            "relaxation": str(daily.get("relaxation_advice", "")),
            "actions": actions,
        },
        "basis": str(daily["basis"]),
        "boundary_note": str(daily["boundary_note"]),
    }


def build_yearly_guidance_view(
    target_year: int | None = None, *, advice: dict | None = None
) -> dict:
    """Build the public, non-personal yearly guidance contract."""
    yearly = advice if advice is not None else build_yearly_popular_advice(target_year)
    required_fields = (
        "year",
        "title",
        "annual_tone",
        "keywords",
        "action_advice",
        "basis",
        "boundary_note",
    )
    if not isinstance(yearly, dict) or any(field not in yearly for field in required_fields):
        raise ValueError("年度大众建议数据不完整，无法生成公开年度指引。")

    actions = _string_list(yearly.get("action_advice"))
    keywords = _string_list(yearly.get("keywords"))
    return {
        "kind": "yearly_guidance",
        "is_personal": False,
        "year": int(yearly["year"]),
        "title": str(yearly["title"]),
        "theme": str(yearly["annual_tone"]),
        "focus": keywords[0] if keywords else "整理年度重点",
        "actions": actions,
        "basis": str(yearly["basis"]),
        "boundary_note": str(yearly["boundary_note"]),
    }


def _has_usable_chart(chart: dict | None) -> bool:
    """Return whether a chart has the minimum safe data for personal entry."""
    return (
        isinstance(chart, dict)
        and not chart.get("error")
        and isinstance(chart.get("day_master"), str)
        and bool(chart["day_master"].strip())
    )


def build_chart_summary_view(chart: dict | None) -> dict:
    """Expose a minimal chart state without returning profile or birth data."""
    if not _has_usable_chart(chart):
        return {"kind": "chart_summary", "ready": False, "summary": "尚未建立个人命盘。"}

    strength = chart.get("day_master_strength")
    favorable_elements = (
        _string_list(strength.get("favorable_elements"))
        if isinstance(strength, dict)
        else []
    )
    summary = f"日主为{chart['day_master']}。"
    if favorable_elements:
        summary += f"可优先关注{'、'.join(favorable_elements)}相关的平衡与安排。"
    else:
        summary += "建议进入个人命盘查看完整解读。"
    return {
        "kind": "chart_summary",
        "ready": True,
        "summary": summary,
        "day_master": str(chart.get("day_master", "")),
        "favorable_elements": favorable_elements,
        "next_action": "今日/年度建议",
    }


def build_profile_status(profile: dict | None, chart: dict | None) -> dict:
    """Return only local profile/chart availability and the next named route."""
    has_profile = bool(profile)
    has_chart = _has_usable_chart(chart)
    return {
        "kind": "profile_status",
        "has_profile": has_profile,
        "has_chart": has_chart,
        "next_action": "个人命盘" if has_chart else "新建命盘",
    }
