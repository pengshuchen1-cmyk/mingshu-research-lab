"""八字主盘生成。"""

from __future__ import annotations

from datetime import date

from core.bazi_calendar_adapter import BirthInput, normalize_birth_input
from core.bazi_constants import (
    BRANCH_HIDDEN_STEMS,
    BRANCH_MAIN_ELEMENTS,
    NAYIN_ELEMENT,
    STEM_ELEMENTS,
)
from core.bazi_rulebook import load_rulebook
from core.chart_facts import attach_chart_facts
from core.five_elements import calculate_five_elements
from core.four_pillars_engine import calculate_four_pillars
from core.pattern_engine import analyze_pattern
from core.seasonal_adjustment import analyze_seasonal_adjustment
from core.strength_engine import analyze_day_master_strength
from core.ten_gods import count_ten_gods, get_hidden_stem_ten_gods, get_ten_god
from core.relationship_analysis import analyze_relationship
from core.wealth_analysis import analyze_wealth


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    """解析出生日期。"""
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def _normalize_calendar_profile(profile: dict) -> dict:
    """把农历输入统一换算成公历 birth_date，保留原始农历日期。"""
    normalized = dict(profile)
    calendar_type = "lunar" if normalized.get("calendar_type") == "lunar" else "solar"
    source_date = normalized.get("lunar_birth_date") or normalized.get("birth_date")
    year, month, day = _parse_birth_date(source_date)
    birth = BirthInput(
        calendar=calendar_type,
        year=year,
        month=month,
        day=day,
        hour=_profile_time_value(normalized, "birth_hour", 0),
        minute=_profile_time_value(normalized, "birth_minute", 0),
        gender=_normalize_gender(normalized.get("gender")),
        is_leap_month=bool(normalized.get("is_leap_month", False)),
    )
    evidence = normalize_birth_input(birth)
    normalized["calendar_type"] = calendar_type
    if calendar_type == "lunar":
        normalized["lunar_birth_date"] = f"{year:04d}-{month:02d}-{day:02d}"
    normalized["birth_date"] = evidence.converted_solar_date.isoformat()
    normalized["calendar_conversion"] = {
        "from": calendar_type,
        "source_date": f"{year:04d}-{month:02d}-{day:02d}",
        "solar_birth_date": normalized["birth_date"],
        "is_leap_month": birth.is_leap_month,
    }
    normalized["time_mode"] = "china_standard"
    return normalized


def _normalize_gender(value: object) -> str:
    return "female" if str(value).strip().lower() in {"女", "female", "f"} else "male"


def _profile_time_value(profile: dict, key: str, default: int) -> int | None:
    if key in profile and profile[key] is None:
        return None
    return int(profile.get(key, default))


def _birth_input_from_profile(profile: dict) -> BirthInput:
    calendar_type = "lunar" if profile.get("calendar_type") == "lunar" else "solar"
    source_date = profile.get("lunar_birth_date") if calendar_type == "lunar" else None
    year, month, day = _parse_birth_date(source_date or profile.get("birth_date"))
    return BirthInput(
        calendar=calendar_type,
        year=year,
        month=month,
        day=day,
        hour=_profile_time_value(profile, "birth_hour", 0),
        minute=_profile_time_value(profile, "birth_minute", 0),
        gender=_normalize_gender(profile.get("gender")),
        is_leap_month=bool(profile.get("is_leap_month", False)),
    )


def ensure_bazi_analysis_fields(chart: dict) -> dict:
    """为旧 session / 旧档案命盘补齐新分析字段。

    v1.0.4.8 之前生成的 chart 没有格局判定和调候表字段。页面渲染时调用
    这个函数，可避免用户必须重新录入命盘才能看到新增核心能力。
    """
    if not isinstance(chart, dict) or chart.get("error"):
        return chart
    if "seasonal_adjustment" not in chart:
        try:
            chart["seasonal_adjustment"] = analyze_seasonal_adjustment(chart)
        except Exception as exc:
            chart["seasonal_adjustment"] = {
                "plain_text": f"调候解释暂不可用：{exc}",
                "primary_useful_stems": [],
                "supporting_stems": [],
            }
    if "pattern_analysis" not in chart:
        try:
            chart["pattern_analysis"] = analyze_pattern(chart)
        except Exception as exc:
            chart["pattern_analysis"] = {
                "pattern": "格局暂无法判断",
                "plain_text": f"格局判定暂不可用：{exc}",
                "evidence": [],
            }
    strength = chart.get("day_master_strength", {})
    if isinstance(strength, dict) and "season_adjustment" not in strength:
        strength["season_adjustment"] = chart.get("seasonal_adjustment", {})
    return chart


def build_bazi_chart(profile: dict) -> dict:
    """
    输入用户出生信息，生成完整八字基础盘。
    """
    try:
        source_profile = dict(profile)
        birth = _birth_input_from_profile(source_profile)
        result = calculate_four_pillars(birth)
        profile = _normalize_calendar_profile(source_profile)
        year, month, day = _parse_birth_date(profile.get("birth_date"))
        hour = birth.hour
        minute = birth.minute

        pillar_values = {
            "year": ("年柱", result.year),
            "month": ("月柱", result.month),
            "day": ("日柱", result.day),
            "hour": ("时柱", result.hour),
        }
        pillars = {}
        for key, (name, pillar) in pillar_values.items():
            gan = pillar.gan if pillar is not None else ""
            zhi = pillar.zhi if pillar is not None else ""
            text = pillar.text if pillar is not None else ""
            elements = f"{STEM_ELEMENTS.get(gan, '')}{BRANCH_MAIN_ELEMENTS.get(zhi, '')}"
            pillars[key] = {
                "name": name,
                "gan": gan,
                "zhi": zhi,
                "pillar": text,
                "na_yin": NAYIN_ELEMENT.get(text, ""),
                "xun_kong": "",
                "di_shi": "",
                "wu_xing": elements,
            }
        day_master = result.day.gan
        hidden_stems = {}
        ten_gods = {}

        for key, pillar in pillars.items():
            hidden_stems[key] = [
                {
                    "gan": gan,
                    "element": STEM_ELEMENTS.get(gan, "未知"),
                    "ten_god": get_ten_god(day_master, gan),
                }
                for gan in BRANCH_HIDDEN_STEMS.get(pillar["zhi"], [])
            ]
            ten_gods[key] = {
                "gan": get_ten_god(day_master, pillar["gan"]),
                "hidden_stems": get_hidden_stem_ten_gods(day_master, pillar["zhi"]),
            }

        display_time = (
            f"{hour:02d}:{minute:02d}" if hour is not None and minute is not None else "时辰不详"
        )
        birth_datetime = f"{year:04d}-{month:02d}-{day:02d} {display_time}"
        pillar_evidence = {
            "year_basis": result.evidence.year_basis,
            "month_basis": result.evidence.month_basis,
            "day_basis": result.evidence.day_basis,
            "hour_basis": result.evidence.hour_basis,
            "rule_ids": list(result.evidence.rule_ids),
            "public_text": result.evidence.public_text(),
        }
        chart = {
            "profile": profile,
            "time_mode": "china_standard",
            "time_mode_label": result.calendar.time_mode_label,
            "use_true_solar_time": False,
            "birth_longitude": None,
            "timezone_offset": 8.0,
            "original_birth_datetime": birth_datetime,
            "adjusted_birth_datetime": birth_datetime,
            "true_solar_time_applied": False,
            "true_solar_time_warning": "",
            "zi_time_boundary_note": result.evidence.day_basis if hour == 23 else "",
            "solar": birth_datetime,
            "lunar_text": result.calendar.lunar_text,
            "pillars": pillars,
            "pillar_evidence": pillar_evidence,
            "calendar_evidence": {
                "source_calendar": result.calendar.source_calendar,
                "source_date": result.calendar.original_date.isoformat(),
                "solar_date": result.calendar.converted_solar_date.isoformat(),
                "is_leap_month": result.calendar.is_leap_month,
                "time_mode": "china_standard",
            },
            "rule_version": load_rulebook().version,
            "day_master": day_master,
            "hidden_stems": hidden_stems,
            "ten_gods": ten_gods,
            "ming_gong": "",
            "shen_gong": "",
            "tai_yuan": "",
            "tai_xi": "",
        }
        chart["five_elements"] = calculate_five_elements(chart)
        chart["ten_god_counts"] = count_ten_gods(chart)
        try:
            chart["day_master_strength"] = analyze_day_master_strength(chart)
        except Exception as exc:
            chart["day_master_strength"] = {
                "strength": "暂无法判断",
                "message": f"日主强弱分析暂不可用：{exc}",
            }
        ensure_bazi_analysis_fields(chart)
        chart["wealth_analysis"] = analyze_wealth(chart).to_dict()
        chart["relationship_analysis"] = analyze_relationship(chart).to_dict()
        attach_chart_facts(chart)
        return chart
    except Exception as exc:
        return {"profile": profile, "error": f"生成八字命盘失败：{exc}"}
