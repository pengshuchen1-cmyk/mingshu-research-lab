"""紫微斗数页面 — v1.2-D-Polish 卡片化"""

from __future__ import annotations

import streamlit as st
from core.ziwei_engine import build_ziwei_chart
from core.ziwei_life_card_engine import analyze_ziwei_life_card
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
)


def _j(items):
    return "、".join(items) if items else ""


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

    t1, t2, t3, t4, t5, t6 = st.tabs(["命盘名片", "十二宫盘", "主星速查", "重点宫位", "三方四正", "参考依据"])

    with t1:
        card = analyze_ziwei_life_card(chart)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(render_hero_card("命宫", chart.get("life_palace",""), "命盘核心"), unsafe_allow_html=True)
        with c2: st.markdown(render_hero_card("身宫", chart.get("body_palace",""), card.get("shen_gong_summary","")[:30]), unsafe_allow_html=True)
        with c3: st.markdown(render_hero_card("命身关系", card.get("ming_shen_relation",""), ""), unsafe_allow_html=True)

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
                    stars = p.get("main_stars", []); shs = sbp.get(sn, [])
                    with cols[j]:
                        st.markdown(render_palace_card(sn, br, stars, shs, is_life, is_body,
                            "主星未显" if ms_ready else "主星待完善"), unsafe_allow_html=True)

    with t3:
        st.markdown("#### 十四主星")
        for star in DETAILED_STAR_EXPLANATIONS:
            s = DETAILED_STAR_EXPLANATIONS[star]
            loc = ""
            for pn, sl in msbp.items():
                if star in sl: loc = f"[{_j(sl)}]"
            with st.expander(f"{star}({s.get('star_type','')}){loc}", expanded=False):
                st.markdown(f'{"".join(render_keyword_tags(s.get("core_keywords",[])))}', unsafe_allow_html=True)
                st.markdown(f"**性格**：{s.get('personality_tendency','')}")
                st.markdown(f"**事业**：{s.get('career_tendency','')}")
        with st.expander("辅星速查（待完善）"):
            for sn, m in MINOR_STAR_MEANINGS.items():
                st.markdown(f"**{sn}**（{m['type']}）：{'、'.join(m['keywords'])} — {m['meaning']}")
        with st.expander("煞星速查（待完善）"):
            for sn, m in FIERCE_STAR_MEANINGS.items():
                st.markdown(f"**{sn}**（{m['type']}）：{'、'.join(m['keywords'])} — {m['meaning']}")

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
            st.markdown(render_triangle_card(name, tri["sanfang"], tri["sizheng"], tri.get("summary","")), unsafe_allow_html=True)
        st.info("当前为基础结构准备，后续将结合辅星、四化、大限流年增强。")

    with t6:
        refs = [("紫微斗数全书","十四主星/十二宫/星曜性质"),("紫微斗数全集","星曜组合/宫位分析"),("紫微斗数大全","十二宫系统"),("传统十二宫体系","命宫/身宫/十二宫位"),("传统四化体系","化禄权科忌")]
        for t, u in refs: st.markdown(render_source_card(t, u), unsafe_allow_html=True)
        st.divider()
        st.markdown("**完成度**")
        items = [("命宫/身宫定位",True),("十二宫位",True),("十四主星落宫",True),("生年四化",True),("三方四正结构",True),("辅星数据结构",True),("煞星数据结构",True),("辅星落宫算法",False),("煞星落宫算法",False),("大限流年",False),("飞化",False)]
        for name, ok in items:
            st.markdown(f'- {"✅" if ok else "❌"} {name}')
        st.divider()
        st.warning("当前内容基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。")
