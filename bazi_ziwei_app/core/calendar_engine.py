"""公历转八字基础排盘。"""

from __future__ import annotations

from datetime import datetime


def _ensure_float(value, field_name: str = "longitude", default: float = 120.0) -> float:
    """Safely convert to float, fallback to default on failure."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except (ValueError, TypeError):
            pass
    return default


def _call_first(obj: object, method_names: list[str]) -> str | None:
    """尝试调用第一个可用方法。"""
    for name in method_names:
        method = getattr(obj, name, None)
        if callable(method):
            value = method()
            if value is not None:
                return str(value)
    return None


def _build_solar(year: int, month: int, day: int, hour: int, minute: int):
    """兼容不同 lunar_python 版本创建 Solar 对象。"""
    from lunar_python import Solar

    try:
        return Solar(year, month, day, hour, minute, 0)
    except TypeError:
        return Solar.fromYmdHms(year, month, day, hour, minute, 0)


def _split_pillar(pillar: str) -> tuple[str, str]:
    """从干支字符串中拆分天干和地支。"""
    if len(pillar) >= 2:
        return pillar[0], pillar[1]
    return "", ""


def _solar_time_correction(hour: int, minute: int, longitude: float = 120.0) -> tuple[int, int]:
    """根据出生地经度对钟表时间做真太阳时校正（经度时差部分）。

    北京时间基准为东经 120°E，每差 1° 约差 4 分钟。

    Args:
        hour: 出生钟表时（24 小时制）
        minute: 出生钟表分
        longitude: 出生地经度，东经为正。默认 120.0（北京时间基准）

    Returns:
        (校正后小时, 校正后分钟)
    """
    offset = int(round((longitude - 120.0) * 4))
    total = hour * 60 + minute + offset
    return (total // 60) % 24, total % 60




def get_zi_time_boundary_note(hour: int, minute: int = 0) -> str:
    """返回早晚子时边界提示。

    这里只做用户可见提醒，不改变既有排盘规则。23:00-00:59 属于子时，
    传统流派对 23:00 后是否换日有不同处理，靠近这个区间时适合复核。
    """
    try:
        total = int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return ""
    if total >= 23 * 60 or total < 60:
        return (
            "出生时间处在子时边界。传统命理中早晚子时、23:00 后是否换日存在不同流派，"
            "如果现实反馈与命盘差异较大，建议把子时换日作为复核点。"
        )
    return ""

def get_lunar_eight_char(year: int, month: int, day: int, hour: int, minute: int = 0, longitude: float = 120.0, **extra) -> dict:
    """
    使用 lunar_python 根据公历生日生成八字四柱。

    longitude 参数用于真太阳时校正，默认 120°E（北京时间）。
    **extra 用于安全吸收未命名参数（如 gender 字符串误传入）。
    """
    try:
        safe_longitude = _ensure_float(longitude, default=120.0)
        adjusted_hour, adjusted_minute = _solar_time_correction(hour, minute, safe_longitude)
        datetime(year, month, day, hour, minute)
        orig_hour, orig_minute = hour, minute
        hour, minute = orig_hour, orig_minute
        solar = _build_solar(year, month, day, adjusted_hour, adjusted_minute)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        year_pillar = _call_first(eight_char, ["getYear", "getYearInGanZhi"]) or ""
        month_pillar = _call_first(eight_char, ["getMonth", "getMonthInGanZhi"]) or ""
        day_pillar = _call_first(eight_char, ["getDay", "getDayInGanZhi"]) or ""
        hour_pillar = _call_first(eight_char, ["getTime", "getHour", "getTimeInGanZhi"]) or ""

        if not year_pillar or not month_pillar:
            raise ValueError(f"八字排盘异常：年柱({year_pillar!r})或月柱({month_pillar!r})为空")

        year_gan = _call_first(eight_char, ["getYearGan"]) or _split_pillar(year_pillar)[0]
        year_zhi = _call_first(eight_char, ["getYearZhi"]) or _split_pillar(year_pillar)[1]
        month_gan = _call_first(eight_char, ["getMonthGan"]) or _split_pillar(month_pillar)[0]
        month_zhi = _call_first(eight_char, ["getMonthZhi"]) or _split_pillar(month_pillar)[1]
        day_gan = _call_first(eight_char, ["getDayGan"]) or _split_pillar(day_pillar)[0]
        day_zhi = _call_first(eight_char, ["getDayZhi"]) or _split_pillar(day_pillar)[1]
        hour_gan = _call_first(eight_char, ["getTimeGan", "getHourGan"]) or _split_pillar(hour_pillar)[0]
        hour_zhi = _call_first(eight_char, ["getTimeZhi", "getHourZhi"]) or _split_pillar(hour_pillar)[1]

        lunar_text = _call_first(lunar, ["toFullString", "toString"]) or str(lunar)
        solar_text = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"

        # 新字段：纳音、空亡、十二长生、五行
        year_na_yin = _call_first(eight_char, ["getYearNaYin"]) or ""
        month_na_yin = _call_first(eight_char, ["getMonthNaYin"]) or ""
        day_na_yin = _call_first(eight_char, ["getDayNaYin"]) or ""
        time_na_yin = _call_first(eight_char, ["getTimeNaYin"]) or ""

        year_xun_kong = _call_first(eight_char, ["getYearXunKong"]) or ""
        month_xun_kong = _call_first(eight_char, ["getMonthXunKong"]) or ""
        day_xun_kong = _call_first(eight_char, ["getDayXunKong"]) or ""
        time_xun_kong = _call_first(eight_char, ["getTimeXunKong"]) or ""

        year_di_shi = _call_first(eight_char, ["getYearDiShi"]) or ""
        month_di_shi = _call_first(eight_char, ["getMonthDiShi"]) or ""
        day_di_shi = _call_first(eight_char, ["getDayDiShi"]) or ""
        time_di_shi = _call_first(eight_char, ["getTimeDiShi"]) or ""

        year_wu_xing = _call_first(eight_char, ["getYearWuXing"]) or ""
        month_wu_xing = _call_first(eight_char, ["getMonthWuXing"]) or ""
        day_wu_xing = _call_first(eight_char, ["getDayWuXing"]) or ""
        time_wu_xing = _call_first(eight_char, ["getTimeWuXing"]) or ""

        # 全局数据：命宫、身宫、胎元、胎息
        ming_gong = _call_first(eight_char, ["getMingGong"]) or ""
        shen_gong = _call_first(eight_char, ["getShenGong"]) or ""
        tai_yuan = _call_first(eight_char, ["getTaiYuan"]) or ""
        tai_xi = _call_first(eight_char, ["getTaiXi"]) or ""

        return {
            "time_mode": "standard_time" if safe_longitude == 120.0 else "true_solar_time",
            "original_longitude": safe_longitude,
            "true_solar_time_applied": safe_longitude != 120.0,
            "original_birth_hour": orig_hour,
            "original_birth_minute": orig_minute,
            "adjusted_birth_hour": adjusted_hour,
            "adjusted_birth_minute": adjusted_minute,
            "zi_time_boundary_note": get_zi_time_boundary_note(adjusted_hour, adjusted_minute),
            "solar": solar_text,
            "lunar_text": lunar_text,
            "year_pillar": year_pillar,
            "month_pillar": month_pillar,
            "day_pillar": day_pillar,
            "hour_pillar": hour_pillar,
            "year_gan": year_gan,
            "year_zhi": year_zhi,
            "month_gan": month_gan,
            "month_zhi": month_zhi,
            "day_gan": day_gan,
            "day_zhi": day_zhi,
            "hour_gan": hour_gan,
            "hour_zhi": hour_zhi,
            "day_master": day_gan,
            # 纳音
            "year_na_yin": year_na_yin,
            "month_na_yin": month_na_yin,
            "day_na_yin": day_na_yin,
            "time_na_yin": time_na_yin,
            # 空亡
            "year_xun_kong": year_xun_kong,
            "month_xun_kong": month_xun_kong,
            "day_xun_kong": day_xun_kong,
            "time_xun_kong": time_xun_kong,
            # 十二长生
            "year_di_shi": year_di_shi,
            "month_di_shi": month_di_shi,
            "day_di_shi": day_di_shi,
            "time_di_shi": time_di_shi,
            # 五行
            "year_wu_xing": year_wu_xing,
            "month_wu_xing": month_wu_xing,
            "day_wu_xing": day_wu_xing,
            "time_wu_xing": time_wu_xing,
            # 全局
            "ming_gong": ming_gong,
            "shen_gong": shen_gong,
            "tai_yuan": tai_yuan,
            "tai_xi": tai_xi,
        }
    except ModuleNotFoundError as exc:
        if exc.name == "lunar_python":
            return {"error": "缺少 lunar_python，请先运行：python -m pip install -r requirements.txt"}
        return {"error": f"日期不合法或排盘失败：{exc}"}
    except Exception as exc:
        return {"error": f"日期不合法或排盘失败：{exc}"}
