"""个人命盘的四柱矩阵与五行分布展示组件。"""

from __future__ import annotations

from html import escape
import math
from typing import Any

import streamlit as st

from core.bazi_constants import (
    BRANCH_MAIN_ELEMENTS,
    FIVE_ELEMENT_ORDER,
    STEM_ELEMENTS,
)
from core.five_elements import judge_element_strength
from ui.styles import ELEMENT_COLORS


PILLAR_ORDER = (
    ("year", "年柱"),
    ("month", "月柱"),
    ("day", "日柱"),
    ("hour", "时柱"),
)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    rendered = str(value).strip()
    return rendered or default


def _pillar_parts(raw_pillar: Any) -> tuple[str, str, dict]:
    if isinstance(raw_pillar, dict):
        full = _text(raw_pillar.get("pillar") or raw_pillar.get("gan_zhi"))
        stem = _text(
            raw_pillar.get("gan")
            or raw_pillar.get("stem")
            or raw_pillar.get("heavenly_stem")
        )
        branch = _text(
            raw_pillar.get("zhi")
            or raw_pillar.get("branch")
            or raw_pillar.get("earthly_branch")
        )
        stem = stem or full[:1]
        branch = branch or full[1:2]
        return stem, branch, raw_pillar

    full = _text(raw_pillar)
    return full[:1], full[1:2], {}


def _ten_god_text(raw: Any) -> str:
    if isinstance(raw, dict):
        return _text(raw.get("gan") or raw.get("stem") or raw.get("ten_god"))
    return _text(raw)


def _hidden_stem_view(raw: Any) -> list[dict]:
    if isinstance(raw, (str, dict)):
        items = [raw]
    elif isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        items = []

    result = []
    for item in items:
        if isinstance(item, dict):
            stem = _text(item.get("gan") or item.get("stem"))
            element = _text(item.get("element")) or STEM_ELEMENTS.get(stem, "")
            ten_god = _text(item.get("ten_god") or item.get("god"))
        else:
            stem = _text(item)
            element = STEM_ELEMENTS.get(stem, "")
            ten_god = ""
        if stem:
            result.append({"stem": stem, "element": element, "ten_god": ten_god})
    return result


def build_four_pillars_view(chart: dict) -> list[dict]:
    """将现有 chart 字段适配为固定年、月、日、时顺序的展示模型。"""
    chart = chart if isinstance(chart, dict) else {}
    pillars = chart.get("pillars") if isinstance(chart.get("pillars"), dict) else {}
    ten_gods = chart.get("ten_gods") if isinstance(chart.get("ten_gods"), dict) else {}
    hidden_stems = (
        chart.get("hidden_stems") if isinstance(chart.get("hidden_stems"), dict) else {}
    )

    result = []
    for key, default_label in PILLAR_ORDER:
        raw_pillar = pillars.get(key, chart.get(f"{key}_pillar", {}))
        stem, branch, pillar_details = _pillar_parts(raw_pillar)
        raw_ten_god = ten_gods.get(key, pillar_details.get("ten_god", ""))
        raw_hidden = hidden_stems.get(key)
        if not raw_hidden and isinstance(raw_ten_god, dict):
            raw_hidden = raw_ten_god.get("hidden_stems", [])

        result.append(
            {
                "label": _text(pillar_details.get("name"), default_label),
                "stem": stem,
                "branch": branch,
                "stem_element": _text(pillar_details.get("stem_element"))
                or STEM_ELEMENTS.get(stem, ""),
                "branch_element": _text(pillar_details.get("branch_element"))
                or BRANCH_MAIN_ELEMENTS.get(branch, ""),
                "ten_god": _ten_god_text(raw_ten_god),
                "hidden_stems": _hidden_stem_view(raw_hidden),
                "na_yin": _text(pillar_details.get("na_yin")),
                "di_shi": _text(pillar_details.get("di_shi")),
                "xun_kong": _text(
                    pillar_details.get("xun_kong") or pillar_details.get("void")
                ),
            }
        )
    return result


def _non_negative_number(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("score", value.get("value", 0))
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return round(max(0.0, number), 2)


def build_element_distribution(chart: dict) -> list[dict]:
    """返回固定五行顺序、非负数值的水平条展示模型。"""
    chart = chart if isinstance(chart, dict) else {}
    raw_elements = chart.get("five_elements", {})
    if not isinstance(raw_elements, dict):
        raw_elements = {}
    values = {
        element: _non_negative_number(raw_elements.get(element, 0))
        for element in FIVE_ELEMENT_ORDER
    }
    total = sum(values.values())
    return [
        {
            "element": element,
            "value": value,
            "percentage": round(value / total * 100, 1) if total else 0.0,
            "level": judge_element_strength(value, total),
            "color": ELEMENT_COLORS[element],
        }
        for element, value in values.items()
    ]


def _hidden_stems_html(items: list[dict]) -> str:
    if not items:
        return '<span class="ms4-empty">暂无记录</span>'
    labels = []
    for item in items:
        detail = " · ".join(
            part for part in (_text(item.get("element")), _text(item.get("ten_god"))) if part
        )
        suffix = f"<small>{escape(detail)}</small>" if detail else ""
        labels.append(f'<span class="ms4-hidden-stem">{escape(_text(item.get("stem")))}{suffix}</span>')
    return "".join(labels)


def render_four_pillars_matrix(chart: dict) -> None:
    """渲染四柱矩阵；移动端由全局 CSS 重排为非四列布局。"""
    cards = []
    for pillar in build_four_pillars_view(chart):
        helper_parts = []
        if pillar["na_yin"]:
            helper_parts.append(f'纳音 {escape(pillar["na_yin"])}')
        if pillar["di_shi"]:
            helper_parts.append(f'星运 {escape(pillar["di_shi"])}')
        if pillar["xun_kong"]:
            helper_parts.append(f'旬空 {escape(pillar["xun_kong"])}')
        helper = " · ".join(helper_parts)
        helper_html = f'<p class="ms4-pillar-helper">{helper}</p>' if helper else ""
        cards.append(
            '<article class="ms4-pillar-card">'
            f'<p class="ms4-pillar-label">{escape(pillar["label"])}</p>'
            f'<p class="ms4-ten-god">十神 <strong>{escape(pillar["ten_god"] or "未记录")}</strong></p>'
            '<div class="ms4-pillar-glyphs">'
            f'<div><span>天干</span><strong>{escape(pillar["stem"] or "—")}</strong>'
            f'<small>{escape(pillar["stem_element"] or "未知")}</small></div>'
            f'<div><span>地支</span><strong>{escape(pillar["branch"] or "—")}</strong>'
            f'<small>{escape(pillar["branch_element"] or "未知")}</small></div>'
            '</div>'
            '<div class="ms4-hidden-row"><span>藏干</span>'
            f'<div>{_hidden_stems_html(pillar["hidden_stems"])}</div></div>'
            f'{helper_html}'
            '</article>'
        )
    st.markdown(
        '<section class="ms4-chart-section" aria-label="四柱矩阵">'
        '<div class="ms4-section-head"><div><p>FOUR PILLARS</p><h3>四柱矩阵</h3></div>'
        '<span>按年、月、日、时顺序阅读</span></div>'
        f'<div class="ms4-four-pillars">{"".join(cards)}</div></section>',
        unsafe_allow_html=True,
    )


def render_element_distribution(chart: dict) -> None:
    """渲染带数值、占比和等级文字的五行水平分布。"""
    rows = []
    for item in build_element_distribution(chart):
        percentage = min(100.0, max(0.0, item["percentage"]))
        value_text = f'{item["value"]:g}'
        rows.append(
            '<div class="ms4-element-row">'
            f'<div class="ms4-element-name"><strong>{escape(item["element"])}</strong>'
            f'<span>{escape(item["level"])}</span></div>'
            '<div class="ms4-element-track" role="img" '
            f'aria-label="{escape(item["element"])} {value_text}，{item["percentage"]:g}%，{escape(item["level"])}">'
            f'<span class="ms4-element-bar" style="width:{percentage:g}%;--element-color:{item["color"]};"></span>'
            '</div>'
            f'<div class="ms4-element-value"><strong>{value_text}</strong><span>{item["percentage"]:g}%</span></div>'
            '</div>'
        )
    st.markdown(
        '<section class="ms4-chart-section" aria-label="五行分布">'
        '<div class="ms4-section-head"><div><p>FIVE ELEMENTS</p><h3>五行分布</h3></div>'
        '<span>横向条长表示占比，右侧同时标注原始数值</span></div>'
        f'<div class="ms4-element-distribution">{"".join(rows)}</div></section>',
        unsafe_allow_html=True,
    )
