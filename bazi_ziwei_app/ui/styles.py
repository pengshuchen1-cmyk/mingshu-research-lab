"""命数研究室 · 编辑式浅色视觉基础。"""

ELEMENT_COLORS = {
    "木": "#4F8A5B",
    "火": "#C2413B",
    "土": "#A16207",
    "金": "#64748B",
    "水": "#2563EB",
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
    :root {
        --ms-surface: #FAFAFA;
        --ms-surface-muted: #F4F4F5;
        --ms-ink: #18181B;
        --ms-muted: #71717A;
        --ms-line: rgba(24, 24, 27, .14);
        --ms-action: #EC4899;
        --ms-on-action: #FFFFFF;
        --ms-danger: #B91C1C;
        --ms-radius: 8px;
        --ms-bg: var(--ms-surface);
        --ms-bg-2: var(--ms-surface-muted);
        --ms-surface-2: var(--ms-surface-muted);
        --ms-surface-soft: #FCE7F3;
        --ms-border: var(--ms-line);
        --ms-border-strong: rgba(24, 24, 27, .28);
        --ms-text: var(--ms-ink);
        --ms-text-strong: var(--ms-ink);
        --ms-readable-muted: var(--ms-muted);
        --ms-muted-2: var(--ms-muted);
        --ms-accent: var(--ms-action);
        --ms-accent-soft: #FCE7F3;
        --ms-success: #15803D;
        --ms-info: #2563EB;
        --ms-card-radius: var(--ms-radius);
        --ms-shadow: 0 1px 2px rgba(24, 24, 27, .05);
    }

    #root, .stApp, .main > div {
        background: var(--ms-surface) !important;
        color: var(--ms-ink) !important;
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    h1, h2, h3 {
        color: var(--ms-ink) !important;
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        color: var(--ms-ink) !important;
        line-height: 1.82 !important;
    }
    div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] p,
    div[data-testid="stCaptionContainer"] span, .mingshu-muted, .zw-readable-text,
    .zw-triangle-card p { color: var(--ms-muted) !important; }
    div[data-testid="stStatusWidget"] {
        background: var(--ms-surface-muted) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: none !important;
    }
    div[data-testid="stStatusWidget"] details summary {
        color: var(--ms-ink) !important;
    }

    .main .block-container {
        max-width: 1200px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    .ms-card, .ms-readable-panel, .ms-element-card, .ms-bazi-card,
    .ms-bazi-pillar-card, .ms-bazi-note, .ms-report-panel, .ms-mini-metric,
    .ms-month-card, .ms-life-summary-card, .ms-life-score-card,
    .ms-life-score-grid-card, .ms4-chart-section, .ms4-pillar-card,
    .ms4-dimension-card, .ms4-life-insight-card, .mingshu-feature-card, .mingshu-panel,
    .mingshu-report-card, .mingshu-ai-panel, .mingshu-trend-panel,
    .zw-summary-card, .zw-palace-card, .zw-triangle-card, .zw-source-card {
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: var(--ms-shadow) !important;
        color: var(--ms-ink) !important;
    }
    .ms-readable-panel, .ms-report-panel, .mingshu-report-card { padding: 16px 18px; }
    .ms-chart-title, .mingshu-section-title, .mingshu-report-title,
    .mingshu-feature-title, .mingshu-brand, .v106c-page-title,
    .ms-bazi-title, .ms-month-name, .zw-main-star { color: var(--ms-ink) !important; }
    .mingshu-report-body, .mingshu-mini-stat, .mingshu-chip, .ms-tag,
    .ms-bazi-pill, .zw-minor-star, .zw-main-star {
        background: var(--ms-surface-muted) !important;
        border: 1px solid var(--ms-line) !important;
        color: var(--ms-ink) !important;
        border-radius: var(--ms-radius) !important;
    }
    .ms-bazi-bar {
        height: 10px;
        background: var(--ms-surface-muted) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        overflow: hidden;
    }
    .ms-bazi-text { color: var(--ms-ink) !important; line-height: 1.75; }
    .ms-luck-stage-card {
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        padding: 16px;
    }
    .ms-luck-stage-card.current { border-color: var(--ms-action) !important; }
    .ms-action-grid { display: grid; gap: 12px; }
    .mingshu-hero, .mingshu-bottom-cta, .v106c-page-hero {
        background: var(--ms-surface-muted) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: none !important;
    }
    .mingshu-hero:before, .mingshu-hero:after, .v106c-page-hero:after { display: none; }
    .mingshu-hero-title, .mingshu-hero-subtitle, .mingshu-kicker,
    .mingshu-report-eyebrow, .mingshu-toplinks, .mingshu-orbit-label,
    .v106c-page-eyebrow, .ms-bazi-accent, .ms-month-pillar, .zw-triangle-role {
        color: var(--ms-action) !important;
    }

    /* 保留侧栏 radio 的键盘回退能力，但不把它作为产品主导航展示。 */
    section[data-testid="stSidebar"] {
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        width: 1px !important;
        height: 1px !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0 0 0 0) !important;
        white-space: nowrap !important;
    }
    section[data-testid="stSidebar"]:focus-within {
        width: min(20rem, 100vw) !important;
        height: auto !important;
        margin: 0 !important;
        overflow: visible !important;
        clip: auto !important;
        white-space: normal !important;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        box-shadow: var(--ms-shadow) !important;
        z-index: 1000 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:focus-within {
        background: var(--ms-surface-muted) !important;
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] input:focus-visible {
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    .stButton button {
        min-height: 44px;
        border-radius: var(--ms-radius) !important;
        border: 1px solid var(--ms-ink) !important;
        background: var(--ms-surface) !important;
        color: var(--ms-ink) !important;
        box-shadow: none !important;
        font-weight: 650 !important;
    }
    .stButton button[kind="primary"] {
        background: var(--ms-action) !important;
        border-color: var(--ms-action) !important;
        color: var(--ms-on-action) !important;
    }
    .stButton button:hover { background: var(--ms-surface-muted) !important; }
    .stButton button[kind="primary"]:hover { background: #DB2777 !important; }
    .stButton button:focus-visible, input:focus-visible, textarea:focus-visible,
    div[data-baseweb="select"] > div:focus-within {
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    [class*="st-key-ms_term_button_"] button {
        min-height: 44px;
        width: 100%;
        max-width: 100%;
        justify-content: flex-start;
        cursor: pointer;
    }
    [class*="st-key-ms_term_button_"] {
        min-width: 0;
        max-width: 100%;
        margin-bottom: 8px;
    }
    [class*="st-key-ms_term_button_"] button:focus-visible {
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    .ms-term-detail {
        box-sizing: border-box;
        width: 100%;
        max-width: 100%;
        margin: 12px 0 22px;
        padding: 20px;
        background: var(--ms-surface);
        border: 1px solid var(--ms-line);
        border-left: 4px solid var(--ms-action);
        border-radius: var(--ms-radius);
    }
    .ms-term-detail h3, .ms-term-detail h4 { margin: 0 0 10px; }
    .ms-term-kicker {
        margin: 0 0 4px;
        color: var(--ms-muted) !important;
        font-size: 12px;
        font-weight: 750;
        letter-spacing: .08em;
    }
    .ms-term-public-facts, .ms-term-personalized { margin-top: 16px; }
    .ms-term-public-facts p { margin: 8px 0; }
    .ms-term-public-facts strong { display: block; color: var(--ms-muted); font-size: 12px; }
    .ms-term-personalized { padding-top: 16px; border-top: 1px solid var(--ms-line); }
    .ms-term-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
    .ms-term-facts > div { padding: 10px; background: var(--ms-surface-muted); }
    .ms-term-facts dt { color: var(--ms-muted); font-size: 12px; font-weight: 700; }
    .ms-term-facts dd { margin: 4px 0 0; color: var(--ms-ink); overflow-wrap: anywhere; }
    .ms-term-detail *, .ms4-dimension-card *, .ms-life-identity-card * {
        min-width: 0;
        overflow-wrap: anywhere;
    }

    input, select, textarea, div[data-baseweb="select"] > div,
    div[data-testid="metric-card"], div[data-testid="stExpander"] {
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        color: var(--ms-ink) !important;
        box-shadow: none !important;
    }
    div[data-testid="metric-card"] [data-testid="stMetricLabel"],
    .ms-bazi-label, .ms-bazi-muted, .ms-life-score-label { color: var(--ms-muted) !important; }
    div[data-testid="metric-card"] [data-testid="stMetricValue"],
    .ms-bazi-value, .ms-life-score-summary { color: var(--ms-ink) !important; }
    div[data-testid="stDataFrame"] thead tr th { background: var(--ms-surface-muted) !important; color: var(--ms-ink) !important; }
    div[data-testid="stDataFrame"] tbody tr td { background: var(--ms-surface) !important; color: var(--ms-ink) !important; }
    div[data-testid="stExpander"] p { color: var(--ms-ink) !important; }
    div[role="progressbar"] > div > div { background: var(--ms-action) !important; }

    .zw-hero, .zw-hero-card {
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: var(--ms-shadow) !important;
        color: var(--ms-ink) !important;
    }
    .zw-star-chip, .zw-tag, .zw-keyword {
        display: inline-block;
        background: var(--ms-surface-muted) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        color: var(--ms-ink) !important;
        padding: 2px 8px;
    }
    .ms-luck-stage-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        color: var(--ms-ink) !important;
    }
    .ms-luck-stage-pillar {
        color: var(--ms-action) !important;
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-weight: 700;
    }
    .ms-life-summary-title {
        color: var(--ms-ink) !important;
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-weight: 700;
    }
    .ms-life-summary-text, .ms-report-text, .zw-triangle-muted {
        color: var(--ms-muted) !important;
        line-height: 1.75;
    }
    .ms-life-identity-card {
        margin: 16px 0 24px;
        overflow: hidden;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line);
        border-top: 4px solid var(--ms-ink);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .ms-life-identity-grid {
        display: grid;
        grid-template-columns: minmax(210px, .72fr) minmax(0, 1.28fr);
    }
    .ms-life-core-mark {
        position: relative;
        min-width: 0;
        padding: 28px;
        overflow: hidden;
        background: var(--ms-surface-muted);
        border-right: 1px solid var(--ms-line);
    }
    .ms-life-identity-label, .ms-life-detail-label {
        margin: 0;
        color: var(--ms-muted) !important;
        font-size: 11px;
        font-weight: 750;
        letter-spacing: .12em;
    }
    .ms-life-core-content {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-top: 28px;
    }
    .ms-life-master-copy { display: grid; min-width: 0; }
    .ms-life-master-glyph {
        color: var(--ms-ink);
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-size: 58px;
        font-weight: 750;
        line-height: 1;
    }
    .ms-life-master-copy strong {
        margin-top: 8px;
        color: var(--ms-ink);
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-size: 19px;
    }
    .ms-life-master-copy small { margin-top: 4px; color: var(--ms-muted); }
    .ms-element-pattern {
        position: relative;
        display: inline-block;
        flex: 0 0 76px;
        width: 76px;
        height: 76px;
        overflow: hidden;
        border: 1px solid var(--ms-ink);
        color: var(--ms-ink);
    }
    .ms-element-pattern i { position: absolute; display: block; background: currentColor; }
    .ms-identity-pattern-wood i { bottom: 18%; width: 2px; }
    .ms-identity-pattern-wood i:nth-child(1) { left: 26%; height: 42%; }
    .ms-identity-pattern-wood i:nth-child(2) { left: 49%; height: 63%; }
    .ms-identity-pattern-wood i:nth-child(3) { left: 71%; height: 32%; }
    .ms-identity-pattern-fire i {
        bottom: 17%;
        width: 26%;
        height: 45%;
        clip-path: polygon(50% 0, 100% 100%, 0 100%);
    }
    .ms-identity-pattern-fire i:nth-child(1) { left: 13%; }
    .ms-identity-pattern-fire i:nth-child(2) { left: 37%; bottom: 29%; }
    .ms-identity-pattern-fire i:nth-child(3) { left: 61%; }
    .ms-identity-pattern-earth i { left: 16%; height: 3px; }
    .ms-identity-pattern-earth i:nth-child(1) { bottom: 24%; width: 68%; }
    .ms-identity-pattern-earth i:nth-child(2) { bottom: 45%; width: 55%; }
    .ms-identity-pattern-earth i:nth-child(3) { bottom: 66%; width: 39%; }
    .ms-identity-pattern-metal i { top: 48%; left: 17%; width: 66%; height: 2px; }
    .ms-identity-pattern-metal i:nth-child(1) { transform: rotate(45deg); }
    .ms-identity-pattern-metal i:nth-child(2) { transform: rotate(-45deg); }
    .ms-identity-pattern-metal i:nth-child(3) { left: 34%; width: 32%; transform: rotate(90deg); }
    .ms-identity-pattern-water i {
        left: 13%;
        width: 74%;
        height: 24%;
        background: transparent;
        border-top: 2px solid currentColor;
        border-radius: 50%;
    }
    .ms-identity-pattern-water i:nth-child(1) { top: 26%; }
    .ms-identity-pattern-water i:nth-child(2) { top: 45%; left: 5%; }
    .ms-identity-pattern-water i:nth-child(3) { top: 63%; left: 21%; }
    .ms-life-identity-details { min-width: 0; padding: 26px 28px; }
    .ms-life-detail-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
    .ms-life-detail-heading span { color: var(--ms-muted); font-size: 12px; font-weight: 700; }
    .ms-life-detail-heading strong { color: var(--ms-ink); font-size: 18px; }
    .ms-life-strength-scale {
        position: relative;
        height: 10px;
        margin-top: 12px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
    }
    .ms-life-strength-scale::before {
        position: absolute;
        top: -1px;
        bottom: -1px;
        left: 50%;
        width: 1px;
        background: var(--ms-line);
        content: '';
    }
    .ms-life-strength-marker {
        position: absolute;
        top: -5px;
        left: var(--strength-position);
        width: 4px;
        height: 18px;
        background: var(--ms-ink);
        transform: translateX(-2px);
    }
    .ms-life-strength-labels { display: flex; justify-content: space-between; margin-top: 5px; }
    .ms-life-strength-labels span { color: var(--ms-muted); font-size: 10px; }
    .ms-life-dominant-elements { margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--ms-line); }
    .ms-life-dominant-elements > div { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 9px; }
    .ms-life-dominant-item {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        min-height: 44px;
        padding: 6px 10px 6px 6px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
    }
    .ms-life-dominant-item .ms-element-pattern { flex-basis: 30px; width: 30px; height: 30px; }
    .ms-life-dominant-item strong { color: var(--ms-ink); font-size: 13px; }
    .ms-life-no-dominant { margin: 0; color: var(--ms-ink) !important; font-size: 13px; }
    .ms-life-pattern-line {
        display: grid;
        grid-template-columns: 84px minmax(0, 1fr);
        gap: 12px;
        align-items: baseline;
        margin-top: 18px;
        padding-top: 18px;
        border-top: 1px solid var(--ms-line);
    }
    .ms-life-pattern-line span { color: var(--ms-muted); font-size: 12px; font-weight: 700; }
    .ms-life-pattern-line strong {
        color: var(--ms-ink);
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-size: 18px;
    }
    .ms-life-identity-summary { margin: 14px 0 0; color: var(--ms-ink) !important; line-height: 1.75 !important; }
    .ms-life-score-value {
        color: var(--ms-ink) !important;
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-weight: 750;
    }
    .ms4-chart-section {
        max-width: 100%;
        margin: 20px 0;
        padding: 22px;
        overflow: hidden;
        box-sizing: border-box;
    }
    .ms4-section-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: 16px;
    }
    .ms4-section-head p, .ms4-insight-index {
        margin: 0 0 4px;
        color: var(--ms-muted) !important;
        font-size: 11px;
        font-weight: 750;
        letter-spacing: .12em;
    }
    .ms4-section-head h3 { margin: 0; font-size: 22px; }
    .ms4-section-head > span { color: var(--ms-muted); font-size: 13px; }
    .ms4-four-pillars {
        display: grid;
        grid-template-columns: repeat(4, minmax(150px, 1fr));
        gap: 10px;
        width: 100%;
        max-width: 100%;
        min-width: 0;
        padding-bottom: 8px;
        overflow-x: auto;
        overscroll-behavior-inline: contain;
        -webkit-overflow-scrolling: touch;
    }
    .ms4-pillar-card { min-width: 0; padding: 16px; box-shadow: none !important; }
    .ms4-pillar-label { margin: 0; color: var(--ms-ink) !important; font-weight: 750; }
    .ms4-ten-god { margin: 5px 0 12px; color: var(--ms-muted) !important; font-size: 12px; }
    .ms4-ten-god strong { color: var(--ms-ink); }
    .ms4-pillar-glyphs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .ms4-pillar-glyphs > div {
        padding: 10px 8px;
        background: var(--ms-surface-muted);
        border-radius: var(--ms-radius);
        text-align: center;
    }
    .ms4-pillar-glyphs span, .ms4-pillar-glyphs small { display: block; color: var(--ms-muted); font-size: 11px; }
    .ms4-pillar-glyphs strong {
        display: block;
        margin: 3px 0;
        color: var(--ms-ink);
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-size: 28px;
    }
    .ms4-hidden-row { margin-top: 12px; }
    .ms4-hidden-row > span { display: block; margin-bottom: 6px; color: var(--ms-muted); font-size: 11px; font-weight: 700; }
    .ms4-hidden-row > div { display: flex; flex-wrap: wrap; gap: 5px; }
    .ms4-hidden-stem {
        display: inline-flex;
        align-items: baseline;
        gap: 4px;
        padding: 4px 6px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        color: var(--ms-ink);
        font-weight: 700;
    }
    .ms4-hidden-stem small, .ms4-empty, .ms4-pillar-helper { color: var(--ms-muted); font-size: 10px; font-weight: 500; }
    .ms4-pillar-helper { min-height: 1.5em; margin: 10px 0 0; line-height: 1.5; }
    .ms4-element-distribution { display: grid; gap: 12px; }
    .ms4-element-row {
        display: grid;
        grid-template-columns: 74px minmax(0, 1fr) 82px;
        align-items: center;
        gap: 12px;
    }
    .ms4-element-name { display: flex; align-items: baseline; gap: 7px; }
    .ms4-element-name strong { color: var(--ms-ink); font-size: 16px; }
    .ms4-element-name span { color: var(--ms-muted); font-size: 11px; }
    .ms4-element-track {
        height: 12px;
        overflow: hidden;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
    }
    .ms4-element-bar { display: block; height: 100%; background: var(--element-color); }
    .ms4-element-value { display: flex; align-items: baseline; justify-content: flex-end; gap: 6px; font-variant-numeric: tabular-nums; }
    .ms4-element-value strong { color: var(--ms-ink); }
    .ms4-element-value span { color: var(--ms-muted); font-size: 11px; }
    .ms4-dimension-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 12px 0 16px;
        max-width: 100%;
    }
    .ms4-dimension-card {
        min-width: 0;
        max-width: 100%;
        padding: 18px;
        overflow-wrap: anywhere;
        box-shadow: none !important;
    }
    .ms4-dimension-label { margin: 0; color: var(--ms-ink) !important; font-weight: 750; }
    .ms4-dimension-score { display: flex; align-items: baseline; gap: 4px; margin-top: 12px; }
    .ms4-dimension-score strong { color: var(--ms-ink); font-size: 32px; font-variant-numeric: tabular-nums; }
    .ms4-dimension-score span { color: var(--ms-muted); font-size: 11px; }
    .ms4-dimension-level { margin: 2px 0 10px; color: var(--ms-muted) !important; font-size: 12px; font-weight: 700; }
    .ms4-dimension-summary { margin: 0; color: var(--ms-ink) !important; font-size: 16px; line-height: 1.7 !important; }
    .ms4-dimension-detail {
        max-width: 100%;
        overflow-wrap: anywhere;
    }
    .ms4-dimension-detail-section + .ms4-dimension-detail-section {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid var(--ms-line);
    }
    .ms4-dimension-detail-section h4 { margin: 0 0 6px; color: var(--ms-ink); font-size: 16px; }
    .ms4-dimension-detail-section ul { margin: 0; padding-left: 1.25rem; }
    .ms4-dimension-detail-section li { color: var(--ms-ink); font-size: 16px; line-height: 1.7; }
    .ms4-life-insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 24px 0;
    }
    .ms4-life-insight-card { padding: 20px; }
    .ms4-life-insight-card h3 { margin: 0 0 14px; font-size: 20px; }
    .ms4-life-insight-card > div { padding: 10px 0; border-top: 1px solid var(--ms-line); }
    .ms4-life-insight-card > div > span { color: var(--ms-muted); font-size: 11px; font-weight: 750; }
    .ms4-life-insight-card > div > p { margin: 4px 0 0; color: var(--ms-ink) !important; font-size: 13px; line-height: 1.7 !important; }
    .ms3-year-cover {
        display: grid;
        grid-template-columns: minmax(0, 1.6fr) minmax(180px, .4fr);
        gap: 24px;
        align-items: stretch;
        margin: 20px 0 16px;
        padding: 28px;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line);
        border-top: 4px solid var(--ms-action);
        border-radius: var(--ms-radius);
    }
    .ms3-year-kicker, .ms3-insight-index {
        margin: 0 0 8px;
        color: var(--ms-ink) !important;
        font-size: 12px;
        font-weight: 750;
        letter-spacing: .12em;
    }
    .ms3-year-heading-row {
        display: flex;
        align-items: baseline;
        gap: 14px;
        flex-wrap: wrap;
    }
    .ms3-year-heading-row h2 {
        margin: 0;
        font-size: clamp(48px, 8vw, 88px);
        line-height: .95;
        letter-spacing: -.05em;
        font-variant-numeric: tabular-nums;
    }
    .ms3-year-heading-row p {
        margin: 0;
        color: var(--ms-muted) !important;
        font-weight: 700;
    }
    .ms3-year-theme {
        max-width: 62ch;
        margin: 22px 0 14px;
        color: var(--ms-ink) !important;
        font-size: 18px;
        line-height: 1.7;
    }
    .ms3-year-keywords { display: flex; gap: 8px; flex-wrap: wrap; }
    .ms3-year-keyword {
        padding: 6px 10px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        color: var(--ms-ink);
        font-size: 13px;
    }
    .ms3-year-identity {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        gap: 6px;
        padding: 20px;
        background: var(--ms-surface-muted);
        border-radius: var(--ms-radius);
    }
    .ms3-year-identity span { color: var(--ms-muted); font-size: 13px; }
    .ms3-year-identity strong { color: var(--ms-ink); font-size: 20px; }
    .ms3-year-metrics,
    .ms3-insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin: 0 0 24px;
    }
    .ms3-year-metric,
    .ms3-insight-card {
        min-width: 0;
        padding: 18px;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .ms3-year-metric > p { margin: 0; color: var(--ms-muted) !important; font-size: 13px; }
    .ms3-year-metric > strong {
        display: block;
        margin: 5px 0 12px;
        color: var(--ms-ink);
        font-size: 21px;
    }
    .ms3-year-metric > div { color: var(--ms-muted); font-size: 13px; line-height: 1.65; }
    .ms3-year-metric > div span { color: var(--ms-ink); font-weight: 700; }
    .ms3-insight-grid { margin-top: 24px; }
    .ms3-insight-card h3 { margin: 0 0 18px; font-size: 22px; }
    .ms3-insight-block {
        padding: 12px 0;
        border-top: 1px solid var(--ms-line);
    }
    .ms3-insight-block > span {
        display: block;
        margin-bottom: 5px;
        color: var(--ms-muted);
        font-size: 12px;
        font-weight: 700;
    }
    .ms3-insight-block p { margin: 0; color: var(--ms-ink) !important; line-height: 1.65; }
    .ms3-action-step { display: grid; grid-template-columns: 32px 1fr; gap: 8px; align-items: start; }
    .ms3-action-step + .ms3-action-step { margin-top: 8px; }
    .ms3-action-step span { color: var(--ms-ink); font-variant-numeric: tabular-nums; font-weight: 750; }
    .ms3-boundary-copy strong { display: inline-block; min-width: 64px; margin-right: 8px; }
    .ms3-month-rhythm {
        margin: 18px 0 24px;
        padding: 20px;
        background: var(--ms-surface);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
    }
    .ms3-month-rhythm-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px; }
    .ms3-month-rhythm-head p {
        margin: 0;
        color: var(--ms-muted) !important;
        font-size: 11px;
        font-weight: 750;
        letter-spacing: .12em;
    }
    .ms3-month-rhythm-head h3 { margin: 0; font-size: 22px; }
    .ms3-month-timeline {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 6px;
    }
    .ms3-month-node {
        min-width: 0;
        padding: 10px 6px;
        border-top: 3px solid var(--ms-ink);
        background: var(--ms-surface-muted);
        text-align: center;
    }
    .ms3-month-node span,
    .ms3-month-node strong { display: block; overflow-wrap: anywhere; }
    .ms3-month-node span { color: var(--ms-ink); font-size: 13px; font-weight: 700; }
    .ms3-month-node strong { margin-top: 5px; color: var(--ms-muted); font-size: 11px; line-height: 1.45; }
    .ms3-month-card {
        min-height: 224px;
        margin-top: 8px;
        padding: 20px;
        background: var(--ms-surface);
        border: 1px solid var(--ms-line);
        border-top: 3px solid var(--ms-ink);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .ms3-month-card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
    .ms3-month-card-head p { margin: 0; color: var(--ms-ink) !important; font-size: 22px; font-weight: 750; }
    .ms3-month-card-head strong {
        color: var(--ms-action);
        font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
        font-size: 20px;
    }
    .ms3-month-status {
        display: inline-block;
        margin: 14px 0 8px;
        padding: 4px 9px;
        background: var(--ms-surface-muted);
        border-left: 3px solid var(--ms-ink);
        color: var(--ms-ink);
        font-size: 12px;
        font-weight: 700;
    }
    .ms3-month-direction { margin: 0 0 14px; color: var(--ms-ink) !important; line-height: 1.65; }
    .ms3-month-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .ms3-month-tag {
        padding: 4px 8px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        color: var(--ms-ink);
        font-size: 12px;
    }
    .ms3-month-tag.is-empty { color: var(--ms-muted); }
    div[data-testid="stToggle"] label {
        min-height: 44px;
        width: 100%;
        cursor: pointer;
    }
    .ms3-month-event {
        margin: 12px 0 8px;
        padding: 18px;
        background: var(--ms-surface);
        border: 1px solid var(--ms-line);
        border-left: 3px solid var(--ms-ink);
        border-radius: var(--ms-radius);
    }
    .ms3-month-event-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
    .ms3-month-event-head h4 { margin: 0; color: var(--ms-ink); font-size: 18px; }
    .ms3-month-event-head > span { color: var(--ms-muted); font-size: 12px; font-weight: 700; }
    .ms3-month-event-details {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0 18px;
        margin-top: 12px;
    }
    .ms3-month-event-details > div { padding: 10px 0; border-top: 1px solid var(--ms-line); }
    .ms3-month-event-details span { display: block; color: var(--ms-muted); font-size: 12px; font-weight: 700; }
    .ms3-month-event-details p { margin: 4px 0 0; color: var(--ms-ink) !important; line-height: 1.65; }
    .ms3-month-basis { margin: 0; color: var(--ms-ink) !important; line-height: 1.7; }
    div[data-testid="stNumberInput"] input {
        min-height: 44px;
    }
    div[data-testid="stNumberInput"] button {
        min-width: 44px;
        min-height: 44px;
    }
    div[data-testid="stExpander"] summary { min-height: 44px; }
    div[data-testid="stForm"] {
        margin-top: 18px;
        padding: 24px;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: var(--ms-shadow) !important;
    }
    div[data-testid="stForm"] h3 {
        margin-top: 12px;
        padding-top: 18px;
        border-top: 1px solid var(--ms-line);
        font-size: 18px;
    }
    div[data-testid="stForm"] h3:first-of-type {
        margin-top: 0;
        padding-top: 0;
        border-top: 0;
    }
    div[data-testid="stForm"] input,
    div[data-testid="stForm"] div[role="radiogroup"] label,
    div[data-testid="stForm"] div[data-baseweb="select"] > div {
        min-height: 44px;
    }
    div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] button {
        min-height: 48px;
        margin-top: 12px;
        background: var(--ms-action) !important;
        border-color: var(--ms-action) !important;
        color: var(--ms-on-action) !important;
        font-weight: 700 !important;
    }
    .st-key-ms5-profile-card div[data-testid="stForm"] {
        margin-top: 12px;
        padding: 0;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }
    .st-key-ms5-profile-card [data-testid="stCheckbox"] label {
        min-height: 44px;
        align-items: center;
    }
    .ms-life-score-level {
        color: var(--ms-action) !important;
        font-weight: 700;
    }
    .ms-month-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
    }
    .ms-bazi-section { margin-top: 20px; padding-top: 4px; }
    .ms-bazi-risk { color: var(--ms-danger) !important; line-height: 1.65; }
    .zw-boundary {
        background: var(--ms-surface-muted) !important;
        border-left: 3px solid var(--ms-action) !important;
        color: var(--ms-ink) !important;
        padding: 10px 14px;
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            transition-duration: .01ms !important;
            scroll-behavior: auto !important;
        }
    }
    @media (max-width: 1024px) {
        .ms4-dimension-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
        .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        div[data-testid="stForm"] { padding: 18px 16px; }
        .stMain [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        .stMain [data-testid="stHorizontalBlock"] > div { flex: 1 1 calc(50% - 6px) !important; min-width: 0 !important; }
        .mingshu-hero, .mingshu-bottom-cta { padding: 24px 18px !important; }
        .mingshu-hero-title { font-size: 32px !important; }
        .mingshu-dashboard-grid, .mingshu-hero-grid { grid-template-columns: 1fr !important; }
        .ms4-dimension-grid { grid-template-columns: 1fr; }
        .ms4-dimension-card { padding: 18px 16px; }
    }
    @media (max-width: 768px) {
        .ms3-year-cover,
        .ms3-year-metrics,
        .ms3-insight-grid { grid-template-columns: 1fr; }
        .ms3-year-cover { padding: 22px 18px; }
        .ms3-year-identity { padding: 16px; }
        .ms3-year-theme { font-size: 16px; }
        .ms3-month-timeline { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .ms3-month-event-details { grid-template-columns: 1fr; }
        .ms4-life-insight-grid { grid-template-columns: 1fr; }
        .ms-life-identity-grid { grid-template-columns: 1fr; }
        .ms-life-core-mark { padding: 22px 20px; border-right: 0; border-bottom: 1px solid var(--ms-line); }
        .ms-life-core-content { margin-top: 20px; }
        .ms-life-identity-details { padding: 22px 20px; }
        .st-key-ms3-month-grid [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: 1fr !important;
        }
        .st-key-ms3-month-grid [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 0 !important;
        }
    }
    @media (max-width: 480px) {
        .ms3-month-rhythm { padding: 16px; }
        .ms3-month-timeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .ms3-month-card { min-height: 0; }
        .ms4-chart-section { padding: 16px; }
        .ms4-section-head { align-items: flex-start; flex-direction: column; gap: 6px; }
        .ms4-pillar-helper { display: none; }
        .ms4-element-row { grid-template-columns: 60px minmax(0, 1fr) 64px; gap: 8px; }
    }
    """


def card_style() -> str:
    """单张卡片的 inline style。"""
    return (
        "background:var(--ms-surface);border:1px solid var(--ms-border);"
        "border-radius:var(--ms-card-radius);padding:16px 20px;"
        "box-shadow:var(--ms-shadow);color:var(--ms-text);"
    )


def element_tag(element: str) -> str:
    """生成五行标签的 inline style 字符串。"""
    color = ELEMENT_COLORS.get(element, "#71717A")
    return (
        f"display:inline-block;background:{color};color:#FFFFFF;padding:2px 10px;"
        f"border-radius:var(--ms-radius);font-size:12px;margin:2px;"
    )


def metric_card_html(title: str, value: str, desc: str = "") -> str:
    """指标卡 HTML 片段。三列一行使用。"""
    desc_html = f'<div style="font-size:12px;color:var(--ms-muted);margin-top:4px;">{desc}</div>' if desc else ""
    return (
        f'<div style="{card_style()}text-align:center;">'
        f'<div style="font-weight:600;color:var(--ms-muted);font-size:13px;margin-bottom:4px;">{title}</div>'
        f'<div style="font-size:24px;font-weight:700;color:var(--ms-accent);">{value}</div>{desc_html}</div>'
    )


def info_row(label: str, value: str) -> str:
    """信息卡内一行键值对（带分割线）。"""
    return (
        '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--ms-border);">'
        f'<span style="color:var(--ms-muted);font-size:13px;">{label}</span>'
        f'<span style="color:var(--ms-text);font-weight:500;">{value}</span></div>'
    )


def info_card_html(title: str, rows: list[tuple[str, str]]) -> str:
    """完整信息卡 HTML。rows 是 (label, value) 列表。"""
    rows_html = "".join(info_row(label, value) for label, value in rows)
    return (
        f'<div style="{card_style()}margin:12px 0;">'
        f'<div style="font-weight:600;color:var(--ms-text-strong);font-size:15px;margin-bottom:8px;">{title}</div>{rows_html}</div>'
    )
