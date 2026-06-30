"""紫微斗数 UI 组件 — v1.2-D-Polish"""

def _join(items):
    return "\u3001".join(items) if items else ""


def render_star_chip(star: str, star_type: str = "main") -> str:
    css = {"main": "zw-main-star", "minor": "zw-minor-star", "fierce": "zw-fierce-star"}
    cls = css.get(star_type, "zw-main-star")
    return f'<span class="zw-star-chip {cls}">{star}</span>'


def render_sihua_chip(sihua: str) -> str:
    css_map = {"\u5316\u7984": "zw-sihua-lu", "\u5316\u6743": "zw-sihua-quan",
               "\u5316\u79d1": "zw-sihua-ke", "\u5316\u5fcc": "zw-sihua-ji"}
    cls = css_map.get(sihua, "zw-sihua-lu")
    return f'<span class="zw-tag {cls}">{sihua}</span>'


def render_keyword_tags(keywords: list[str]) -> str:
    return "".join(f'<span class="zw-keyword">{kw}</span>' for kw in keywords)


def render_boundary_notice(text: str) -> str:
    return f'<div class="zw-boundary">{text}</div>'


def render_palace_card(name: str, branch: str, stars: list, sihua_list: list,
                       is_life: bool = False, is_body: bool = False,
                       placeholder: str = "\u4e3b\u661f\u5f85\u5b8c\u5584") -> str:
    cls = "zw-palace-card"
    if is_life: cls += " life"
    if is_body and not is_life: cls += " body"
    stars_html = "".join(render_star_chip(s) for s in stars) if stars else f'<span style="font-size:10px;color:#B8A894;">{placeholder}</span>'
    sihua_html = "".join(render_sihua_chip(s) for s in sihua_list)
    label = ""
    if is_life: label = '<div style="font-size:10px;color:#B8860B;font-weight:600;">\u2605 \u547d\u5bab</div>'
    elif is_body: label = '<div style="font-size:10px;color:#C49A3C;font-weight:600;">\u2606 \u8eab\u5bab</div>'
    return (
        f'<div class="{cls}">'
        f'<div style="font-size:11px;color:#8C7A64;">{name}</div>'
        f'<div style="font-size:16px;font-weight:700;color:#3D2B1A;">{branch}</div>'
        f'<div style="margin:4px 0;">{stars_html}</div>'
        f'<div>{sihua_html}</div>'
        f'{label}'
        f'</div>'
    )


def render_hero_card(title: str, main_value: str, subtitle: str = "",
                     accent: str = "#B8860B") -> str:
    return (
        f'<div class="zw-hero-card" style="border-color:{accent};">'
        f'<div style="font-size:12px;color:#8C7A64;">{title}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{accent};margin:4px 0;">{main_value}</div>'
        f'<div style="font-size:12px;color:#5C4A32;">{subtitle}</div>'
        f'</div>'
    )


def render_triangle_card(target: str, sanfang: list, duigong: str, summary: str) -> str:
    sanfang_html = "".join(f'<span class="zw-keyword">{s}</span>' for s in sanfang)
    return (
        f'<div class="zw-triangle-card">'
        f'<div style="font-weight:600;color:#3D2B1A;font-size:14px;margin-bottom:6px;">{target}</div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px;">'
        f'<span style="font-size:11px;color:#8C7A64;">\u4e09\u5408\u5bab\uff1a</span>{sanfang_html}'
        f'<span style="font-size:11px;color:#8C7A64;margin-left:8px;">\u5bf9\u5bab\uff1a</span>'
        f'<span class="zw-keyword">{duigong}</span>'
        f'</div>'
        f'<div style="font-size:12px;color:#5C4A32;line-height:1.5;">{summary}</div>'
        f'</div>'
    )


def render_source_card(title: str, text: str) -> str:
    return (
        f'<div style="background:#FAF7F4;border-radius:8px;padding:8px 12px;margin-bottom:4px;'
        f'border:1px solid #EDE6DC;">'
        f'<span style="font-weight:600;color:#3D2B1A;font-size:12px;">{title}</span>'
        f'<span style="color:#5C4A32;font-size:12px;margin-left:6px;">{text}</span>'
        f'</div>'
    )


# ====== 辅星/煞星标签 ======

def render_minor_star_chip(star: str) -> str:
    """辅星标签（藤黄色系）。"""
    return f'<span class="zw-star-chip zw-minor-star">{star}</span>'


def render_fierce_star_chip(star: str) -> str:
    """煞星标签（淡朱砂色系）。"""
    return f'<span class="zw-star-chip zw-fierce-star">{star}</span>'


def render_star_category_chip(star: str, star_type: str = "main") -> str:
    """通用星曜分类标签：main/minor/fierce 分色。"""
    css_map = {"main": "zw-main-star", "minor": "zw-minor-star", "fierce": "zw-fierce-star"}
    cls = css_map.get(star_type, "zw-main-star")
    return f'<span class="zw-star-chip {cls}">{star}</span>'


def render_minor_star_status() -> str:
    return '<span style="font-size:10px;color:#B8A894;">辅星待完善</span>'


def render_fierce_star_status() -> str:
    return '<span style="font-size:10px;color:#C49A7C;">煞星待完善</span>'


def render_no_star_placeholder() -> str:
    return '<span style="font-size:10px;color:#B8A894;">主星未见 / 辅星待完善 / 可结合三方四正观察</span>'


# ====== 大限卡片 ======

def render_daxian_card(stage: dict) -> str:
    """单段大限卡片。"""
    age_range = stage.get("age_range", "")
    palace = stage.get("palace", "")
    branch = stage.get("branch", "")
    main_stars = stage.get("main_stars", [])
    minor_stars = stage.get("minor_stars", [])
    fierce_stars = stage.get("fierce_stars", [])
    summary = stage.get("summary", "")
    boundary = stage.get("boundary", "")

    ms_html = "".join(render_star_chip(s) for s in main_stars) if main_stars else ""
    mis_html = "".join(render_minor_star_chip(s) for s in minor_stars) if minor_stars else ""
    fs_html = "".join(render_fierce_star_chip(s) for s in fierce_stars) if fierce_stars else ""

    return (
        f'<div class="zw-palace-card" style="margin-bottom:8px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-size:14px;font-weight:700;color:#3D2B1A;">{age_range}岁</span>'
        f'<span style="font-size:13px;color:#8C7A64;">{palace}（{branch}）</span>'
        f'</div>'
        f'<div style="margin:4px 0;">{ms_html}</div>'
        f'<div style="margin:2px 0;">'
        + (f'<span style="font-size:11px;color:#8C7A64;">辅星：</span>{mis_html}' if mis_html else "")
        + (f'<span style="font-size:11px;color:#8C7A64;">煞星：</span>{fs_html}' if fs_html else "")
        + f'</div>'
        f'<div style="font-size:12px;color:#5C4A32;line-height:1.5;margin-top:4px;">{summary}</div>'
        f'<div style="font-size:10px;color:#B8A894;margin-top:4px;">{boundary}</div>'
        f'</div>'
    )


# ====== 重点宫位卡片 ======

def render_key_palace_card(palace_name: str, palace_data: dict) -> str:
    """生成重点宫位分析卡片。"""
    theme = palace_data.get("theme", "")
    stars = palace_data.get("main_stars", [])
    sihua = palace_data.get("sihua", [])
    positive = palace_data.get("positive_tendency", "")
    risk = palace_data.get("risk_tendency", "")
    advice = palace_data.get("advice", "")
    branch = palace_data.get("branch", "")

    stars_html = "".join(render_star_chip(s) for s in stars) if stars else ""
    sihua_html = "".join(render_sihua_chip(s) for s in sihua) if sihua else ""

    return (
        f'<div class="zw-palace-card" style="border-left:3px solid #B8860B;margin-bottom:10px;">'
        f'<div style="font-size:15px;font-weight:700;color:#3D2B1A;">{palace_name}</div>'
        f'<div style="font-size:12px;color:#8C7A64;margin:2px 0;">{branch} · {theme}</div>'
        f'<div style="margin:4px 0;">{stars_html} {sihua_html}</div>'
        f'<div style="font-size:12px;color:#5C4A32;margin-top:4px;"><b>正向倾向：</b>{positive}</div>'
        f'<div style="font-size:12px;color:#B85C4A;margin-top:2px;"><b>风险提醒：</b>{risk}</div>'
        f'<div style="font-size:12px;color:#8BA888;margin-top:2px;"><b>行动建议：</b>{advice}</div>'
        f'</div>'
    )


# ====== 三方四正分析卡片 ======

def render_triangle_detail_card(target: str, sanfang: list, duigong: str,
                                main_stars: list, sihua: list, summary: str,
                                opportunity: str, risk: str, advice: str) -> str:
    sanfang_html = "".join(f'<span class="zw-keyword">{s}</span>' for s in sanfang)
    stars_html = "".join(render_star_chip(s) for s in main_stars) if main_stars else ""
    sihua_html = "".join(render_sihua_chip(s) for s in sihua) if sihua else ""

    return (
        f'<div class="zw-triangle-card" style="margin-bottom:10px;">'
        f'<div style="font-weight:700;color:#3D2B1A;font-size:15px;margin-bottom:6px;">{target}</div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px;">'
        f'<span style="font-size:11px;color:#8C7A64;">三合宫：</span>{sanfang_html}'
        f'<span style="font-size:11px;color:#8C7A64;margin-left:8px;">对宫：</span><span class="zw-keyword">{duigong}</span>'
        f'</div>'
        f'<div style="margin:4px 0;">{stars_html} {sihua_html}</div>'
        f'<div style="font-size:12px;color:#5C4A32;line-height:1.5;">{summary}</div>'
        f'<div style="font-size:12px;color:#8BA888;margin-top:4px;"><b>机会：</b>{opportunity}</div>'
        f'<div style="font-size:12px;color:#B85C4A;margin-top:2px;"><b>风险：</b>{risk}</div>'
        f'<div style="font-size:12px;color:#5C4A32;margin-top:2px;"><b>建议：</b>{advice}</div>'
        f'</div>'
    )


# ====== 命盘名片组件 ======

def render_identity_card(main_value: str, subtitle: str = "",
                         accent_color: str = "#B8860B") -> str:
    return (
        f'<div class="zw-hero-card" style="border-color:{accent_color};">'
        f'<div style="font-size:22px;font-weight:700;color:{accent_color};">{main_value}</div>'
        f'<div style="font-size:12px;color:#5C4A32;margin-top:4px;">{subtitle}</div>'
        f'</div>'
    )


# ====== 综合卡片区域 ======

def render_section_header(title: str, subtitle: str = "") -> str:
    return (
        f'<div style="margin:16px 0 8px 0;">'
        f'<div style="font-size:17px;font-weight:700;color:#3D2B1A;">{title}</div>'
        + (f'<div style="font-size:12px;color:#8C7A64;">{subtitle}</div>' if subtitle else "")
        + f'</div>'
    )
