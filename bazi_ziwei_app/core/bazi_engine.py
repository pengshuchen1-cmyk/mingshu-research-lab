"""八字主盘生成。"""

from __future__ import annotations

from datetime import date

from core.bazi_constants import BRANCH_HIDDEN_STEMS, STEM_ELEMENTS
from core.calendar_engine import get_lunar_eight_char
from core.five_elements import calculate_five_elements
from core.strength_engine import analyze_day_master_strength
from core.ten_gods import count_ten_gods, get_hidden_stem_ten_gods, get_ten_god


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    """解析出生日期。"""
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def build_bazi_chart(profile: dict) -> dict:
    """
    输入用户出生信息，生成完整八字基础盘。
    """
    try:
        year, month, day = _parse_birth_date(profile.get("birth_date"))
        hour = int(profile.get("birth_hour", 0))
        minute = int(profile.get("birth_minute", 0))
        lunar_info = get_lunar_eight_char(year, month, day, hour, minute)
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

        chart = {
            "profile": profile,
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
        return chart
    except Exception as exc:
        return {"profile": profile, "error": f"生成八字命盘失败：{exc}"}
