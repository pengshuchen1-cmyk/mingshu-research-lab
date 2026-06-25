"""紫微斗数页面 —— 4×3 网格宫位卡片 + 新手指南。"""

from __future__ import annotations

import pandas as pd

from core.ziwei_engine import build_ziwei_chart
from core.ziwei_constants import PALACE_NAMES
from report.ziwei_report import generate_ziwei_report


def render_ziwei_page() -> None:
    """渲染紫微斗数页面。"""
    import streamlit as st
    from core.ziwei_constants import ZWDS_GUIDE, STAR_MEANINGS, STAR_GROUPS

    profile = st.session_state.get("current_profile", {})
    if not profile:
        st.info("请先在新建命盘页面生成命盘，或从命盘档案中加载一个命盘。")
        return

    result = build_ziwei_chart(profile)
    if not result.get("available"):
        st.warning(result.get("message", "紫微斗数基础盘暂不可用。"))
        return

    # ★ 新手入门指南（实用解读说明）
    with st.expander("📖 快速看懂紫微斗数 · 新手入门指南", expanded=True):
        st.markdown(ZWDS_GUIDE)
        st.markdown(
            '<div style="background:linear-gradient(135deg,#3D2B1A 0%,#5C4A32 100%);'
            'border-radius:12px;padding:20px;margin:12px 0;">'
            '<div style="color:#FCF8F0;font-size:14px;font-weight:600;margin-bottom:10px;">'
            '📌 简单看懂一张命盘的步骤</div>'
            '<ol style="color:#D4C5B0;font-size:13px;line-height:1.8;margin:0;padding-left:20px;">'
            '<li><b>第一眼：看命宫地支</b> —— 命宫落在哪个地支?决定命盘的基本倾向。</li>'
            '<li><b>看身宫</b> —— 身宫代表后天努力方向，与命宫互补。</li>'
            '<li><b>看十二宫分布</b> —— 每个宫位代表生活的一个领域?注意对宫影响。</li>'
            '<li><b>参考主星说明</b> —— 了解十四主星的基础含义。</li>'
            '<li><b>交叉验证</b> —— 结合八字喜用神、大运流年一起看更准确。</li>'
            '</ol></div>',
            unsafe_allow_html=True,
        )

    # 十四主星含义速查
    with st.expander("⭐ 十四主星含义速查"):
        stars_html = ""
        for star, meaning in STAR_MEANINGS.items():
            groups = []
            for g, members in STAR_GROUPS.items():
                if star in members:
                    groups.append(g)
            tag = " \u00b7 ".join(groups) if groups else "\u4e2d\u5929"
            stars_html += (
                '<div style="display:flex;padding:6px 0;border-bottom:1px solid #EDE6DC;">'
                f'<span style="font-weight:700;color:#3D2B1A;width:60px;flex-shrink:0;">{star}</span>'
                f'<span style="color:#8C7A64;width:90px;font-size:12px;">{tag}</span>'
                f'<span style="color:#5C4A32;font-size:13px;">{meaning}</span></div>'
            )
        st.markdown(stars_html, unsafe_allow_html=True)

    # 命宫/身宫指标卡
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:16px 20px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);'
            f'text-align:center;border:2px solid #B8860B;">'
            f'<div style="font-size:12px;color:#8C7A64;margin-bottom:4px;">\u547d\u5bab</div>'
            f'<div style="font-size:22px;font-weight:700;color:#B8860B;">{result.get("life_palace", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div style="background:#FAF7F4;border-radius:10px;padding:16px 20px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);'
            f'text-align:center;">'
            f'<div style="font-size:12px;color:#8C7A64;margin-bottom:4px;">\u8eab\u5bab</div>'
            f'<div style="font-size:22px;font-weight:700;color:#3D2B1A;">{result.get("body_palace", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 12 宫位 4x3 网格卡片
    st.markdown("## \u7d2b\u5fae\u6597\u6570")
    st.markdown("### \u5341\u4e8c\u5bab\u4f4d \u00b7 \u70b9\u51fb\u67e5\u770b\u5bab\u4f4d\u8bf4\u660e")
    palaces = result.get("palaces", [])
    for i in range(0, 12, 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(palaces):
                p = palaces[i + j]
                is_life = p.get("is_life_palace")
                is_body = p.get("is_body_palace")
                border_style = "border:2px solid #B8860B;" if is_life else "border:1px solid #EDE6DC;"
                palace_name = p.get("name", "")
                branch = p.get("branch", "")
                explanation = p.get("explanation", "")
                with cols[j]:
                    st.markdown(
                        f'<div style="background:#FAF7F4;border-radius:10px;padding:10px 6px;'
                        f'text-align:center;{border_style}box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
                        f'<div style="font-size:11px;color:#8C7A64;margin-bottom:1px;">{palace_name}</div>'
                        f'<div style="font-size:15px;font-weight:700;color:#3D2B1A;margin:2px 0;'
                        f'font-family:\'Noto Serif SC\',serif;">{branch}</div>'
                        f'<div style="font-size:10px;color:#8C7A64;line-height:1.3;">'
                        f'{explanation[:25]}{"..." if len(explanation) > 25 else ""}</div>'
                        f'<div style="font-size:10px;color:#B8A894;margin-top:3px;">\u4e3b\u661f: \u5f85\u5b8c\u5584</div>'
                        + ('<div style="font-size:10px;color:#B8860B;margin-top:2px;font-weight:600;">\u2605 \u547d\u5bab</div>' if is_life else '')
                        + ('<div style="font-size:10px;color:#8C7A64;margin-top:2px;">\u2606 \u8eab\u5bab</div>' if is_body and not is_life else '')
                        + '</div>',
                        unsafe_allow_html=True,
                    )
                    # 宫位说明弹窗
                    with st.popover(f"📖 {palace_name}"):
                        opp = PALACE_NAMES[(PALACE_NAMES.index(palace_name) + 6) % 12]
                        st.markdown(
                            f"**{palace_name}**\uff08\u5730\u652f\uff1a{branch}\uff09  "
                            f"\n\n{explanation}  "
                            f"\n\n💡 **\u770b\u76d8\u63d0\u793a**\uff1a\u5bf9\u5bab\u662f**{opp}**\uff0c\u4e24\u5bab\u4e92\u76f8\u5f71\u54cd\u3002"
                        )

    # 十二宫位数据表
    with st.expander("📋 \u67e5\u770b\u5bab\u4f4d\u8be6\u7ec6\u4fe1\u606f"):
        rows = [
            {
                "\u5bab\u4f4d": p.get("name", ""),
                "\u5730\u652f": p.get("branch", ""),
                "\u547d\u5bab": "\u2605" if p.get("is_life_palace") else "",
                "\u8eab\u5bab": "\u2606" if p.get("is_body_palace") else "",
                "\u4e3b\u661f": "\u5f85\u5b8c\u5584",
                "\u57fa\u7840\u542b\u4e49": p.get("explanation", ""),
            }
            for p in palaces
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # 紫微基础报告
    report = generate_ziwei_report(result)
    st.markdown("### \u7d2b\u5fae\u57fa\u7840\u62a5\u544a")
    for item in report.get("sections", []):
        with st.expander(item.get("title", ""), expanded=item.get("title") == "\u547d\u5bab\u5206\u6790"):
            st.markdown(item.get("text", ""))
