"""紫微斗数基础报告。"""

from __future__ import annotations

from report.export_report import DISCLAIMER


KEY_PALACES = ["命宫", "身宫", "夫妻宫", "财帛宫", "官禄宫", "迁移宫", "田宅宫", "福德宫"]


def _find_palace(chart: dict, name: str) -> dict:
    """查找宫位。"""
    if name == "身宫":
        for item in chart.get("palaces", []):
            if item.get("is_body_palace"):
                return item
        return {}
    for item in chart.get("palaces", []):
        if item.get("name") == name:
            return item
    return {}


def generate_ziwei_report(chart: dict) -> dict:
    """
    生成紫微斗数基础报告。
    """
    if not chart.get("available"):
        return {
            "title": "紫微斗数基础报告",
            "sections": [{"title": "提示", "text": chart.get("message", "紫微斗数基础盘暂不可用。")}],
            "advice": "请先生成基础盘。",
            "disclaimer": DISCLAIMER,
        }
    sections = []
    for name in KEY_PALACES:
        palace = _find_palace(chart, name)
        branch = palace.get("branch", chart.get("body_palace", "") if name == "身宫" else "")
        text = palace.get("explanation", "该宫位用于辅助观察人生对应主题。")
        sections.append({"title": f"{name}分析", "text": f"{name}落在{branch or '待确认'}，{text} 当前版本采用基础宫位解释，{chart.get('star_note', '')}"})
    sections.append(
        {
            "title": "综合建议",
            "text": "紫微斗数当前为基础宫位分析版，适合与八字排盘、五行十神和年度运程交叉参考，不建议单独作为重大决策依据。",
        }
    )
    return {
        "title": "紫微斗数基础报告",
        "sections": sections,
        "advice": sections[-1]["text"],
        "disclaimer": DISCLAIMER,
    }
