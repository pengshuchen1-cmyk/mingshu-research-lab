"""命盘总览页面 —— 结论先行的个人摘要与命盘图形。"""

from __future__ import annotations

from html import escape
import json

import streamlit as st

from core.bazi_constants import STEM_ELEMENTS
from core.bazi_engine import ensure_bazi_analysis_fields
from core.bazi_term_glossary import build_term_view, collect_term_ids
from core.life_overview_engine import analyze_life_overview
from core.presentation_models import (
    build_term_chip_view,
    build_term_detail_view,
    build_term_disclosure_semantics,
    transition_term_disclosure,
)
from ui.chart_visual_components import (
    render_element_distribution,
    render_four_pillars_matrix,
)
from ui.bazi_components import render_rule_summary
from ui.primitives import empty_state_header, page_header, section_header


_ELEMENT_PATTERN_NAMES = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}
_TERM_STATE_KEY = "life_overview_expanded_term_id"
_TERM_FOCUS_RETURN_KEY = "life_overview_term_focus_return"


def _first_sentence(text: object, fallback: str = "暂无摘要。") -> str:
    summary = str(text or "").strip()
    if not summary:
        return fallback
    first_period = summary.find("。")
    sentence = summary[: first_period + 1] if first_period >= 0 else summary
    if len(sentence) > 80:
        sentence = sentence[:80].rstrip() + "…"
    return sentence


def _build_life_identity_card(chart: dict, overview: dict) -> dict:
    """把命盘与总览结论转成稳定的身份卡展示模型。"""
    profile = chart.get("profile", {}) if isinstance(chart.get("profile"), dict) else {}
    strength_info = (
        chart.get("day_master_strength", {})
        if isinstance(chart.get("day_master_strength"), dict)
        else {}
    )
    day_master = str(chart.get("day_master") or "—").strip()
    day_element = STEM_ELEMENTS.get(day_master, "未知")
    strength = str(strength_info.get("strength") or "暂无判断").strip()

    raw_elements = chart.get("five_elements", {})
    element_scores = []
    if isinstance(raw_elements, dict):
        for element in _ELEMENT_PATTERN_NAMES:
            try:
                element_scores.append((element, max(0.0, float(raw_elements.get(element, 0)))))
            except (TypeError, ValueError):
                element_scores.append((element, 0.0))
    total = sum(score for _, score in element_scores)
    dominant_elements = [
        element
        for element, score in sorted(element_scores, key=lambda item: item[1], reverse=True)
        if total and score / total >= 0.30
    ][:2]

    overall_pattern = str(overview.get("overall_pattern") or "格局待判").strip()
    pattern = overall_pattern.split("·", 1)[-1].strip()
    summary_source = str(overview.get("overall_summary") or "").strip()
    pattern_position = summary_source.find(overall_pattern)
    if pattern_position > 0:
        summary_source = summary_source[pattern_position:]
    term_ids = [
        "day-master",
        f"day-element-{_ELEMENT_PATTERN_NAMES.get(day_element, 'unknown')}",
        "strength",
        *(f"element-{_ELEMENT_PATTERN_NAMES[element]}" for element in dominant_elements),
        "pattern",
    ]
    base_summary = _first_sentence(summary_source)
    counts = chart.get("ten_god_counts", {})
    if isinstance(counts, dict) and counts:
        groups = {
            "比劫": int(counts.get("比肩", 0) or 0) + int(counts.get("劫财", 0) or 0),
            "食伤": int(counts.get("食神", 0) or 0) + int(counts.get("伤官", 0) or 0),
            "财星": int(counts.get("正财", 0) or 0) + int(counts.get("偏财", 0) or 0),
            "官杀": int(counts.get("正官", 0) or 0) + int(counts.get("七杀", 0) or 0),
            "印星": int(counts.get("正印", 0) or 0) + int(counts.get("偏印", 0) or 0),
        }
        top_groups = sorted(groups.items(), key=lambda item: (-item[1], item[0]))[:3]
        group_text = "、".join(f"{label}{count}" for label, count in top_groups)
        favorable = "".join(str(item) for item in strength_info.get("favorable_elements", []) or []) or "待定"
        net_score = strength_info.get("net_score")
        score_text = f"{float(net_score):g}" if isinstance(net_score, (int, float)) else "待定"
        base_summary = f"{base_summary} 结构侧重{group_text}；喜{favorable}；净评分{score_text}。"
    return {
        "name": str(profile.get("name") or "未命名").strip(),
        "day_master": day_master,
        "day_element": day_element,
        "strength": strength,
        "dominant_elements": dominant_elements,
        "pattern": pattern,
        "summary": base_summary,
        "term_ids": term_ids,
    }


def _element_pattern_html(element: str) -> str:
    pattern_name = _ELEMENT_PATTERN_NAMES.get(element, "unknown")
    return (
        f'<span class="ms-element-pattern ms-identity-pattern-{pattern_name}" '
        f'aria-hidden="true"><i></i><i></i><i></i></span>'
    )


def _strength_position(strength: str) -> int:
    if any(word in strength for word in ("弱", "衰")):
        return 20
    if any(word in strength for word in ("强", "旺")):
        return 80
    return 50


def _render_life_identity_card(model: dict) -> None:
    dominant_html = "".join(
        '<div class="ms-life-dominant-item">'
        f'{_element_pattern_html(element)}<strong>{escape(element)}偏旺</strong>'
        '</div>'
        for element in model["dominant_elements"]
    ) or '<p class="ms-life-no-dominant">五行分布相对均衡</p>'
    strength_position = _strength_position(str(model["strength"]))
    st.markdown(
        '<article class="ms-life-identity-card" aria-label="个人五行身份卡">'
        '<div class="ms-life-identity-grid">'
        '<section class="ms-life-core-mark">'
        '<p class="ms-life-identity-label">日主核心印记</p>'
        '<div class="ms-life-core-content">'
        f'{_element_pattern_html(str(model["day_element"]))}'
        '<div class="ms-life-master-copy">'
        f'<span class="ms-life-master-glyph">{escape(str(model["day_master"]))}</span>'
        f'<strong>{escape(str(model["day_element"]))}日主</strong>'
        f'<small>{escape(str(model["name"]))}</small>'
        '</div></div></section>'
        '<section class="ms-life-identity-details">'
        '<div class="ms-life-strength-block">'
        '<div class="ms-life-detail-heading"><span>日主强弱</span>'
        f'<strong>{escape(str(model["strength"]))}</strong></div>'
        f'<div class="ms-life-strength-scale" role="img" aria-label="日主强弱：{escape(str(model["strength"]))}" '
        f'style="--strength-position: {strength_position}%">'
        '<span class="ms-life-strength-marker"></span></div>'
        '<div class="ms-life-strength-labels"><span>偏弱</span><span>中和</span><span>偏强</span></div>'
        '</div>'
        '<div class="ms-life-dominant-elements">'
        '<p class="ms-life-detail-label">突出五行</p>'
        f'<div>{dominant_html}</div></div>'
        '<div class="ms-life-pattern-line"><span>格局主线</span>'
        f'<strong>{escape(str(model["pattern"]))}</strong></div>'
        f'<p class="ms-life-identity-summary">{escape(str(model["summary"]))}</p>'
        '</section></div></article>',
        unsafe_allow_html=True,
    )


def _render_term_detail(term_id: str, chart: dict | None) -> None:
    view = build_term_detail_view(build_term_view(term_id, chart))
    personal = view.get("personalized")
    personal_html = ""
    if isinstance(personal, dict):
        facts: list[tuple[str, str]] = []
        if "count" in personal:
            facts.extend(
                [
                    ("出现数量", str(personal.get("count", 0))),
                    (
                        "所在位置",
                        "、".join(str(item) for item in personal.get("positions", []))
                        or "原局未见明确落位",
                    ),
                ]
            )
        if "day_master" in personal:
            facts.extend(
                [
                    ("当前日主", str(personal.get("day_master", ""))),
                    ("日主五行", str(personal.get("day_element", ""))),
                ]
            )
        if "current_judgment" in personal:
            facts.append(("当前判断", str(personal.get("current_judgment", ""))))
            facts.append(
                ("喜用元素", "、".join(str(item) for item in personal.get("favorable_elements", [])) or "暂未明确")
            )
            facts.append(
                ("忌神元素", "、".join(str(item) for item in personal.get("unfavorable_elements", [])) or "暂未明确")
            )
        if "distribution" in personal:
            distribution = personal.get("distribution", {})
            readable = (
                "、".join(f"{element}{value}" for element, value in distribution.items())
                if isinstance(distribution, dict)
                else str(distribution)
            )
            facts.append(("五行分布", readable or "暂无分布数据"))
        if "current_pattern" in personal:
            facts.append(("当前格局", str(personal.get("current_pattern", ""))))
        if "related_elements" in personal:
            facts.append(
                ("相关元素", "、".join(str(item) for item in personal.get("related_elements", [])) or "暂未明确")
            )
        if "element_role" in personal:
            facts.append(("五行角色", str(personal.get("element_role", ""))))
        if "favorable_relation" in personal:
            facts.append(("喜忌关系", str(personal.get("favorable_relation", ""))))
        facts_html = "".join(
            f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
            for label, value in facts
        )
        personal_html = (
            '<div class="ms-term-personalized">'
            '<h4>在你的命盘中</h4>'
            '<dl class="ms-term-facts">'
            f'{facts_html}'
            '</dl>'
            f'<p>{escape(str(personal.get("interpretation", "")))}</p>'
            '</div>'
        )
    st.markdown(
        f'<article id="term-detail-{escape(str(view["term_id"]))}" '
        'class="ms-term-detail" aria-live="polite" role="region">'
        f'<p class="ms-term-kicker">当前术语</p><h3>{escape(str(view["label"]))}</h3>'
        f'<p>{escape(str(view["definition"]))}</p>'
        '<div class="ms-term-public-facts">'
        f'<p><strong>观察范围</strong>{escape(str(view["observation_scope"]))}</p>'
        f'<p><strong>理解边界</strong>{escape(str(view["boundary"]))}</p>'
        '</div>'
        f'{personal_html}</article>',
        unsafe_allow_html=True,
    )


def _toggle_term_dictionary(term_id: str) -> None:
    active_term_id = st.session_state.get(_TERM_STATE_KEY)
    transition = transition_term_disclosure(active_term_id, term_id)
    st.session_state[_TERM_STATE_KEY] = transition["active_term_id"]
    if transition["restore_focus_to"]:
        st.session_state[_TERM_FOCUS_RETURN_KEY] = transition["restore_focus_to"]


def _sync_term_button_semantics(
    chips: list[dict],
    *,
    active_term_id: str | None,
    restore_focus_to: str | None,
) -> None:
    """Attach disclosure ARIA attributes to Streamlit's native buttons."""
    semantics = [
        {
            "streamlit_key": f'ms_term_button_{chip["term_id"]}',
            **build_term_disclosure_semantics(
                str(chip["term_id"]),
                active_term_id,
                label=str(chip["label"]),
            ),
        }
        for chip in chips
    ]
    script = f"""
    <script>
    (() => {{
      const items = {json.dumps(semantics, ensure_ascii=False)};
      const focusId = {json.dumps(restore_focus_to, ensure_ascii=False)};
      const sync = () => {{
        items.forEach((item) => {{
          const selector = `[class*="st-key-${{item.streamlit_key}}"] button`;
          const button = window.parent.document.querySelector(selector);
          if (!button) return;
          button.id = item.button_id;
          button.setAttribute("aria-expanded", item.aria_expanded);
          button.setAttribute("aria-controls", item.controls_id);
          button.setAttribute("aria-label", item.accessibility_label);
        }});
        if (focusId) {{
          const button = window.parent.document.getElementById(focusId);
          if (button) button.focus({{ preventScroll: true }});
        }}
      }};
      window.requestAnimationFrame(sync);
      window.setTimeout(sync, 80);
    }})();
    </script>
    """
    with st.container(key="ms-term-accessibility-bridge"):
        st.iframe(script, height=1, width=1, tab_index=-1)


def _render_term_dictionary(term_ids: list[str], chart: dict | None) -> None:
    """用渐进披露与紧凑标签网格展示单开术语详情。"""
    if not term_ids:
        return
    chips: list[dict] = []
    for term_id in term_ids:
        chip = build_term_chip_view(build_term_view(term_id, chart))
        chips.append(chip)

    active_term_id = st.session_state.get(_TERM_STATE_KEY)
    canonical_ids = {str(chip["term_id"]) for chip in chips}
    with st.container(key="ms-term-dictionary"):
        with st.expander(
            f"术语解释 · {len(chips)} 个",
            expanded=active_term_id in canonical_ids,
        ):
            for row_start in range(0, len(chips), 4):
                row = chips[row_start:row_start + 4]
                columns = st.columns(len(row))
                for column, chip in zip(columns, row):
                    canonical_id = str(chip["term_id"])
                    is_active = active_term_id == canonical_id
                    label = f'✓ {chip["label"]}' if is_active else str(chip["label"])
                    with column:
                        st.button(
                            label,
                            key=f"ms_term_button_{canonical_id}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                            on_click=_toggle_term_dictionary,
                            args=(canonical_id,),
                        )
            if active_term_id in canonical_ids:
                _render_term_detail(active_term_id, chart)

    restore_focus_to = st.session_state.pop(_TERM_FOCUS_RETURN_KEY, None)
    _sync_term_button_semantics(
        chips,
        active_term_id=active_term_id,
        restore_focus_to=restore_focus_to,
    )


def _score_to_level(score: int) -> str:
    if score >= 80:
        return "偏强"
    if score >= 65:
        return "中上"
    if score >= 45:
        return "中等"
    if score >= 30:
        return "需经营"
    return "波动较大"


def _clean_score(value, default: int = 50) -> int:
    try:
        return max(0, min(100, int(round(float(value)))))
    except (TypeError, ValueError):
        return default


def _summary_text(data: dict, key: str, fallback: str) -> str:
    if not isinstance(data, dict):
        return fallback
    return str(data.get(f"{key}_summary") or data.get("summary") or fallback).strip()


def _detail_texts(*values: object) -> list[str]:
    """把现有分析字段整理为去重后的详情文本，不生成新的命理结论。"""
    texts: list[str] = []
    for value in values:
        items = value if isinstance(value, (list, tuple)) else [value]
        for item in items:
            text = str(item or "").strip()
            if text and text not in texts:
                texts.append(text)
    return texts


def _build_dimension_views(dp: dict) -> list[dict]:
    scores = dp.get("scores", {}) if isinstance(dp.get("scores"), dict) else {}
    score_details = (
        dp.get("score_details", {}) if isinstance(dp.get("score_details"), dict) else {}
    )
    definitions = [
        {
            "key": "wealth",
            "label": "财富",
            "score_key": "wealth",
            "overview_key": "wealth_overview",
            "summary_key": "wealth",
            "strength_keys": ("wealth_opportunities",),
            "risk_keys": ("wealth_risks",),
            "advice_keys": ("money_management_advice",),
            "fallback": "关注收支节奏、资源配置与风险承受方式。",
        },
        {
            "key": "relationship",
            "label": "关系",
            "score_key": "romance",
            "overview_key": "romance_overview",
            "summary_key": "romance",
            "strength_keys": ("relationship_strengths", "attraction_points"),
            "risk_keys": ("relationship_risks",),
            "advice_keys": ("communication_advice",),
            "fallback": "关注表达、边界与长期相处节奏。",
        },
        {
            "key": "health",
            "label": "健康",
            "score_key": "health_stability",
            "overview_key": "health_overview",
            "summary_key": "health",
            "strength_keys": ("health_strengths",),
            "risk_keys": ("lifestyle_risks", "sensitive_elements"),
            "advice_keys": ("long_term_care_advice",),
            "fallback": "关注日常精力与生活节律，不代替医学判断。",
        },
        {
            "key": "career",
            "label": "事业",
            "score_key": "career",
            "overview_key": "career_overview",
            "summary_key": "career",
            "strength_keys": ("career_strengths",),
            "risk_keys": ("career_risks",),
            "advice_keys": ("long_term_action_advice",),
            "fallback": "关注工作方式、成长路径与现实协作。",
        },
    ]
    views = []
    for definition in definitions:
        score_key = str(definition["score_key"])
        overview = dp.get(str(definition["overview_key"]), {})
        overview = overview if isinstance(overview, dict) else {}
        detail = score_details.get(score_key, {})
        detail = detail if isinstance(detail, dict) else {}
        score = _clean_score(scores.get(score_key, 50))
        strengths = _detail_texts(
            *(overview.get(key) for key in definition["strength_keys"])
        )
        risks = _detail_texts(
            *(overview.get(key) for key in definition["risk_keys"]),
            detail.get("deductions"),
        )
        advice = _detail_texts(
            *(overview.get(key) for key in definition["advice_keys"]),
            detail.get("advice"),
        )
        views.append(
            {
                "key": definition["key"],
                "label": definition["label"],
                "score": score,
                "level": _score_to_level(score),
                "summary": _summary_text(
                    overview,
                    str(definition["summary_key"]),
                    str(definition["fallback"]),
                ),
                "detail_label": "证据",
                "evidence": _detail_texts(overview.get("evidence"), detail.get("evidence")),
                "strengths": strengths
                or ["当前没有单独记录本维度优势，先以证据和现实表现持续观察。"],
                "risks": risks
                or ["当前没有单独记录本维度隐患，仍需结合现实变化持续观察。"],
                "advice": advice
                or ["把本维度作为观察提示，不代替现实信息与专业判断。"],
            }
        )

    balance_score = _clean_score(scores.get("overall_balance", 50))
    core_structure = [
        f'{item["label"]} {item["score"]} 分（{item["level"]}）' for item in views
    ]
    highest_score = max(item["score"] for item in views)
    lowest_score = min(item["score"] for item in views)
    highest = [item for item in views if item["score"] == highest_score]
    lowest = [item for item in views if item["score"] == lowest_score]
    if highest_score == lowest_score:
        balance_strengths = ["四项表现相对均衡。"]
        balance_risks = ["当前没有单独的相对低项，继续结合现实表现观察。"]
    else:
        high_labels = "、".join(str(item["label"]) for item in highest)
        low_labels = "、".join(str(item["label"]) for item in lowest)
        balance_strengths = [
            (
                f'并列最高项为{high_labels}，均为 {highest_score} 分（{highest[0]["level"]}）。'
                if len(highest) > 1
                else f'相对较高项为{high_labels} {highest_score} 分（{highest[0]["level"]}）。'
            )
        ]
        balance_risks = [
            (
                f'并列最低项为{low_labels}，均为 {lowest_score} 分（{lowest[0]["level"]}）。'
                if len(lowest) > 1
                else f'相对需要经营的是{low_labels} {lowest_score} 分（{lowest[0]["level"]}）。'
            )
        ]
    overall_detail = score_details.get("overall_pace", {})
    overall_detail = overall_detail if isinstance(overall_detail, dict) else {}
    views.append(
        {
            "key": "overall_balance",
            "label": "整体平衡",
            "score": balance_score,
            "level": _score_to_level(balance_score),
            "summary": str(
                dp.get("balance_summary")
                or "综合观察财富、关系、健康与事业四项维度的结构协调程度。"
            ),
            "detail_label": "四项结构",
            "evidence": core_structure,
            "strengths": balance_strengths,
            "risks": balance_risks,
            "advice": _detail_texts(overall_detail.get("advice"))
            or ["结合四项表现安排节奏，不以单项分数替代现实判断。"],
        }
    )
    return views


def _render_five_dimension_insights(dp: dict) -> None:
    st.markdown("### 五维洞察")
    dimensions = _build_dimension_views(dp)
    cards = []
    for item in dimensions:
        cards.append(
            '<article class="ms4-dimension-card">'
            f'<p class="ms4-dimension-label">{escape(item["label"])}</p>'
            '<div class="ms4-dimension-score">'
            f'<strong>{item["score"]}</strong><span>/ 100</span></div>'
            f'<p class="ms4-dimension-level">{escape(item["level"])}</p>'
            f'<p class="ms4-dimension-summary">{escape(item["summary"])}</p>'
            '</article>'
        )
    st.markdown(
        f'<div class="ms4-dimension-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )
    for item in dimensions:
        with st.expander(f'查看详情：{item["label"]}', expanded=False):
            sections = [
                (item["detail_label"], item["evidence"]),
                ("优势", item["strengths"]),
                ("隐患", item["risks"]),
                ("建议", item["advice"]),
            ]
            section_html = "".join(
                '<section class="ms4-dimension-detail-section">'
                f'<h4>{escape(str(title))}</h4><ul>'
                + "".join(f'<li>{escape(str(text))}</li>' for text in texts)
                + "</ul></section>"
                for title, texts in sections
            )
            st.markdown(
                f'<div class="ms4-dimension-detail">{section_html}</div>',
                unsafe_allow_html=True,
            )


def _first_or(items: list, index: int, fallback: str) -> str:
    if index < len(items) and str(items[index]).strip():
        return str(items[index]).strip()
    return fallback


def _render_life_insight_cards(dp: dict) -> None:
    strengths = list(dp.get("key_strengths", []) or [])[:3]
    risks = list(dp.get("key_risks", []) or [])[:3]
    advice = list(dp.get("long_term_advice", []) or [])[:3]
    evidence = list(dp.get("evidence", []) or [])
    cards = [
        {
            "index": "01",
            "title": "优势",
            "conclusion": _first_or(strengths, 0, "当前命盘没有特别突出的单项优势。"),
            "why": _first_or(evidence, 0, "这是一项综合观察，仍需结合现实经验持续验证。"),
            "action": "把可复用的方法留下记录，在重要任务中优先调用。",
        },
        {
            "index": "02",
            "title": "隐患",
            "conclusion": _first_or(risks, 0, "当前没有需要特别放大的结构性隐患。"),
            "why": _first_or(evidence, 1, "当前依据有限，先以现实信号和长期变化作为校正。"),
            "action": "为重要选择预留缓冲，用可观察的现实信号及时校正。",
        },
        {
            "index": "03",
            "title": "行动建议",
            "conclusion": _first_or(advice, 0, "先建立稳定节奏，再逐步扩展目标。"),
            "why": "建议综合了上述优势、隐患与五维表现，用于辅助规划而非替你决定。",
            "action": "、".join(str(item).strip() for item in advice[1:] if str(item).strip())
            or "从一个可以在本周完成的小行动开始，完成后再复盘。",
        },
    ]
    html_cards = []
    for card in cards:
        html_cards.append(
            '<article class="ms4-life-insight-card">'
            f'<p class="ms4-insight-index">INSIGHT {card["index"]}</p>'
            f'<h3>{escape(card["title"])}</h3>'
            '<div><span>结论</span>'
            f'<p>{escape(card["conclusion"])}</p></div>'
            '<div><span>为什么</span>'
            f'<p>{escape(card["why"])}</p></div>'
            '<div><span>怎么做</span>'
            f'<p>{escape(card["action"])}</p></div>'
            '</article>'
        )
    st.markdown(
        f'<div class="ms4-life-insight-grid">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def render_life_overview_page():
    """渲染个人命盘总览。"""
    chart = st.session_state.get("current_chart")
    if not chart or chart.get("error"):
        with st.container(key="ms-life-empty"):
            empty_state_header(
                "尚未建立个人命盘",
                "填写出生资料后，即可生成个人摘要与完整命盘。",
            )
            if st.button("开始个人分析", type="primary", use_container_width=True):
                st.session_state["navigate_to"] = "新建命盘"
                st.rerun()
        return
    chart = ensure_bazi_analysis_fields(chart)
    st.session_state["current_chart"] = chart

    profile = chart.get("profile", {})
    luck_data = st.session_state.get("current_luck_data")
    try:
        dp = analyze_life_overview(chart, luck_data)
    except Exception as exc:
        st.error(f"命盘总览生成失败：{exc}")
        return

    with st.container(key="ms-life-overview"):
        page_header(
            "个人命盘",
            f'命盘：{profile.get("name", "未命名")} · {dp["overall_pattern"]}',
            eyebrow="PERSONAL CHART",
        )
        section_header("个人摘要")
        identity_card = _build_life_identity_card(chart, dp)
        _render_life_identity_card(identity_card)
        render_rule_summary(chart)

        evidence = list(dp.get("evidence", []))
        pattern_info = chart.get("pattern_analysis", {})
        if pattern_info.get("pattern"):
            evidence.append(
                f'格局初判：{pattern_info.get("pattern")}，{pattern_info.get("quality", "")}。'
            )
        term_ids = collect_term_ids(
            identity_card["term_ids"],
            [identity_card["summary"], dp.get("overall_pattern", ""), *evidence],
            chart,
        )
        _render_term_dictionary(term_ids, chart)

        render_four_pillars_matrix(chart)
        render_element_distribution(chart)

        with st.container(key="ms-life-next-actions"):
            section_header("下一步建议", "继续查看时间建议，或生成便于阅读的简明报告。")
            advice_col, report_col = st.columns(2)
            with advice_col:
                if st.button("查看今日/年度建议", type="primary", use_container_width=True):
                    st.session_state["navigate_to"] = "今日/年度建议"
                    st.rerun()
            with report_col:
                if st.button("查看简明报告", use_container_width=True):
                    st.session_state["navigate_to"] = "简明报告"
                    st.rerun()

        _render_five_dimension_insights(dp)
        _render_life_insight_cards(dp)

        if evidence:
            with st.expander("命理依据", expanded=False):
                st.markdown("**判断依据**：")
                for item in evidence[:8]:
                    st.markdown(f"- {item}")

        disclaimer = dp.get("health_overview", {}).get("medical_disclaimer", "")
        if disclaimer:
            st.caption(disclaimer)

        st.divider()
        st.caption("本报告基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考。")
