"""命数研究室 · 全局 CSS 设计系统

所有页面的统一设计语言：淡雅东方调。
基底 #F5F0EB，卡片 #FAF7F4，墨色 #3D2B1A，藤黄 #B8860B。
"""

# ——— 五行色值 ———
ELEMENT_COLORS = {
    "木": "#8BA888",
    "火": "#B85C4A",
    "土": "#C4A882",
    "金": "#D4A843",
    "水": "#7A9BAE",
}

ELEMENT_EMOJIS = {
    "木": "🌳",
    "火": "🔥",
    "土": "⛰️",
    "金": "⚔️",
    "水": "💧",
}

ELEMENT_METADATA = {
    "木": {"tian_gan": "甲乙", "direction": "东", "season": "春"},
    "火": {"tian_gan": "丙丁", "direction": "南", "season": "夏"},
    "土": {"tian_gan": "戊己", "direction": "中", "season": "季末"},
    "金": {"tian_gan": "庚辛", "direction": "西", "season": "秋"},
    "水": {"tian_gan": "壬癸", "direction": "北", "season": "冬"},
}


def get_global_css() -> str:
    """返回完整的全局 CSS 字符串，在 app.py 入口注入。"""
    return """
    /* ===== 基础重置 ===== */
    #root, .stApp, .main > div {
        background-color: #F5F0EB !important;
        font-family: 'Noto Sans SC', 'PingFang SC', -apple-system, sans-serif;
        color: #3D2B1A;
    }

    /* ===== 标题 ===== */
    h1, h2, h3 {
        font-family: 'Noto Serif SC', serif;
        color: #3D2B1A !important;
    }
    h1 {
        font-size: 28px !important;
        letter-spacing: 3px;
        font-weight: 700 !important;
    }
    h2 {
        font-size: 20px !important;
        letter-spacing: 2px;
        margin-top: 28px !important;
        margin-bottom: 12px !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #EDE6DC;
        padding-bottom: 8px;
    }
    h3 { font-size: 16px !important; font-weight: 600 !important; }

    /* ===== 指标卡片 ===== */
    div[data-testid="metric-card"] {
        background: #FAF7F4 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04) !important;
        border: none !important;
    }
    div[data-testid="metric-card"] [data-testid="stMetricLabel"] {
        color: #5C4A32 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    div[data-testid="metric-card"] [data-testid="stMetricValue"] {
        color: #B8860B !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    /* ===== 导航侧边栏 ===== */
    section[data-testid="stSidebar"] {
        background-color: #3D2B1A !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #3D2B1A !important;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #B8A894 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        color: #B8A894 !important;
        padding: 4px 12px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.06) !important;
        color: #EDE6DC !important;
    }

    /* ===== 按钮 ===== */
    .stButton button {
        background: #B8860B !important;
        color: #FCF8F0 !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 6px 20px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background: #D4A843 !important;
        color: #3D2B1A !important;
    }

    /* ===== Input / Select / Textarea ===== */
    input, select, textarea,
    div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #EDE6DC !important;
        background: #FAF7F4 !important;
    }
    input:focus, select:focus, textarea:focus,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #B8860B !important;
        box-shadow: 0 0 0 1px #B8860B !important;
    }

    /* ===== 提示框 ===== */
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stAlert"] {
        border-left: 4px solid #8C7A64 !important;
    }
    div[data-testid="stAlert"]:has(div[data-testid="stAlertContainer"]) {
        background: #EDE6DC !important;
        color: #3D2B1A !important;
    }

    /* ===== 数据表格 ===== */
    div[data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stDataFrame"] thead tr th {
        background: #EDE6DC !important;
        color: #3D2B1A !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    div[data-testid="stDataFrame"] tbody tr td {
        background: #FAF7F4 !important;
        color: #5C4A32 !important;
        font-size: 13px !important;
    }

    /* ===== 展开容器 ===== */
    div[data-testid="stExpander"] {
        background: #FAF7F4 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
        margin-bottom: 8px !important;
        border: 1px solid #EDE6DC !important;
    }

    /* ===== 标签页 ===== */
    button[data-testid="stTab"] {
        color: #8C7A64 !important;
        font-size: 14px !important;
    }
    button[data-testid="stTab"][aria-selected="true"] {
        color: #B8860B !important;
        border-bottom: 2px solid #B8860B !important;
    }

    /* ===== 进度条 ===== */
    div[role="progressbar"] > div > div {
        background: linear-gradient(90deg, #D4A843, #B8860B) !important;
    }

    /* ===== 页面容器间距 ===== */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px !important;
    }

    /* ===== ZW Page Styles ===== */
    .zw-hero {
        background:#FAF7F4; border-radius:14px; padding:16px;
        border:1px solid #EDE6DC; box-shadow:0 1px 3px rgba(0,0,0,0.04);
        margin-bottom:12px;
    }
    .zw-hero-card {
        background:#FAF7F4; border-radius:12px; padding:14px;
        text-align:center; border:1px solid #EDE6DC;
    }
    .zw-palace-card {
        background:#FAF7F4; border-radius:10px; padding:10px 6px;
        text-align:center; border:1px solid #EDE6DC;
        box-shadow:0 1px 2px rgba(0,0,0,0.04);
    }
    .zw-palace-card.life { border:2px solid #B8860B; }
    .zw-palace-card.body { border:2px solid #C49A3C; }
    .zw-star-chip {
        display:inline-block; border-radius:8px; padding:2px 8px;
        font-size:11px; margin:1px 2px; font-weight:500;
    }
    .zw-main-star { background:#EDE6DC; color:#3D2B1A; }
    .zw-minor-star { background:#D4C5B0; color:#5C4A32; }
    .zw-fierce-star { background:#F0DDD6; color:#B85C4A; }
    .zw-sihua-lu { background:#8BA888; color:#F0F4EC; }
    .zw-sihua-quan { background:#B8860B; color:#FCF8F0; }
    .zw-sihua-ke { background:#7A9BAE; color:#F0F4EC; }
    .zw-sihua-ji { background:#B85C4A; color:#FCF0EC; }
    .zw-tag {
        display:inline-block; border-radius:10px; padding:2px 8px;
        font-size:10px; margin:1px; font-weight:600;
    }
    .zw-keyword {
        display:inline-block; background:#EDE6DC; color:#5C4A32;
        border-radius:10px; padding:3px 10px; font-size:11px;
        margin:2px 3px;
    }
    .zw-boundary {
        background:#FAF7F4; border-left:3px solid #B8860B;
        border-radius:8px; padding:10px 14px; font-size:12px;
        color:#5C4A32; line-height:1.6;
    }
    .zw-triangle-card {
        background:#FAF7F4; border-radius:12px; padding:14px;
        border:1px solid #EDE6DC; margin-bottom:8px;
    }
    .zw-source-card {
        background:#FAF7F4; border-radius:8px; padding:8px 12px;
        margin-bottom:4px; border:1px solid #EDE6DC;
    }
    """


def card_style() -> str:
    """单张卡片的 inline style。"""
    return (
        "background:#FAF7F4;border-radius:10px;"
        "padding:16px 20px;"
        "box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);"
    )


def element_tag(element: str) -> str:
    """生成五行标签的 inline style 字符串。"""
    color = ELEMENT_COLORS.get(element, "#8C7A64")
    text_color = "#FCF8F0" if element in ("火", "金") else "#3D2B1A"
    return (
        f"display:inline-block;background:{color};"
        f"color:{text_color};padding:2px 10px;"
        f"border-radius:12px;font-size:12px;margin:2px;"
    )


def metric_card_html(title: str, value: str, desc: str = "") -> str:
    """指标卡 HTML 片段。三列一行使用。"""
    desc_html = (
        f'<div style="font-size:12px;color:#8C7A64;margin-top:4px;">{desc}</div>'
        if desc else ""
    )
    return (
        f'<div style="{card_style()}text-align:center;">'
        f'<div style="font-weight:600;color:#3D2B1A;font-size:13px;margin-bottom:4px;">{title}</div>'
        f'<div style="font-size:24px;font-weight:700;color:#B8860B;">{value}</div>'
        f"{desc_html}</div>"
    )


def info_row(label: str, value: str) -> str:
    """信息卡内一行键值对（带分割线）。"""
    return (
        f'<div style="display:flex;justify-content:space-between;'
        f'padding:8px 0;border-bottom:1px solid #EDE6DC;">'
        f'<span style="color:#8C7A64;font-size:13px;">{label}</span>'
        f'<span style="color:#3D2B1A;font-weight:500;">{value}</span></div>'
    )


def info_card_html(title: str, rows: list[tuple[str, str]]) -> str:
    """完整信息卡 HTML。rows 是 (label, value) 列表。"""
    rows_html = "".join(info_row(label, value) for label, value in rows)
    return (
        f'<div style="{card_style()}margin:12px 0;">'
        f'<div style="font-weight:600;color:#3D2B1A;font-size:15px;margin-bottom:8px;">{title}</div>'
        f"{rows_html}</div>"
    )

# ===== ZW Page =====
