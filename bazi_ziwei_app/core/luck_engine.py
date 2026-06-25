"""大运流年分析接口。"""

from __future__ import annotations

from datetime import date, datetime

from core.bazi_constants import BRANCH_MAIN_ELEMENTS, STEM_ELEMENTS
from core.stage_engine import analyze_luck_stage
from core.ten_gods import get_ten_god
from core.yearly_engine import analyze_yearly_fortune


def _parse_birth_date(value: object) -> tuple[int, int, int]:
    """解析出生日期。"""
    if isinstance(value, date):
        return value.year, value.month, value.day
    year, month, day = str(value).split("-")
    return int(year), int(month), int(day)


def _call_first(obj: object, method_names: list[str]) -> object | None:
    """调用第一个可用方法。"""
    for name in method_names:
        method = getattr(obj, name, None)
        if callable(method):
            return method()
    return None


def _build_solar(year: int, month: int, day: int, hour: int, minute: int):
    """兼容不同 lunar_python 版本创建 Solar 对象。"""
    from lunar_python import Solar

    try:
        return Solar(year, month, day, hour, minute, 0)
    except TypeError:
        return Solar.fromYmdHms(year, month, day, hour, minute, 0)


def _get_yun(eight_char: object, gender_code: int) -> object:
    """兼容不同 lunar_python 版本获取大运对象。"""
    try:
        return eight_char.getYun(gender_code)
    except TypeError:
        return eight_char.getYun(gender_code, 1)


def _split_pillar(pillar: str) -> tuple[str, str]:
    """拆分干支。"""
    if len(pillar) >= 2:
        return pillar[0], pillar[1]
    return "", ""


def _safe_int(value: object, default: int = 0) -> int:
    """安全转整数。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _start_text(start_age: int, start_year: int, start_month: object = "") -> str:
    """生成起运说明文字。"""
    if start_age or start_year:
        month_text = f"，约{start_month}个月" if start_month not in ("", None) else ""
        return (
            f"约 {max(0, start_age)} 岁左右起运{month_text}，起运年份约为 {start_year} 年。"
            "起运时间为传统命理推算结果，具体起运点可在后续版本结合节气进一步校正。"
        )
    return "起运时间为传统命理推算结果，具体起运点可在后续版本结合节气进一步校正。"


def _normalize_age_range(raw_start_age: int, raw_end_age: int, reference_start_age: int = 0, index: int = 0) -> tuple[int, int]:
    """修正大运年龄区间，避免出现负数或倒挂。"""
    if raw_start_age < 0:
        start_age = max(0, reference_start_age, raw_end_age - 9)
    elif reference_start_age > 0 and raw_start_age < reference_start_age and index == 0:
        start_age = reference_start_age
    else:
        start_age = max(0, raw_start_age)

    if raw_end_age < start_age:
        end_age = start_age + 9
    else:
        end_age = raw_end_age
    return start_age, end_age


def _pillar_year(year: int) -> str:
    """使用 lunar_python 获取流年干支。"""
    solar = _build_solar(year, 2, 4, 12, 0)
    eight_char = solar.getLunar().getEightChar()
    value = _call_first(eight_char, ["getYear", "getYearInGanZhi"])
    if value:
        return str(value)
    gan = _call_first(eight_char, ["getYearGan"]) or ""
    zhi = _call_first(eight_char, ["getYearZhi"]) or ""
    return f"{gan}{zhi}"


def _relation_to_favorable(element_pair: list[str], favorable: set[str], unfavorable: set[str]) -> str:
    """判断流年五行与喜忌关系。"""
    elements = set(element_pair)
    if elements & favorable:
        return "喜用相关"
    if elements & unfavorable:
        return "忌神相关"
    return "平稳观察"


def _year_brief_text(pillar: str, elements: list[str], relation: str) -> str:
    """生成年度简短提示。"""
    element_text = "、".join([item for item in elements if item]) or "五行"
    if relation == "喜用相关":
        return f"{pillar} 年{element_text}气较明显，若相关五行为喜用，较适合顺势推进学习、事业和资源积累。"
    if relation == "忌神相关":
        return f"{pillar} 年{element_text}气较明显，若相关五行为忌，需要注意节奏、压力和资源消耗。"
    return f"{pillar} 年整体宜平稳观察，适合稳步积累，不宜简单判断好坏。"


def _build_yearly_list(chart: dict, years: int = 10) -> list[dict]:
    """生成未来若干年流年列表。"""
    day_master = chart.get("day_master", "")
    strength = chart.get("day_master_strength", {})
    favorable = set(strength.get("favorable_elements", []))
    unfavorable = set(strength.get("unfavorable_elements", []))
    current_year = datetime.now().year
    items = []
    for year in range(current_year, current_year + years):
        try:
            items.append(analyze_yearly_fortune(chart, year))
        except Exception:
            continue
    return items


def get_luck_cycles(profile: dict, chart: dict | None = None) -> dict:
    """
    返回大运基础信息。
    """
    try:
        chart = chart or {}
        year, month, day = _parse_birth_date(profile.get("birth_date"))
        hour = int(profile.get("birth_hour", 0))
        minute = int(profile.get("birth_minute", 0))
        gender_code = 1 if profile.get("gender") == "男" else 0
        solar = _build_solar(year, month, day, hour, minute)
        eight_char = solar.getLunar().getEightChar()
        yun = _get_yun(eight_char, gender_code)
        da_yun_list = _call_first(yun, ["getDaYun"]) or []
        start_year = _safe_int(_call_first(yun, ["getStartYear"]))
        start_month = _call_first(yun, ["getStartMonth"]) or ""
        start_age = 0

        dayun_list = []
        for item in da_yun_list:
            pillar = str(_call_first(item, ["getGanZhi"]) or "")
            if not pillar:
                if not start_age:
                    start_age = _safe_int(_call_first(item, ["getEndAge"]), 0) + 1
                continue
            gan, zhi = _split_pillar(pillar)
            gan_element = STEM_ELEMENTS.get(gan, "")
            zhi_element = BRANCH_MAIN_ELEMENTS.get(zhi, "")
            item_start_age = _safe_int(_call_first(item, ["getStartAge"]))
            item_end_age = _safe_int(_call_first(item, ["getEndAge"]))
            item_start_age, item_end_age = _normalize_age_range(
                item_start_age,
                item_end_age,
                max(0, start_age),
                len(dayun_list),
            )
            item_start_year = _safe_int(_call_first(item, ["getStartYear"]))
            item_end_year = _safe_int(_call_first(item, ["getEndYear"]))
            if not start_age:
                start_age = item_start_age
            luck_item = {
                "index": len(dayun_list) + 1,
                "pillar": pillar,
                "gan": gan,
                "zhi": zhi,
                "gan_element": gan_element,
                "zhi_element": zhi_element,
                "ten_god": get_ten_god(chart.get("day_master", ""), gan) if gan else "未知",
                "start_age": item_start_age,
                "end_age": item_end_age,
                "start_year": item_start_year,
                "end_year": item_end_year,
            }
            luck_item.update(analyze_luck_stage(chart, luck_item))
            dayun_list.append(luck_item)

        if not dayun_list:
            return {
                "available": False,
                "message": "当前环境暂未成功获取大运接口，将在后续版本继续兼容。",
                "debug_message": "DaYun list is empty or all GanZhi values are empty.",
            }

        return {
            "available": True,
            "start_age": start_age,
            "start_year": start_year,
            "start_month": start_month,
            "start_day": _call_first(yun, ["getStartDay"]) or "",
            "start_text": _start_text(start_age, start_year, start_month),
            "dayun_list": dayun_list,
            "yearly_list": _build_yearly_list(chart, 10),
        }
    except ModuleNotFoundError as exc:
        if exc.name == "lunar_python":
            return {
                "available": False,
                "message": "缺少 lunar_python，请先运行：python -m pip install -r requirements.txt",
            }
        return {
            "available": False,
            "message": "当前环境暂未成功获取大运接口，将在后续版本继续兼容。",
            "debug_message": str(exc),
        }
    except Exception as exc:
        return {
            "available": False,
            "message": "当前环境暂未成功获取大运接口，将在后续版本继续兼容。",
            "debug_message": str(exc),
        }
