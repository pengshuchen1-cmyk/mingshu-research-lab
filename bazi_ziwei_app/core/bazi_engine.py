"""八字主盘生成。"""

from __future__ import annotations

from datetime import date

from core.bazi_constants import BRANCH_HIDDEN_STEMS, STEM_ELEMENTS
from core.calendar_engine import get_lunar_eight_char, get_zi_time_boundary_note
from core.five_elements import calculate_five_elements
from core.pattern_engine import analyze_pattern
from core.seasonal_adjustment import analyze_seasonal_adjustment
from core.strength_engine import analyze_day_master_strength
from core.ten_gods import count_ten_gods, get_hidden_stem_ten_gods, get_ten_god


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    """解析出生日期。"""
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def _normalize_calendar_profile(profile: dict) -> dict:
    """把农历输入统一换算成公历 birth_date，保留原始农历日期。"""
    normalized = dict(profile)
    if normalized.get("calendar_type") != "lunar":
        normalized.setdefault("calendar_type", "solar")
        return normalized

    lunar_birth_date = normalized.get("lunar_birth_date") or normalized.get("birth_date")
    year, month, day = _parse_birth_date(lunar_birth_date)
    hour = int(normalized.get("birth_hour", 0))
    minute = int(normalized.get("birth_minute", 0))

    from lunar_python import Lunar

    lunar = Lunar.fromYmdHms(year, month, day, hour, minute, 0)
    solar = lunar.getSolar()
    normalized["lunar_birth_date"] = f"{year:04d}-{month:02d}-{day:02d}"
    normalized["birth_date"] = solar.toYmd()
    normalized["calendar_conversion"] = {
        "from": "lunar",
        "lunar_birth_date": normalized["lunar_birth_date"],
        "solar_birth_date": normalized["birth_date"],
    }
    return normalized


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
        profile = _normalize_calendar_profile(profile)
        year, month, day = _parse_birth_date(profile.get("birth_date"))
        hour = int(profile.get("birth_hour", 0))
        minute = int(profile.get("birth_minute", 0))
        use_true_solar_time = profile.get("use_true_solar_time", False) or profile.get("use_solar_time", False)
        raw_longitude = profile.get("birth_longitude") or profile.get("longitude")
        if use_true_solar_time and raw_longitude is not None:
            longitude = float(raw_longitude)
            time_mode = "true_solar_time"
            tsp_warning = ""
        else:
            longitude = 120.0
            time_mode = "standard_time"
            tsp_warning = ""
        if use_true_solar_time and raw_longitude is None:
            tsp_warning = "缺少出生地经度，已使用标准时间排盘"
        lunar_info = get_lunar_eight_char(year, month, day, hour, minute, longitude=longitude)
        if lunar_info.get("error"):
            return {"profile": profile, "error": lunar_info["error"]}

        pillars = {
            "year": {
                "name": "年柱",
                "gan": lunar_info["year_gan"],
                "zhi": lunar_info["year_zhi"],
                "pillar": lunar_info["year_pillar"],
            },
            "month": {
                "name": "月柱",
                "gan": lunar_info["month_gan"],
                "zhi": lunar_info["month_zhi"],
                "pillar": lunar_info["month_pillar"],
            },
            "day": {
                "name": "日柱",
                "gan": lunar_info["day_gan"],
                "zhi": lunar_info["day_zhi"],
                "pillar": lunar_info["day_pillar"],
            },
            "hour": {
                "name": "时柱",
                "gan": lunar_info["hour_gan"],
                "zhi": lunar_info["hour_zhi"],
                "pillar": lunar_info["hour_pillar"],
                "na_yin": lunar_info.get("time_na_yin", ""),
                "xun_kong": lunar_info.get("time_xun_kong", ""),
                "di_shi": lunar_info.get("time_di_shi", ""),
                "wu_xing": lunar_info.get("time_wu_xing", ""),
            },
        }
        for key, info in [("year", "year_"), ("month", "month_"), ("day", "day_")]:
            pillars[key]["na_yin"] = lunar_info.get(info + "na_yin", "")
            pillars[key]["xun_kong"] = lunar_info.get(info + "xun_kong", "")
            pillars[key]["di_shi"] = lunar_info.get(info + "di_shi", "")
            pillars[key]["wu_xing"] = lunar_info.get(info + "wu_xing", "")
        day_master = lunar_info["day_master"]
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

        time_mode = lunar_info.get("time_mode", "standard_time")
        chart = {
            "profile": profile,
            "time_mode": time_mode,
            "use_true_solar_time": use_true_solar_time,
            "birth_longitude": raw_longitude if use_true_solar_time else None,
            "timezone_offset": 8.0,
            "original_birth_datetime": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            "adjusted_birth_datetime": f"{year:04d}-{month:02d}-{day:02d} {lunar_info.get('adjusted_birth_hour', hour):02d}:{lunar_info.get('adjusted_birth_minute', minute):02d}",
            "true_solar_time_applied": lunar_info.get("true_solar_time_applied", False),
            "true_solar_time_warning": tsp_warning,
            "zi_time_boundary_note": lunar_info.get("zi_time_boundary_note") or get_zi_time_boundary_note(hour, minute),
            "solar": lunar_info["solar"],
            "lunar_text": lunar_info["lunar_text"],
            "pillars": pillars,
            "day_master": day_master,
            "hidden_stems": hidden_stems,
            "ten_gods": ten_gods,
            "ming_gong": lunar_info.get("ming_gong", ""),
            "shen_gong": lunar_info.get("shen_gong", ""),
            "tai_yuan": lunar_info.get("tai_yuan", ""),
            "tai_xi": lunar_info.get("tai_xi", ""),
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
        return chart
    except Exception as exc:
        return {"profile": profile, "error": f"生成八字命盘失败：{exc}"}
