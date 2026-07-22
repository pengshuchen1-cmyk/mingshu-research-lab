"""紫微斗数页面 — v1.2-D-Polish 卡片化"""

from __future__ import annotations

import streamlit as st
from core.ziwei_engine import build_ziwei_chart
from core.ziwei_algorithm_audit import audit_ziwei_algorithms
from core.ziwei_life_card_engine import analyze_ziwei_life_card
from core.ziwei_readable_engine import build_ziwei_capability_review, build_ziwei_plain_guide
from core.ziwei_star_combination_engine import load_star_combination_rules
from core.ziwei_triangle_engine import get_sanfang_sizheng
from core.ziwei_sihua_engine import get_sihua_by_year_gan, apply_sihua_to_chart
from core.ziwei_star_engine import get_year_gan_from_profile
from core.ziwei_constants import (
    DETAILED_STAR_EXPLANATIONS, PALACE_EXPLANATIONS, DETAILED_PALACE_EXPLANATIONS,
    PALACE_NAMES, MINOR_STAR_MEANINGS, FIERCE_STAR_MEANINGS,
)
from ui.ziwei_components import (
    render_hero_card, render_palace_card, render_star_chip,
    render_sihua_chip, render_keyword_tags, render_boundary_notice,
    render_triangle_card, render_source_card,
    render_minor_star_chip, render_fierce_star_chip,
    render_star_category_chip, render_daxian_card,
    render_key_palace_card, render_triangle_detail_card,
    render_section_header, render_identity_card,
)


def _j(items):
    return "、".join(items) if items else ""


def _render_plain_language_entry(card: dict, chart: dict) -> None:
    """给不熟悉紫微斗数的用户一个白话入口。"""
    life_palace = chart.get("life_palace", "")
    body_palace = chart.get("body_palace", "")
    st.markdown(render_section_header("先看这张紫微名片", "不用先背术语，先抓住命宫、身宫和几个重点宫位。"), unsafe_allow_html=True)
    st.markdown(
        render_boundary_notice(
            f"命宫像性格底盘，先看一个人平常怎么做选择；身宫像后天用力方向，"
            f"看成年后更愿意把力气花在哪里。当前命宫在{life_palace}，身宫在{body_palace}。"
            "当前版本不会把未确认算法包装成结论，未完成的飞化和紫微流年会明确标注。"
        ),
        unsafe_allow_html=True,
    )
    if card.get("profile_keywords"):
        st.markdown("".join(render_keyword_tags(card.get("profile_keywords", [])[:6])), unsafe_allow_html=True)


def _render_plain_focus_cards(card: dict) -> None:
    """把重点宫位转成更好懂的生活语言。"""
    st.markdown(render_section_header("重点先看", "这几张卡片对应普通人最关心的事业、钱、关系和身心状态。"), unsafe_allow_html=True)
    name_map = {
        "官禄宫": ("事业怎么发力", "看工作方向、职位责任、适合专业路线还是管理路线。"),
        "财帛宫": ("钱从哪里来", "看收入方式、金钱观、资源承接和花钱压力。"),
        "夫妻宫": ("关系怎么相处", "看伴侣类型、亲密关系模式和合作边界。"),
        "迁移宫": ("外部机会", "看出差、异地、换环境、对外发展是否更有推动力。"),
        "福德宫": ("内在电量", "看精神状态、恢复能力、兴趣享受和长期幸福感。"),
        "疾厄宫": ("身心提醒", "只做生活状态提醒，不做医学诊断。"),
    }
    summaries = card.get("key_palace_summaries", {})
    focus_names = ["官禄宫", "财帛宫", "夫妻宫", "迁移宫", "福德宫", "疾厄宫"]
    for start in range(0, len(focus_names), 3):
        cols = st.columns(3)
        for col, palace_name in zip(cols, focus_names[start : start + 3]):
            title, guide = name_map.get(palace_name, (palace_name, ""))
            text = summaries.get(palace_name, guide)
            with col:
                st.markdown(
                    f'<div class="zw-hero">'
                    f'<div style="font-size:14px;font-weight:700;color:#3D2B1A;">{title}</div>'
                    f'<div style="font-size:11px;color:#8C7A64;margin:2px 0 8px;">{palace_name}</div>'
                    f'<div style="font-size:12px;color:#5C4A32;line-height:1.65;">{text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


def _render_plain_manual(guide: dict) -> None:
    """渲染普通用户能看懂的紫微说明书。"""
    st.markdown(render_section_header("命盘说明书", "先看这五个位置：命宫、身宫、事业宫、财帛宫、夫妻宫。"), unsafe_allow_html=True)
    st.caption(guide.get("summary", ""))
    for card in guide.get("focus_cards", []):
        title = card.get("title", "")
        plain_title = card.get("plain_title", "")
        stars = card.get("main_stars", [])
        sihua = card.get("sihua", [])
        with st.expander(f"{title}｜{plain_title}", expanded=title in {"命宫说明", "事业宫说明"}):
            top_col, star_col = st.columns([2, 1])
            with top_col:
                st.markdown(f"**一句话先懂**：{card.get('one_sentence', '')}")
                st.markdown(f"**它是什么意思**：{card.get('what_it_means', '')}")
                st.markdown(f"**生活里怎么看（现实里怎么看）**：{card.get('real_world_view', '')}")
                examples = card.get("life_examples", [])
                if examples:
                    st.markdown("**现实例子**：" + "；".join(examples[:3]))
                st.markdown(f"**可以怎么做**：{card.get('action_advice', '')}")
                st.markdown(f"**应该注意什么**：{card.get('what_to_notice', '')}")
                st.caption(f"边界提醒：{card.get('boundary_note', '')}")
            with star_col:
                st.markdown("**本宫信号**")
                st.write(f"宫位：{card.get('actual_palace_name', '')}｜地支：{card.get('branch', '') or '待确认'}")
                if stars:
                    st.markdown("".join(render_star_chip(s) for s in stars), unsafe_allow_html=True)
                else:
                    st.caption("本宫未见十四主星，可结合对宫和三方四正观察。")
                if sihua:
                    st.markdown("".join(render_sihua_chip(s) for s in sihua), unsafe_allow_html=True)

            st.markdown(f"**星曜组合**：{card.get('star_combination_text', '')}")
            star_palace_items = card.get("star_palace_explanations", [])
            if star_palace_items:
                st.markdown("**主星落宫怎么看**")
                for item in star_palace_items:
                    st.markdown(f"- **{item.get('title', '')}**：{item.get('plain_text', '')}")
                    st.caption(f"{item.get('sihua_text', '')}｜边界提醒：{item.get('boundary', '')}")
            if card.get("palace_focus"):
                st.markdown(f"**命盘依据**：{card.get('palace_focus', '')}")
            risk = card.get("risk_tendencies", [])
            if risk:
                st.warning("、".join(risk))
    st.markdown(render_boundary_notice(guide.get("boundary", "")), unsafe_allow_html=True)


def _render_capability_review(review: dict) -> None:
    """渲染紫微模块算法完成度说明。"""
    st.markdown(render_section_header("算法完成度说明", "先说明哪些内容已接入，哪些只作辅助参考，哪些暂未接入。"), unsafe_allow_html=True)
    rows = []
    for item in review.get("items", []):
        rows.append({
            "项目": item.get("name", ""),
            "当前状态": item.get("status", ""),
            "普通理解": item.get("user_text", ""),
            "边界提醒": item.get("boundary", ""),
        })
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown(render_boundary_notice(review.get("boundary", "")), unsafe_allow_html=True)


def _render_algorithm_audit() -> None:
    """把紫微算法复核报告展示给普通用户。"""
    audit = audit_ziwei_algorithms()
    summary = audit.get("summary", {})

    st.markdown(render_section_header("紫微算法复核", "把五行局、十四主星、辅星/煞星和大限的当前校验状态放在这里。"), unsafe_allow_html=True)
    st.caption("这页只说明算法链路和校验状态，不新增断语，也不把仍需验证的内容包装成结论。")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("已登记盘例", summary.get("known_cases", 0))
    with c2:
        st.metric("盘面通过", summary.get("chart_passed_cases", 0))
    with c3:
        st.metric("需继续复核", summary.get("chart_review_cases", 0))

    resolved = summary.get("resolved_issues", [])
    if resolved:
        st.success("已查清的问题：" + "；".join(resolved))
    st.markdown(render_boundary_notice(summary.get("boundary", "仍需真实盘例继续校验。")), unsafe_allow_html=True)

    five = audit.get("five_element_review", {})
    with st.expander("五行局复核", expanded=True):
        st.markdown(f"**当前状态**：{five.get('status', '待复核')}")
        st.markdown(f"**推算方法**：{five.get('method', '')}")
        traces = five.get("traces", [])
        if traces:
            st.dataframe(
                [{
                    "样例": item.get("case_id", ""),
                    "命宫干支": item.get("life_palace_stem_branch", ""),
                    "实际五行局": item.get("actual", ""),
                    "预期五行局": item.get("expected", ""),
                    "结果": item.get("status", ""),
                } for item in traces],
                use_container_width=True,
                hide_index=True,
            )
        st.caption(five.get("boundary", "仍需真实盘例继续校验。"))

    main_star = audit.get("main_star_review", {})
    with st.expander("十四主星复核", expanded=False):
        st.markdown(f"**当前状态**：{main_star.get('status', '待复核')}")
        st.markdown(f"**推算链路**：{main_star.get('method', '')}")
        st.write(f"已校验样例：{main_star.get('checked_cases', 0)}")
        failed = main_star.get("failed_checks", [])
        if failed:
            st.warning("需复核项：" + "；".join(str(item) for item in failed))
        else:
            st.success("当前已登记盘例未发现十四主星落宫冲突。")
        st.caption(main_star.get("boundary", "仍需真实盘例继续校验。"))

    minor_fierce = audit.get("minor_fierce_review", {})
    with st.expander("辅星/煞星复核", expanded=False):
        rows = [
            {"项目": "辅星", "状态": "已接入" if minor_fierce.get("minor_ready") else "需完善"},
            {"项目": "煞星", "状态": "已接入" if minor_fierce.get("fierce_ready") else "需完善"},
            {"项目": "年干", "状态": minor_fierce.get("year_gan", "")},
            {"项目": "年支", "状态": minor_fierce.get("year_branch", "")},
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown(f"**当前状态**：{minor_fierce.get('status', '待复核')}")
        st.caption(minor_fierce.get("note", "辅星、煞星仍需真实盘例继续校验。"))

    daxian = audit.get("daxian_review", {})
    with st.expander("大限复核", expanded=False):
        rows = [
            {"项目": "大限结构", "状态": "已接入" if daxian.get("daxian_ready") else "需完善"},
            {"项目": "起运年龄", "状态": daxian.get("start_age", "")},
            {"项目": "阶段数量", "状态": daxian.get("stage_count", "")},
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown(f"**当前状态**：{daxian.get('status', '待复核')}")
        st.caption(daxian.get("note", "大限仍需真实盘例继续校验。"))


def render_ziwei_page():
    profile = st.session_state.get("current_profile", {})
    if not profile:
        st.info("请先在新建命盘页面生成命盘。"); return
    chart = build_ziwei_chart(profile)
    if not chart.get("available"):
        st.warning(chart.get("message", "紫微斗数基础盘暂不可用。")); return

    palaces = chart.get("palaces", [])
    msbp = chart.get("main_stars_by_palace", {})
    ms_ready = chart.get("main_stars_ready", False)
    yg = get_year_gan_from_profile(profile)
    sihua = apply_sihua_to_chart(chart, get_sihua_by_year_gan(yg))
    sbp = sihua.get("sihua_by_palace", {})
    chart["sihua_by_palace"] = sbp

    st.title("紫微斗数")
    st.caption("先看白话名片，再看十二宫和星曜细节。复杂名词都会尽量转成生活里的表达。")

    t1, t2, t3, t4, t5, t6, t7 = st.tabs(["先看结论", "十二宫地图", "星曜速查", "重点宫位", "三方四正", "算法复核", "参考依据"])

    with t1:
        card = analyze_ziwei_life_card(chart)
        guide = build_ziwei_plain_guide(chart, sbp)
        capability_review = build_ziwei_capability_review(chart)
        _render_plain_language_entry(card, chart)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(render_hero_card("命宫", chart.get("life_palace",""), "命盘核心"), unsafe_allow_html=True)
        with c2: st.markdown(render_hero_card("身宫", chart.get("body_palace",""), card.get("shen_gong_summary","")[:30]), unsafe_allow_html=True)
        with c3: st.markdown(render_hero_card("命身关系", card.get("ming_shen_relation",""), ""), unsafe_allow_html=True)

        _render_plain_manual(guide)
        _render_plain_focus_cards(card)
        _render_capability_review(capability_review)

        st.divider()
        col_w, col_r, col_h = st.columns(3)
        for col, name in [(col_w, "命宫"), (col_h, "财帛宫"), (col_r, "官禄宫")]:
            stars = msbp.get(name, [])
            detail = DETAILED_PALACE_EXPLANATIONS.get(name, {})
            pos = _j(detail.get("positive_tendencies", [])[:2]) if detail else ""
            with col:
                st.markdown(f'<div class="zw-hero"><div style="font-weight:600;color:#3D2B1A;font-size:14px;margin-bottom:4px;">{name}</div>{"".join(render_star_chip(s) for s in stars)}<div style="font-size:11px;color:#5C4A32;margin-top:4px;">{pos}</div></div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        for col, name in [(col1, "夫妻宫"), (col2, "福德宫"), (col3, "迁移宫")]:
            detail = DETAILED_PALACE_EXPLANATIONS.get(name, {})
            pos = _j(detail.get("positive_tendencies", [])[:1]) if detail else ""
            with col:
                st.markdown(f'<div class="zw-hero" style="border-color:#EDE6DC;"><div style="font-weight:600;color:#5C4A32;font-size:13px;">{name}</div><div style="font-size:11px;color:#8C7A64;">{pos}</div></div>', unsafe_allow_html=True)

        st.divider()
        if sbp:
            st.markdown("#### 四化")
            for pn, shs in sbp.items():
                chips = "".join(render_sihua_chip(s) for s in shs)
                st.markdown(f'<span style="font-size:12px;color:#5C4A32;">{pn}：</span>{chips}', unsafe_allow_html=True)

        st.divider()
        st.markdown(render_boundary_notice(card.get("module_boundary","版本说明：当前包含十四主星落宫、生年四化、三方四正基础。辅星、煞星、大限流年、飞化仍在后续完善。")), unsafe_allow_html=True)

    with t2:
        for i in range(0, 12, 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(palaces):
                    p = palaces[i+j]
                    sn = p.get("name",""); br = p.get("branch","")
                    is_life = p.get("is_life_palace"); is_body = p.get("is_body_palace")
                    stars = p.get("main_stars", [])
                    minor_stars = p.get("minor_stars", [])
                    fierce_stars = p.get("fierce_stars", [])
                    shs = sbp.get(sn, [])
                    # Build star display with categories
                    stars_html = ""
                    if stars:
                        stars_html = "".join(render_star_chip(s) for s in stars)
                    if minor_stars:
                        stars_html += "".join(render_minor_star_chip(s) for s in minor_stars)
                    if fierce_stars:
                        stars_html += "".join(render_fierce_star_chip(s) for s in fierce_stars)
                    if not stars_html:
                        stars_html = '<span style="font-size:10px;color:#B8A894;">主星未见 / 辅星待完善</span>'
                    sihua_html = "".join(render_sihua_chip(s) for s in shs)
                    label = ""
                    if is_life:
                        label = '<div style="font-size:10px;color:#B8860B;font-weight:600;">★ 命宫</div>'
                    elif is_body:
                        label = '<div style="font-size:10px;color:#C49A3C;font-weight:600;">☆ 身宫</div>'
                    palace_theme = DETAILED_PALACE_EXPLANATIONS.get(sn, {}).get("palace_theme", "") if sn in DETAILED_PALACE_EXPLANATIONS else ""
                    with cols[j]:
                        st.markdown(
                            f'<div class="zw-palace-card">'
                            f'<div style="font-size:11px;color:#8C7A64;">{sn}</div>'
                            f'<div style="font-size:16px;font-weight:700;color:#3D2B1A;">{br}</div>'
                            f'<div style="margin:4px 0;">{stars_html}</div>'
                            f'<div>{sihua_html}</div>'
                            f'{label}'
                            f'<div style="font-size:10px;color:#B8A894;margin-top:2px;">{palace_theme}</div>'
                            f'</div>', unsafe_allow_html=True)

    with t3:
        stars_tabs = st.tabs(["十四主星", "常见组合", "辅星", "煞星"])
        with stars_tabs[0]:
            for star in DETAILED_STAR_EXPLANATIONS:
                s = DETAILED_STAR_EXPLANATIONS[star]
                loc = ""
                for pn, sl in msbp.items():
                    if star in sl: loc = f"[{pn}]"
                with st.expander(f"{star}（{s.get('star_type','')}）{loc}", expanded=False):
                    st.markdown(f'{"".join(render_keyword_tags(s.get("core_keywords",[])))}', unsafe_allow_html=True)
                    st.markdown(f"**性格倾向**：{s.get('personality_tendency','')}")
                    st.markdown(f"**事业倾向**：{s.get('career_tendency','')}")
                    st.markdown(f"**财富倾向**：{s.get('wealth_tendency','')}")
                    st.markdown(f"**关系倾向**：{s.get('relationship_tendency','')}")
                    st.markdown(f"**风险提醒**：{s.get('risk_warning','')}")
        with stars_tabs[1]:
            combo_rules = load_star_combination_rules()
            st.caption("这里展示常见双星组合的白话解释。若你的命盘某宫出现对应组合，说明书会优先引用这些组合规则。")
            for rule in combo_rules.get("rules", []):
                with st.expander(rule.get("title", "星曜组合"), expanded=rule.get("id") in {"ziwei_tianfu", "wuqu_qisha", "taiyang_taiyin"}):
                    st.markdown("".join(render_star_chip(s) for s in rule.get("stars", [])), unsafe_allow_html=True)
                    st.markdown(f"**组合意思**：{rule.get('plain_meaning', '')}")
                    st.markdown(f"**现实表现**：{rule.get('real_world_view', '')}")
                    st.markdown(f"**优势**：{'、'.join(rule.get('strengths', []))}")
                    st.markdown(f"**风险**：{'、'.join(rule.get('risks', []))}")
                    st.info(rule.get("advice", ""))
        with stars_tabs[2]:
            for sn, m in MINOR_STAR_MEANINGS.items():
                loc = ""
                for pn, sl in chart.get("minor_stars_by_palace", {}).items():
                    if sn in sl: loc = f"[{pn}]"
                if loc:
                    st.markdown(render_source_card(f"{loc} {sn}", f"{m['type']}：{'、'.join(m['keywords'])} — {m['meaning']}"), unsafe_allow_html=True)
                else:
                    fill = "落宫算法待完善，当前仅展示星曜含义。"
                    st.markdown(render_source_card(sn, f"{m['type']}：{'、'.join(m['keywords'])} — {m['meaning']}<br><span style='font-size:10px;color:#B8A894;'>{fill}</span>"), unsafe_allow_html=True)
        with stars_tabs[3]:
            for sn, m in FIERCE_STAR_MEANINGS.items():
                loc = ""
                for pn, sl in chart.get("fierce_stars_by_palace", {}).items():
                    if sn in sl: loc = f"[{pn}]"
                if loc:
                    st.markdown(render_source_card(f"{loc} {sn}", f"{m['type']}：{'、'.join(m['keywords'])} — {m['meaning']}"), unsafe_allow_html=True)
                else:
                    fill = "落宫算法待完善，当前仅展示星曜含义。"
                    st.markdown(render_source_card(sn, f"{m['type']}：{'、'.join(m['keywords'])} — {m['meaning']}<br><span style='font-size:10px;color:#B8A894;'>{fill}</span>"), unsafe_allow_html=True)

    with t4:
        for name in ["命宫", "财帛宫", "官禄宫", "夫妻宫", "疾厄宫", "福德宫", "迁移宫"]:
            br = ""; stars = []; shs = []
            for p in palaces:
                if p.get("name") == name: br = p.get("branch","")
            stars = msbp.get(name, []); shs = sbp.get(name, [])
            detail = DETAILED_PALACE_EXPLANATIONS.get(name, {})
            with st.expander(name, expanded=(name=="命宫")):
                st.markdown(f'<span style="font-size:13px;color:#5C4A32;">{name}落{br}支</span>', unsafe_allow_html=True)
                st.markdown("".join(render_star_chip(s) for s in stars) + "".join(render_sihua_chip(s) for s in shs), unsafe_allow_html=True)
                if detail:
                    pos = detail.get("positive_tendencies",[]); rsk = detail.get("risk_tendencies",[])
                    if pos: st.markdown(f"**优势**：{'、'.join(pos)}")
                    if rsk: st.markdown(f"**注意**：{'、'.join(rsk)}")
                    st.info(detail.get("advice",""))

    with t5:
        for name in ["命宫", "财帛宫", "官禄宫", "夫妻宫"]:
            tri = get_sanfang_sizheng(name, chart)
            ms = chart.get("main_stars_by_palace", {}).get(name, [])
            shs = sbp.get(name, [])
            st.markdown(render_triangle_detail_card(
                name, tri["sanfang"], tri["sizheng"],
                ms, shs, tri.get("summary",""),
                tri.get("opportunity",""), tri.get("risk",""), tri.get("advice","")
            ), unsafe_allow_html=True)
            st.markdown(
                f'<div class="zw-readable-text" style="margin:-4px 0 10px 0;">'
                f'{tri.get("plain_explanation", "")}</div>',
                unsafe_allow_html=True,
            )
            for item in tri.get("relation_cards", []):
                stars = "".join(render_star_chip(s) for s in item.get("main_stars", []))
                sihua_html = "".join(render_sihua_chip(s) for s in item.get("sihua", []))
                st.markdown(
                    f'<div class="zw-triangle-card">'
                    f'<div class="zw-triangle-role">{item.get("role", "")}｜{item.get("palace", "")}</div>'
                    f'<div class="zw-readable-text" style="font-weight:650;margin:4px 0;">{item.get("life_area", "")}</div>'
                    f'<div>{stars}{sihua_html}</div>'
                    f'<p>{item.get("plain_text", "")}</p>'
                    f'<p class="zw-triangle-muted">{item.get("star_text", "")}</p>'
                    f'<p><b>机会：</b>{item.get("opportunity", "")}</p>'
                    f'<p><b>注意：</b>{item.get("risk", "")}</p>'
                    f'<p><b>建议：</b>{item.get("advice", "")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.caption(f"参考依据：{tri.get('basis', '')}")
        # 大限基础结构
        daxian = chart.get("daxian", {})
        if daxian.get("daxian_ready"):
            st.divider()
            st.markdown("#### 大限基础结构")
            for stage in daxian.get("stages", []):
                st.markdown(render_daxian_card(stage), unsafe_allow_html=True)
            st.info(daxian.get("basis",""))
        else:
            st.info("当前为基础结构准备，后续将结合辅星、四化、大限流年增强。")

    with t6:
        _render_algorithm_audit()

    with t7:
        st.markdown("#### 参考典籍")
        refs = [
            ("《紫微斗数全书》","十四主星/十二宫/星曜性质/安星法"),
            ("《紫微斗数全集》","星曜组合/宫位分析/生年四化"),
            ("《紫微斗数大全》","十二宫系统/三方四正"),
            ("传统十二宫体系","命宫/身宫/十二宫位"),
            ("传统四化体系","化禄/化权/化科/化忌"),
        ]
        for t, u in refs:
            st.markdown(render_source_card(t, u), unsafe_allow_html=True)
        
        st.divider()
        _render_capability_review(build_ziwei_capability_review(chart))
        st.divider()
        
        st.markdown("#### 参考依据")
        st.markdown(render_boundary_notice(
            "当前紫微模块已包含：十四主星落宫、生年四化、三方四正基础结构、辅星落宫（文昌/文曲/左辅/右弼）、"
            "煞星落宫（擎羊/陀罗/火星/铃星/地空/地劫）、大限基础结构。"
            "尚未包含：辅星四化、飞化、紫微流年流月。"
        ), unsafe_allow_html=True)
        
        st.warning("当前内容基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。")
