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
