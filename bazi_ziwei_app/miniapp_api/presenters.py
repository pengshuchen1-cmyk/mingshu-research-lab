"""把现有核心结果整理成小程序可直接渲染的展示文档。"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import math
from typing import Any

from core.bazi_constants import STEM_ELEMENTS


ELEMENT_COLORS = {
    "木": "#4F8A5B",
    "火": "#C2413B",
    "土": "#A16207",
    "金": "#64748B",
    "水": "#2563EB",
}

TONE_CLASSES = {
    "木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water",
    "accent": "accent", "warning": "warning", "": "default",
}

FEATURES = [
    {"key": "bazi", "title": "八字排盘", "caption": "四柱、藏干、十神与甲子名片", "route": "/pages/feature/index?type=bazi"},
    {"key": "overview", "title": "命盘总览", "caption": "人生主线与五维洞察", "route": "/pages/feature/index?type=overview"},
    {"key": "five-elements", "title": "五行喜忌", "caption": "强弱、喜忌与现实建议", "route": "/pages/feature/index?type=five-elements"},
    {"key": "sixty-jiazi", "title": "六十甲子", "caption": "四柱甲子与纳音说明", "route": "/pages/feature/index?type=sixty-jiazi"},
    {"key": "luck", "title": "大运流年", "caption": "十年阶段与未来流年", "route": "/pages/feature/index?type=luck"},
    {"key": "yearly", "title": "年度运程", "caption": "年度专项与十二个月", "route": "/pages/feature/index?type=yearly"},
    {"key": "career", "title": "事业专项", "caption": "事业结构、风险和行动", "route": "/pages/feature/index?type=career"},
    {"key": "wealth", "title": "财运专项", "caption": "收入方式、现金流和风险", "route": "/pages/feature/index?type=wealth"},
    {"key": "love", "title": "婚恋专项", "caption": "关系模式与沟通建议", "route": "/pages/feature/index?type=love"},
    {"key": "ziwei", "title": "紫微斗数", "caption": "十二宫、星曜、四化与说明书", "route": "/pages/feature/index?type=ziwei"},
    {"key": "compatibility", "title": "合婚匹配", "caption": "双人十一维合盘分析", "route": "/pages/compatibility/index"},
    {"key": "acceptance", "title": "验收中心", "caption": "五个固定样例与差异检查", "route": "/pages/feature/index?type=acceptance"},
]


LABELS = {
    "summary": "摘要", "title": "标题", "text": "正文", "advice": "建议",
    "evidence": "命盘依据", "disclaimer": "边界说明", "overall_pattern": "总体格局",
    "overall_summary": "总体结论", "life_keywords": "人生关键词", "key_strengths": "主要优势",
    "key_risks": "主要风险", "long_term_advice": "长期建议", "wealth_overview": "财富",
    "romance_overview": "关系", "health_overview": "健康", "career_overview": "事业",
    "strength": "日主强弱", "favorable_elements": "喜用五行", "unfavorable_elements": "谨慎五行",
    "pattern": "格局", "plain_text": "白话解释", "message": "说明", "basis": "计算依据",
    "direction": "顺逆", "direction_label": "行运方向", "start_age": "起运年龄",
    "start_year": "起运年份", "start_month": "起运月份", "start_text": "起运说明",
    "pillar": "干支", "ten_god": "十神", "branch_relations": "地支关系", "overall_level": "年度等级",
    "overall_text": "年度总论", "career_text": "事业解读", "wealth_text": "财富解读",
    "relationship_text": "关系解读", "health_text": "健康解读", "risk_text": "风险提醒",
    "advice_text": "行动建议", "suitable_actions": "适合做", "actions_to_avoid": "暂缓做",
    "month_name": "月份", "theme": "主题", "event_tags": "事件标签", "event_tendency": "事件倾向",
    "probability": "可能性", "reality": "现实表现", "triggers": "触发因素",
    "overall_score": "总分", "level": "等级", "key_cautions": "重点提醒",
    "match_reasons": "为什么合", "conflict_reasons": "为什么需要磨合", "advice_list": "相处建议",
    "life_palace": "命宫", "body_palace": "身宫", "five_element_bureau": "五行局",
    "star_note": "星曜说明", "module_boundary": "模块边界", "focus_cards": "重点宫位",
    "capabilities": "能力完成度", "sections": "报告章节", "public_summary": "公开摘要",
}


def json_safe(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(item) for item in value]
    return str(value)


def label(key: object) -> str:
    raw = str(key)
    return LABELS.get(raw, raw.replace("_", " "))


def _string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, "")]
    return []


def _row(name: str, value: Any, tone: str = "") -> dict:
    if isinstance(value, bool):
        text = "是" if value else "否"
    elif value is None or value == "":
        text = "—"
    else:
        text = str(value)
    return {"label": name, "value": text, "tone": tone}


def _card(title: str, text: str = "", *, tags: list[str] | None = None,
          rows: list[dict] | None = None, tone: str = "", score: int | float | None = None) -> dict:
    return {
        "title": title,
        "text": str(text or ""),
        "tags": tags or [],
        "rows": rows or [],
        "tone": tone,
        "tone_class": TONE_CLASSES.get(tone, "default"),
        "score": score,
    }


def _hero(title: str, eyebrow: str, subtitle: str, *, metrics: list[dict] | None = None) -> dict:
    return {"title": title, "eyebrow": eyebrow, "subtitle": subtitle, "metrics": metrics or []}


def _section(title: str, *, caption: str = "", kind: str = "cards",
             items: list[dict] | None = None) -> dict:
    return {"title": title, "caption": caption, "kind": kind, "items": items or []}


def _simple_rows(data: dict, keys: list[str]) -> list[dict]:
    result = []
    for key in keys:
        if key not in data:
            continue
        value = data.get(key)
        if isinstance(value, (list, tuple)):
            value = "、".join(str(item) for item in value)
        elif isinstance(value, dict):
            value = "；".join(f"{label(k)}：{v}" for k, v in value.items() if not isinstance(v, (dict, list)))
        result.append(_row(label(key), value))
    return result


def bazi_document(profile: dict, chart: dict, report: dict) -> dict:
    pillars = chart.get("pillars", {})
    ten_gods = chart.get("ten_gods", {})
    hidden = chart.get("hidden_stems", {})
    pillar_items = []
    for key, name in (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")):
        item = pillars.get(key, {})
        hidden_text = "、".join(
            f"{entry.get('gan', '')}·{entry.get('ten_god', '')}" for entry in hidden.get(key, [])
        )
        pillar_items.append(_card(
            name,
            item.get("pillar") or "时柱不详",
            tags=[ten_gods.get(key, {}).get("gan", ""), item.get("na_yin", "")],
            rows=[_row("天干", item.get("gan")), _row("地支", item.get("zhi")), _row("藏干", hidden_text)],
            tone="accent" if key == "day" else "",
        ))
    elements = chart.get("five_elements", {})
    total = sum(float(value or 0) for value in elements.values()) or 1
    element_items = [
        _card(element, f"{float(elements.get(element, 0)) / total * 100:.1f}%", score=round(float(elements.get(element, 0)) / total * 100, 1), tone=element)
        for element in ("木", "火", "土", "金", "水")
    ]
    strength = chart.get("day_master_strength", {})
    pattern = chart.get("pattern_analysis", {})
    return {
        "key": "bazi",
        "hero": _hero(
            "八字排盘",
            "FOUR PILLARS · 本地规则",
            f"{profile.get('name', '访客')}｜{profile.get('gender', '')}｜{chart.get('lunar_text', '')}",
            metrics=[
                _row("日主", chart.get("day_master")),
                _row("五行", STEM_ELEMENTS.get(chart.get("day_master", ""), "")),
                _row("强弱", strength.get("strength")),
            ],
        ),
        "sections": [
            _section("四柱命盘", caption="年、月、日、时固定顺序；日柱为日主核心。", kind="pillars", items=pillar_items),
            _section("五行分布", kind="progress", items=element_items),
            _section("十神结构", items=[
                _card(name, str(count), score=count) for name, count in chart.get("ten_god_counts", {}).items()
            ]),
            _section("强弱与格局", items=[
                _card(strength.get("strength", "日主强弱"), strength.get("message", ""),
                      tags=_string_list(strength.get("favorable_elements")),
                      rows=_simple_rows(strength, ["favorable_elements", "unfavorable_elements", "net_score"])),
                _card(pattern.get("pattern", "格局"), pattern.get("plain_text", ""),
                      rows=[_row("依据", "；".join(_string_list(pattern.get("evidence"))))]),
            ]),
            _section("基础报告", items=[
                _card(label(key), value) for key, value in report.items()
                if isinstance(value, str) and value.strip() and key not in {"public_summary"}
            ]),
        ],
    }


def overview_document(profile: dict, chart: dict, overview: dict) -> dict:
    scores = overview.get("scores", {})
    score_map = (("财富", "wealth"), ("关系", "romance"), ("健康", "health_stability"), ("事业", "career"), ("整体平衡", "overall"))
    score_items = []
    for title, key in score_map:
        raw = scores.get(key, scores.get("overall_pace", 0))
        try:
            score = int(round(float(raw)))
        except (TypeError, ValueError):
            score = 0
        overview_key = {"wealth": "wealth_overview", "romance": "romance_overview", "health_stability": "health_overview", "career": "career_overview"}.get(key)
        content = overview.get(overview_key, {}) if overview_key else {}
        text = content.get("summary", "") if isinstance(content, dict) else str(content or "")
        score_items.append(_card(title, text, score=score, tone="accent" if key == "overall" else ""))
    strength = chart.get("day_master_strength", {})
    return {
        "key": "overview",
        "hero": _hero(
            "个人命盘",
            "PERSONAL CHART · 结论先行",
            overview.get("overall_summary", ""),
            metrics=[
                _row("日主", chart.get("day_master")),
                _row("强弱", strength.get("strength")),
                _row("格局", overview.get("overall_pattern")),
            ],
        ),
        "sections": [
            _section("命盘身份卡", items=[_card(
                profile.get("name", "访客"),
                overview.get("overall_summary", ""),
                tags=_string_list(overview.get("life_keywords")),
                rows=[_row("出生资料", f"{profile.get('birth_date', '')} {profile.get('birth_hour', '')}:{profile.get('birth_minute', '')}"),
                      _row("喜用", "、".join(_string_list(strength.get("favorable_elements"))))],
            )]),
            _section("五维洞察", caption="分数同时配合文字解释，不单独作为现实决策。", kind="scores", items=score_items),
            _section("优势、风险与长期建议", items=[
                _card("主要优势", tags=_string_list(overview.get("key_strengths"))),
                _card("主要风险", tags=_string_list(overview.get("key_risks")), tone="warning"),
                _card("长期建议", tags=_string_list(overview.get("long_term_advice"))),
            ]),
            _section("命理依据", items=[_card("判断依据", tags=_string_list(overview.get("evidence")))]),
        ],
    }


def five_elements_document(chart: dict, deep: dict) -> dict:
    details = deep.get("element_details", {})
    element_items = []
    for element in ("木", "火", "土", "金", "水"):
        item = details.get(element, {}) if isinstance(details, dict) else {}
        element_items.append(_card(
            element,
            item.get("summary", item.get("meaning", "")) if isinstance(item, dict) else str(item),
            tags=_string_list(item.get("keywords")) if isinstance(item, dict) else [],
            rows=_simple_rows(item, ["score", "ratio", "strength", "role", "advice"]) if isinstance(item, dict) else [],
            tone=element,
        ))
    return {
        "key": "five-elements",
        "hero": _hero("五行喜忌", "FIVE ELEMENTS · 深度报告", deep.get("element_balance_summary", ""), metrics=[
            _row("偏旺", "、".join(_string_list(deep.get("strong_elements")))),
            _row("偏弱", "、".join(_string_list(deep.get("weak_elements")))),
            _row("喜用", "、".join(_string_list(deep.get("favorable_elements")))),
        ]),
        "sections": [
            _section("五行结构", kind="progress", items=element_items),
            _section("现实领域", items=[
                _card("事业", deep.get("career_implications", "")),
                _card("财富", deep.get("wealth_implications", "")),
                _card("关系", deep.get("relationship_implications", "")),
                _card("健康", deep.get("health_implications", ""), tone="warning"),
            ]),
            _section("调节建议", items=[_card("行动建议", tags=_string_list(deep.get("adjustment_advice")))]),
            _section("判断依据", items=[_card("命盘证据", tags=_string_list(deep.get("evidence")))]),
        ],
    }


def luck_document(profile: dict, chart: dict, luck: dict) -> dict:
    dayun_items = []
    for item in luck.get("dayun_list", []):
        dayun_items.append(_card(
            item.get("pillar", "大运"),
            item.get("summary", item.get("stage_text", item.get("advice", ""))),
            tags=[str(item.get("stage_level", "")), str(item.get("ten_god", ""))],
            rows=_simple_rows(item, ["start_age", "end_age", "start_year", "end_year", "gan_element", "zhi_element"]),
            tone="accent" if item.get("is_current") else "",
        ))
    yearly_items = [
        _card(str(item.get("year", "")), item.get("brief_text", item.get("overall_text", "")),
              tags=_string_list(item.get("keywords")), rows=_simple_rows(item, ["pillar", "ten_god", "overall_level"]))
        for item in luck.get("yearly_list", [])
    ]
    return {
        "key": "luck",
        "hero": _hero("大运流年分析", "LUCK CYCLES · 阶段节奏", f"{profile.get('name', '访客')}｜日主 {chart.get('day_master', '')}", metrics=[
            _row("行运方向", luck.get("direction_label", luck.get("direction"))),
            _row("起运年龄", luck.get("start_age")),
            _row("起运年份", luck.get("start_year")),
        ]),
        "sections": [
            _section("起运信息", items=[_card("起运说明", luck.get("start_text", ""), rows=_simple_rows(luck, ["start_month", "start_day"]))]),
            _section("完整大运", caption="当前大运使用粉色边框标记。", items=dayun_items),
            _section("未来流年速览", items=yearly_items),
            _section("数据边界", items=[_card("提示", tags=_string_list(luck.get("data_warnings")), tone="warning")]),
        ],
    }


def yearly_document(chart: dict, yearly: dict, monthly: list[dict], events: list[dict]) -> dict:
    months = []
    for index, item in enumerate(monthly):
        event_result = events[index] if index < len(events) else {}
        top_events = event_result.get("top_events", [])[:3]
        event_lines = []
        for event in top_events:
            title = event.get("label", event.get("title", "重点事件"))
            reason = event.get("reason", event.get("summary", ""))
            event_lines.append(f"{title}：{reason}")
        months.append(_card(
            item.get("month_name", f"{index + 1}月"),
            item.get("event_tendency", item.get("theme", "")),
            tags=_string_list(item.get("event_tags"))[:3],
            rows=[
                _row("月柱", item.get("pillar")),
                _row("事业", item.get("career_text")),
                _row("财富", item.get("wealth_text")),
                _row("关系", item.get("relationship_text")),
                _row("风险", item.get("risk_text")),
                _row("行动", item.get("advice_text")),
                *[_row("重点事件", line) for line in event_lines],
            ],
        ))
    return {
        "key": "yearly",
        "hero": _hero(f"{yearly.get('year')} 年度运程", "YEARLY GUIDANCE · 十二个月", yearly.get("overall_text", ""), metrics=[
            _row("流年柱", yearly.get("pillar")),
            _row("十神", yearly.get("ten_god")),
            _row("年度等级", yearly.get("overall_level")),
        ]),
        "sections": [
            _section("年度关键词", items=[_card("今年的节奏", yearly.get("brief_text", ""), tags=_string_list(yearly.get("annual_keywords"))[:5])]),
            _section("年度专项", items=[
                _card("事业", yearly.get("career_text", ""), tags=_string_list(yearly.get("career_good_months"))),
                _card("财富", yearly.get("wealth_text", ""), tags=_string_list(yearly.get("wealth_good_months"))),
                _card("关系", yearly.get("relationship_text", ""), tags=_string_list(yearly.get("peach_months"))),
                _card("健康", yearly.get("health_text", ""), tags=_string_list(yearly.get("health_concerns")), tone="warning"),
            ]),
            _section("风险与行动", items=[
                _card("主要风险", yearly.get("risk_text", ""), tags=_string_list(yearly.get("actions_to_avoid")), tone="warning"),
                _card("优先行动", yearly.get("advice_text", ""), tags=_string_list(yearly.get("suitable_actions"))),
            ]),
            _section("十二个月", caption="点击月份卡片可展开完整解读。", kind="months", items=months),
        ],
    }


def report_document(report: dict, title: str, eyebrow: str) -> dict:
    sections = report.get("sections", []) if isinstance(report, dict) else []
    items = []
    for index, item in enumerate(sections):
        if isinstance(item, dict):
            items.append(_card(item.get("title", f"章节 {index + 1}"), item.get("text", ""),
                               tags=_string_list(item.get("evidence"))))
    used = {"title", "sections", "disclaimer", "source_ids", "source_titles"}
    details = []
    for key, value in report.items():
        if key in used or value in (None, "", [], {}):
            continue
        if isinstance(value, str):
            details.append(_card(label(key), value))
        elif isinstance(value, list) and all(not isinstance(entry, dict) for entry in value):
            details.append(_card(label(key), tags=_string_list(value)))
    return {
        "key": eyebrow.lower().replace(" ", "-"),
        "hero": _hero(title, eyebrow, report.get("public_summary", report.get("summary", report.get("title", "")))),
        "sections": [
            _section("核心判断", items=details),
            _section("完整章节", items=items),
            _section("边界说明", items=[_card("使用说明", report.get("disclaimer", ""), tone="warning")]),
        ],
    }


def ziwei_document(profile: dict, chart: dict, guide: dict, capability: dict, report: dict, sihua: dict) -> dict:
    palaces = []
    sihua_by_palace = sihua.get("sihua_by_palace", {})
    for item in chart.get("palaces", []):
        name = item.get("name", "宫位")
        palaces.append(_card(
            name,
            item.get("palace_theme", ""),
            tags=[
                *chart.get("main_stars_by_palace", {}).get(name, item.get("main_stars", [])),
                *chart.get("minor_stars_by_palace", {}).get(name, item.get("minor_stars", [])),
                *chart.get("fierce_stars_by_palace", {}).get(name, item.get("fierce_stars", [])),
                *sihua_by_palace.get(name, []),
            ],
            rows=[_row("地支", item.get("branch")), _row("命宫", item.get("is_life_palace", False)), _row("身宫", item.get("is_body_palace", False))],
            tone="accent" if item.get("is_life_palace") else "",
        ))
    focus_items = []
    for item in guide.get("focus_cards", []):
        focus_items.append(_card(
            item.get("plain_title", item.get("title", "重点宫位")),
            item.get("one_sentence", ""),
            tags=[*item.get("main_stars", []), *item.get("sihua", [])],
            rows=[
                _row("现实里怎么看", item.get("real_world_view")),
                _row("注意什么", item.get("what_to_notice")),
                _row("行动建议", item.get("action_advice")),
                _row("边界", item.get("boundary_note")),
            ],
        ))
    capability_items = [
        _card(item.get("name", "能力"), item.get("user_text", ""), tags=[item.get("status", "")], rows=[_row("边界", item.get("boundary"))])
        for item in capability.get("items", [])
    ]
    return {
        "key": "ziwei",
        "hero": _hero("紫微斗数", "ZIWEI · 十二宫说明书", guide.get("summary", chart.get("message", "")), metrics=[
            _row("命宫", chart.get("life_palace")),
            _row("身宫", chart.get("body_palace")),
            _row("五行局", chart.get("five_element_bureau", {}).get("bureau_name") if isinstance(chart.get("five_element_bureau"), dict) else chart.get("five_element_bureau")),
        ]),
        "sections": [
            _section("重点先看", items=focus_items),
            _section("十二宫盘", kind="palaces", items=palaces),
            _section("大限基础", items=[_card(str(item.get("age_range", item.get("start_age", "大限"))), item.get("meaning", ""), rows=_simple_rows(item, ["palace_name", "start_age", "end_age", "pillar"])) for item in chart.get("daxian", {}).get("periods", chart.get("daxian", {}).get("stages", []))]),
            _section("算法完成度", items=capability_items),
            _section("紫微综合报告", items=[_card(item.get("title", "章节"), item.get("text", "")) for item in report.get("sections", [])]),
            _section("边界", items=[_card("版本边界", guide.get("boundary", ""), tone="warning")]),
        ],
    }


def sixty_jiazi_document(chart: dict, cards: list[dict], comparison: dict) -> dict:
    items = []
    for card in cards:
        items.append(_card(
            f"{card.get('label', '')} · {card.get('pillar', '')}",
            card.get("user_explanation", ""),
            tags=_string_list(card.get("keywords")),
            rows=[_row("纳音", card.get("nayin")), _row("人生领域", card.get("life_area")), _row("现实观察", card.get("reality_hint")), _row("建议", card.get("advice"))],
        ))
    distribution = comparison.get("chart_distribution", {})
    progress = [_card(element, f"{item.get('ratio', 0)}%", score=item.get("ratio", 0), tone=element) for element, item in distribution.items()]
    return {
        "key": "sixty-jiazi",
        "hero": _hero("六十甲子", "SIXTY JIAZI · 传统知识", "把四柱干支转成更容易理解的甲子名片；纳音只作辅助说明。", metrics=[_row("日主", chart.get("day_master"))]),
        "sections": [
            _section("四柱甲子名片", items=items),
            _section("纳音与原局五行", caption=comparison.get("explanation", ""), kind="progress", items=progress),
            _section("边界", items=[_card("说明", "六十甲子与纳音是知识层和解释层，不作为断事核心；具体判断仍以日主强弱、十神、喜忌、大运流年为主。", tone="warning")]),
        ],
    }


def compatibility_document(result: dict, first_name: str, second_name: str) -> dict:
    dimensions = [
        _card(item.get("label", "维度"), item.get("text", ""), score=item.get("score"),
              rows=[_row("得分", f"{item.get('score', 0)}/{item.get('max_score', 0)}"), _row("细节", item.get("detail"))])
        for item in result.get("dimensions", [])
    ]
    return {
        "key": "compatibility",
        "hero": _hero("合婚匹配", "COMPATIBILITY · 十一维", result.get("summary", ""), metrics=[
            _row("甲方", first_name), _row("乙方", second_name), _row("总分", f"{result.get('overall_score', 0)}/100"), _row("等级", result.get("level")),
        ]),
        "sections": [
            _section("双方命主特质", items=[
                _card("甲方", result.get("person_a", {}).get("description", ""), tags=_string_list(result.get("person_a", {}).get("core_traits"))),
                _card("乙方", result.get("person_b", {}).get("description", ""), tags=_string_list(result.get("person_b", {}).get("core_traits"))),
            ]),
            _section("十一维评分", kind="scores", items=dimensions),
            _section("为什么合", items=[_card("匹配信号", tags=_string_list(result.get("match_reasons")))]),
            _section("为什么需要磨合", items=[_card("冲突信号", tags=_string_list(result.get("conflict_reasons")), tone="warning")]),
            _section("相处建议", items=[_card("行动建议", tags=_string_list(result.get("advice_list")))]),
            _section("重点提醒", items=[_card("注意", tags=_string_list(result.get("key_cautions")), tone="warning")]),
        ],
    }


def acceptance_document(samples: list[dict]) -> dict:
    items = []
    for sample in samples:
        chart = sample.get("chart", {})
        yearly = sample.get("yearly", {})
        items.append(_card(
            sample.get("profile", {}).get("name", "样例"),
            sample.get("overview", {}).get("overall_summary", ""),
            tags=[chart.get("day_master", ""), yearly.get("pillar", ""), yearly.get("overall_level", "")],
            rows=[_row("四柱", " / ".join(item.get("pillar", "") for item in chart.get("pillars", {}).values())), _row("年度", yearly.get("overall_text"))],
        ))
    return {
        "key": "acceptance",
        "hero": _hero("验收中心", "ACCEPTANCE · 固定样例", "集中查看五个固定样例的命盘、年度与内容差异。", metrics=[_row("样例数", len(samples))]),
        "sections": [_section("五个验收样例", items=items)],
    }


def home_document(daily: dict, yearly: dict) -> dict:
    return {
        "brand": "命数研究室",
        "kicker": "命数研究室 · 日常指导",
        "title": "认识命数\n活出选择",
        "subtitle": "利用构建的命数体系，理解人生的底层逻辑，在每一个当下，做更清醒的选择。",
        "daily": json_safe(daily),
        "yearly": json_safe(yearly),
        "features": FEATURES,
    }
