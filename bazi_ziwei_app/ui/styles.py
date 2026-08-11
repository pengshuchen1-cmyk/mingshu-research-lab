"""命数研究室 · 深色星空产品视觉基础。"""

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
        --ms-surface: #030714;
        --ms-surface-muted: rgba(16, 20, 31, .82);
        --ms-panel: rgba(11, 15, 26, .78);
        --ms-ink: #FFFDF9;
        --ms-muted: #AEB4C2;
        --ms-line: rgba(255, 244, 226, .14);
        --ms-action: #F2A85F;
        --ms-action-hover: #FFC47D;
        --ms-on-action: #1A1009;
        --ms-danger: #FF8A80;
        --ms-radius: 18px;
        --ms-radius-small: 8px;
        --ms-bg: var(--ms-surface);
        --ms-bg-2: var(--ms-surface-muted);
        --ms-surface-2: var(--ms-surface-muted);
        --ms-surface-soft: rgba(242, 168, 95, .14);
        --ms-border: var(--ms-line);
        --ms-border-strong: rgba(255, 244, 226, .28);
        --ms-text: var(--ms-ink);
        --ms-text-strong: var(--ms-ink);
        --ms-readable-muted: var(--ms-muted);
        --ms-muted-2: var(--ms-muted);
        --ms-accent: var(--ms-action);
        --ms-accent-soft: rgba(242, 168, 95, .14);
        --ms-success: #79C99E;
        --ms-info: #84BDF5;
        --ms-card-radius: var(--ms-radius);
        --ms-shadow: 0 16px 42px rgba(0, 0, 0, .22);
        --ms-shadow-raised: 0 24px 64px rgba(0, 0, 0, .34);
    }

    #root, .stApp, .stMain > div {
        background: var(--ms-surface) !important;
        color: var(--ms-ink) !important;
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    html, body, #root, .stApp { max-width: 100%; overflow-x: clip; }
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"] {
        display: none !important;
        height: 0 !important;
    }
    div[data-testid="stElementContainer"]:has(a[href="#ms-main"]) {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        overflow: visible !important;
    }
    div[data-testid="stMarkdown"]:has(a[href="#ms-main"]) {
        position: absolute;
        left: -9999px;
        top: auto;
    }
    div[data-testid="stMarkdown"]:has(a[href="#ms-main"]):focus-within {
        left: 20px;
        top: 12px;
        z-index: 1001;
    }
    h1, h2, h3 {
        color: var(--ms-ink) !important;
        font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
        font-weight: 700;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        color: var(--ms-ink) !important;
        line-height: 1.72 !important;
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

    [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 1280px !important;
        padding-top: 20px !important;
        padding-right: 2rem !important;
        padding-bottom: 4rem !important;
        padding-left: 2rem !important;
    }
    body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"] h1 {
        margin-bottom: .65rem;
        font-size: clamp(2.5rem, 5vw, 4rem);
        line-height: 1.08;
        letter-spacing: -.045em;
    }
    body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"] h2 {
        margin-top: 1.8rem;
        font-size: clamp(1.6rem, 3vw, 2.25rem);
        line-height: 1.2;
        letter-spacing: -.025em;
    }
    .ms-card, .ms-readable-panel, .ms-element-card, .ms-bazi-card,
    .ms-bazi-pillar-card, .ms-bazi-note, .ms-report-panel, .ms-mini-metric,
    .ms-month-card, .ms-life-summary-card, .ms-life-score-card,
    .ms-life-score-grid-card, .ms4-chart-section, .ms4-pillar-card,
    .ms4-dimension-card, .ms4-life-insight-card, .mingshu-feature-card, .mingshu-panel,
    .mingshu-report-card, .mingshu-ai-panel, .mingshu-trend-panel,
    .zw-summary-card, .zw-palace-card, .zw-triangle-card, .zw-source-card {
        background: var(--ms-panel) !important;
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
    div[data-testid="stSidebarCollapseButton"],
    button[data-testid="stExpandSidebarButton"] {
        display: none !important;
    }
    .st-key-editorial-product-nav {
        position: relative !important;
        z-index: 10;
        width: 100%;
        margin: 0 0 38px;
        padding: 8px;
        background: rgba(8, 11, 20, .72);
        border: 1px solid var(--ms-line);
        border-radius: 22px;
        box-shadow: 0 18px 48px rgba(0, 0, 0, .24);
        backdrop-filter: blur(22px) saturate(118%);
        -webkit-backdrop-filter: blur(22px) saturate(118%);
        transform: none;
    }
    .st-key-editorial-product-nav [data-testid="stHorizontalBlock"] {
        gap: 6px !important;
    }
    .st-key-editorial-product-nav .stButton button {
        min-height: 44px;
        border-color: transparent !important;
        border-radius: 14px !important;
        background: transparent !important;
        color: var(--ms-muted) !important;
        font-size: 14px;
        transition: background-color 180ms ease, border-color 180ms ease, color 180ms ease;
    }
    .st-key-editorial-product-nav .stButton button:hover {
        background: rgba(255, 255, 255, .06) !important;
        color: var(--ms-ink) !important;
    }
    .st-key-editorial-product-nav .stButton button[kind="primary"] {
        background: var(--ms-accent-soft) !important;
        border: 1px solid rgba(242, 168, 95, .34) !important;
        color: var(--ms-action) !important;
        box-shadow: inset 0 0 22px rgba(242, 168, 95, .06) !important;
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
    .stButton button[kind="primary"] p,
    .stButton button[kind="primary"] span {
        color: var(--ms-on-action) !important;
    }
    .st-key-editorial-product-nav .stButton button[kind="primary"] p,
    .st-key-editorial-product-nav .stButton button[kind="primary"] span {
        color: var(--ms-action) !important;
    }
    .stButton button:hover { background: rgba(255, 255, 255, .07) !important; }
    .stButton button[kind="primary"]:hover {
        background: var(--ms-action-hover) !important;
        border-color: var(--ms-action-hover) !important;
    }
    .st-key-editorial-product-nav .stButton button[kind="primary"]:hover {
        background: rgba(242, 168, 95, .20) !important;
        border-color: rgba(242, 168, 95, .42) !important;
        color: var(--ms-action) !important;
    }
    .st-key-editorial-product-nav .stButton button[kind="primary"]:hover p,
    .st-key-editorial-product-nav .stButton button[kind="primary"]:hover span {
        color: var(--ms-action) !important;
    }

    /* Shared celestial product shell: quieter than the landing hero, but visibly related. */
    body:not(:has(.st-key-ms2-home)) .stApp,
    body:not(:has(.st-key-ms2-home)) .stMain {
        color-scheme: dark;
        background:
            radial-gradient(circle at 82% 12%, rgba(116, 44, 25, .20), transparent 38%),
            radial-gradient(circle at 12% 86%, rgba(11, 55, 88, .22), transparent 42%),
            #030714 !important;
    }
    body:not(:has(.st-key-ms2-home)) .stMain > div {
        position: relative;
        z-index: 1;
        background: transparent !important;
    }
    body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 2;
    }
    .ms-product-celestial-canvas {
        position: fixed;
        inset: 0;
        z-index: 0;
        display: block;
        width: 100%;
        height: 100%;
        opacity: .19;
        filter: saturate(.82);
        pointer-events: none;
    }
    div[data-testid="stLayoutWrapper"]:has(> .st-key-ms-product-celestial-bridge),
    .st-key-ms-product-celestial-bridge {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        margin: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"]::before {
        position: absolute;
        inset: 0 1.1rem;
        z-index: -1;
        border: 1px solid rgba(255, 244, 226, .05);
        border-radius: 30px;
        background: linear-gradient(180deg, rgba(10, 14, 25, .56), rgba(5, 8, 17, .30));
        box-shadow: 0 30px 90px rgba(0, 0, 0, .24);
        backdrop-filter: blur(4px);
        content: "";
        pointer-events: none;
    }

    body:not(:has(.st-key-ms2-home)) .ms2-page-hero {
        position: relative;
        margin: 0 0 28px;
        padding: clamp(28px, 5vw, 58px);
        overflow: hidden;
        border: 1px solid var(--ms-line);
        border-radius: 26px;
        background:
            radial-gradient(circle at 82% 18%, rgba(242, 168, 95, .16), transparent 35%),
            linear-gradient(135deg, rgba(20, 23, 35, .88), rgba(8, 12, 23, .72));
        box-shadow: var(--ms-shadow-raised);
    }
    body:not(:has(.st-key-ms2-home)) .ms2-page-hero::after {
        position: absolute;
        top: -44%;
        right: -8%;
        width: min(42vw, 420px);
        aspect-ratio: 1;
        border: 1px solid rgba(242, 168, 95, .18);
        border-radius: 50%;
        box-shadow:
            0 0 0 38px rgba(242, 168, 95, .025),
            0 0 0 84px rgba(242, 168, 95, .018);
        content: "";
        pointer-events: none;
    }
    body:not(:has(.st-key-ms2-home)) .ms2-page-hero .ms2-kicker {
        margin: 0 0 12px;
        color: var(--ms-action) !important;
        font-size: 12px;
        font-weight: 760;
        letter-spacing: .16em;
    }
    body:not(:has(.st-key-ms2-home)) .ms2-page-hero h1 {
        position: relative;
        z-index: 1;
        margin: 0 0 16px !important;
        font-size: clamp(3.6rem, 8vw, 6.8rem) !important;
        line-height: .92 !important;
    }
    body:not(:has(.st-key-ms2-home)) .ms2-page-hero > p:last-child {
        position: relative;
        z-index: 1;
        max-width: 42rem;
        margin: 0;
        color: var(--ms-muted) !important;
        font-size: 16px;
    }
    body:not(:has(.st-key-ms2-home)):has(.ms2-page-hero)
    div[data-testid="stHorizontalBlock"]:has(h3) > div[data-testid="stColumn"] {
        min-height: 190px;
        padding: 22px 24px;
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        background: var(--ms-panel);
        box-shadow: var(--ms-shadow);
        backdrop-filter: blur(18px);
    }

    body:not(:has(.st-key-ms2-home)) div[data-testid="stExpander"],
    body:not(:has(.st-key-ms2-home)) div[data-testid="stForm"],
    body:not(:has(.st-key-ms2-home)) [data-testid="stNotification"],
    body:not(:has(.st-key-ms2-home)) [data-testid="stChatInput"],
    body:not(:has(.st-key-ms2-home)) [data-testid="stFileUploaderDropzone"] {
        border-color: var(--ms-line) !important;
        background: rgba(11, 15, 26, .78) !important;
        box-shadow: var(--ms-shadow) !important;
        backdrop-filter: blur(18px);
    }
    body:not(:has(.st-key-ms2-home)) input,
    body:not(:has(.st-key-ms2-home)) textarea,
    body:not(:has(.st-key-ms2-home)) [data-baseweb="select"] > div,
    body:not(:has(.st-key-ms2-home)) [data-baseweb="input"] > div {
        background: rgba(8, 12, 22, .86) !important;
        color: var(--ms-ink) !important;
    }
    body:not(:has(.st-key-ms2-home)) input::placeholder,
    body:not(:has(.st-key-ms2-home)) textarea::placeholder {
        color: rgba(255, 253, 249, .48) !important;
        opacity: 1 !important;
    }
    body:not(:has(.st-key-ms2-home)) [role="listbox"],
    body:not(:has(.st-key-ms2-home)) [data-baseweb="popover"] > div {
        border-color: var(--ms-line) !important;
        background: #0C111D !important;
        color: var(--ms-ink) !important;
        box-shadow: var(--ms-shadow-raised) !important;
    }
    body:not(:has(.st-key-ms2-home)) [role="option"]:hover,
    body:not(:has(.st-key-ms2-home)) [role="option"][aria-selected="true"] {
        background: rgba(242, 168, 95, .14) !important;
    }
    body:not(:has(.st-key-ms2-home)) div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom-color: var(--ms-line) !important;
    }
    body:not(:has(.st-key-ms2-home)) div[data-testid="stTabs"] button[role="tab"] {
        color: var(--ms-muted) !important;
    }
    body:not(:has(.st-key-ms2-home)) div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--ms-action) !important;
    }

    /* AI inquiry: quiet, single-column conversation workspace. */
    .st-key-ms-inquiry-page {
        width: 100%;
        max-width: 1040px;
        min-height: 62vh;
        margin: 0 auto;
    }
    .st-key-ms-inquiry-page > div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    .ms-inquiry-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        margin: 2px 0 18px;
        padding: 0 2px 12px;
        border-bottom: 1px solid var(--ms-line);
    }
    .ms-inquiry-title {
        color: var(--ms-ink);
        font-size: 16px;
        font-weight: 750;
        letter-spacing: -.01em;
    }
    .ms-inquiry-meta {
        color: var(--ms-muted);
        font-size: 12px;
        font-weight: 550;
        line-height: 1.5;
        text-align: right;
    }
    .st-key-ms-inquiry-context {
        margin-bottom: 28px;
    }
    .st-key-ms-inquiry-context > div[data-testid="stVerticalBlock"] {
        gap: 8px !important;
    }
    .st-key-ms-inquiry-context div[data-testid="stExpander"] {
        border-color: rgba(24, 24, 27, .1) !important;
        background: transparent !important;
    }
    .st-key-ms-inquiry-context div[data-testid="stExpander"] summary {
        min-height: 46px;
        color: var(--ms-muted) !important;
        font-size: 13px;
    }
    .ms-inquiry-safety {
        margin: 6px 2px 0 !important;
        color: var(--ms-muted) !important;
        font-size: 12px;
        line-height: 1.6 !important;
    }
    .st-key-ms-inquiry-thread {
        width: 100%;
        max-width: 880px;
        min-height: 340px;
        margin: 0 auto;
        padding: 8px 0 40px;
    }
    .st-key-ms-inquiry-thread > div[data-testid="stVerticalBlock"] {
        gap: 12px !important;
    }
    .ms-inquiry-empty {
        display: flex;
        min-height: 108px;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 8px;
        padding: 32px 20px;
        text-align: center;
    }
    .ms-inquiry-empty strong {
        color: var(--ms-ink);
        font-size: clamp(20px, 3vw, 28px);
        font-weight: 700;
        letter-spacing: -.025em;
    }
    .ms-inquiry-empty span {
        max-width: 520px;
        color: var(--ms-muted);
        font-size: 14px;
        line-height: 1.7;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"] {
        width: 100%;
        max-width: 880px;
        margin: 0 auto;
        padding: 10px 0;
        border: 0;
        background: transparent !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessageAvatarUser"],
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"][aria-label="Chat message from user"],
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-end !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"][aria-label="Chat message from user"]
    [data-testid="stChatMessageContent"],
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] {
        flex: 0 1 auto;
        display: flex !important;
        width: fit-content !important;
        min-height: 44px;
        box-sizing: border-box;
        align-items: center !important;
        max-width: min(78%, 680px);
        margin-right: 0 !important;
        margin-left: auto !important;
        padding: 8px 16px;
        border-radius: 20px 20px 6px 20px;
        background: var(--ms-surface-muted) !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] > div,
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stChatMessageContent"] p {
        margin: 0 !important;
        line-height: 1.5 !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stChatMessageContent"] {
        width: 100%;
        padding: 4px 0 12px;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessageContent"] p {
        margin-bottom: .65rem;
        font-size: 15px;
        line-height: 1.75 !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessageContent"] p:last-child {
        margin-bottom: 0;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stBottomBlockContainer"] {
        padding: 14px 24px 20px !important;
        background: var(--ms-surface) !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] {
        box-sizing: border-box;
        width: 100%;
        max-width: 880px;
        min-height: 92px;
        margin: 0 auto;
        padding: 12px 14px !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: 24px !important;
        background: var(--ms-panel) !important;
        box-shadow: var(--ms-shadow-raised) !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] div {
        border: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] textarea {
        min-height: 60px !important;
        padding: 8px 4px !important;
        border: 0 !important;
        background: transparent !important;
        color: var(--ms-ink) !important;
        font-size: 16px !important;
        line-height: 1.55 !important;
        box-shadow: none !important;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] textarea::placeholder {
        color: var(--ms-muted) !important;
        opacity: .85;
    }
    body:has(.st-key-ms-inquiry-page) button[data-testid="stChatInputSubmitButton"] {
        width: 44px !important;
        min-width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        margin: 0 2px 2px 10px;
        border: 0 !important;
        border-radius: 50% !important;
        background: var(--ms-ink) !important;
        color: var(--ms-panel) !important;
        transition: opacity 180ms ease, background-color 180ms ease;
    }
    body:has(.st-key-ms-inquiry-page) button[data-testid="stChatInputSubmitButton"]:disabled {
        background: var(--ms-surface-muted) !important;
        color: var(--ms-muted) !important;
        opacity: .72;
    }
    body:has(.st-key-ms-inquiry-page) [data-testid="stMainBlockContainer"] {
        padding-bottom: 12rem !important;
    }
    .stButton button:focus-visible, input:not([role="combobox"]):focus-visible,
    textarea:focus-visible,
    .stSelectbox div[role="group"]:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    [class*="st-key-ms_term_button_"] button {
        min-height: 44px;
        width: 100%;
        max-width: 100%;
        justify-content: center;
        padding: 6px 12px;
        border-color: var(--ms-line) !important;
        border-radius: 999px !important;
        background: var(--ms-surface-muted) !important;
        font-size: 14px;
        cursor: pointer;
    }
    [class*="st-key-ms_term_button_"] button[kind="primary"] {
        background: var(--ms-action) !important;
        border-color: var(--ms-action) !important;
        color: var(--ms-on-action) !important;
    }
    [class*="st-key-ms_term_button_"] {
        min-width: 0;
        max-width: 100%;
        margin-bottom: 4px;
    }
    [class*="st-key-ms_term_button_"] button:focus-visible {
        outline: 3px solid var(--ms-action) !important;
        outline-offset: 2px !important;
    }
    .st-key-ms-term-dictionary {
        margin: 20px 0 24px;
    }
    .st-key-ms-term-dictionary div[data-testid="stExpander"] {
        overflow: hidden;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: none !important;
    }
    .st-key-ms-term-dictionary div[data-testid="stExpander"] summary {
        min-height: 52px;
        font-weight: 750;
    }
    .ms-term-detail {
        box-sizing: border-box;
        width: 100%;
        max-width: 100%;
        margin: 14px 0 4px;
        padding: 20px;
        background: var(--ms-panel);
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

    input:not([role="combobox"]), select, textarea,
    .stSelectbox div[role="group"], div[data-baseweb="select"] > div,
    div[data-testid="metric-card"], div[data-testid="stExpander"] {
        background: var(--ms-panel) !important;
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
        background: var(--ms-panel) !important;
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
    .st-key-ms-life-empty {
        max-width: 720px;
        margin: 72px auto;
        padding: 30px;
        background: var(--ms-panel) !important;
        border: 1px solid var(--ms-line);
        border-top: 4px solid var(--ms-action);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .st-key-ms-life-empty h2 { margin-top: 0 !important; }
    .st-key-ms-life-overview {
        width: 100%;
        max-width: 1080px;
        margin: 0 auto;
    }
    .st-key-ms-life-overview > div[data-testid="stVerticalBlock"] {
        gap: .35rem;
    }
    .st-key-ms-life-overview h1 + div[data-testid="stMarkdownContainer"] h2 {
        margin-top: .5rem;
    }
    .ms-life-identity-card {
        margin: 18px 0 28px;
        overflow: hidden;
        background: var(--ms-panel) !important;
        border: 1px solid var(--ms-line);
        border-top: 4px solid var(--ms-action);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .ms-life-identity-grid {
        display: grid;
        grid-template-columns: minmax(240px, .86fr) minmax(0, 1.14fr);
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
    .st-key-ms-life-next-actions {
        margin: 32px 0 38px;
        padding: 22px;
        background: var(--ms-panel) !important;
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        box-shadow: var(--ms-shadow);
    }
    .st-key-ms-life-next-actions h3 { margin-top: 0; }
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
    div[data-testid="stForm"] h2 {
        margin-top: 12px;
        padding-top: 18px;
        border-top: 1px solid var(--ms-line);
        font-size: 18px;
    }
    div[data-testid="stForm"] h2:first-of-type {
        margin-top: 0;
        padding-top: 0;
        border-top: 0;
    }
    div[data-testid="stForm"] input:not([role="combobox"]),
    div[data-testid="stForm"] div[role="radiogroup"] label,
    div[data-testid="stForm"] .stSelectbox div[role="group"],
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
    .ms5-stepper {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 14px 0 20px;
    }
    .ms5-step {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
        padding: 12px 14px;
        background: var(--ms-surface-muted);
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius);
        color: var(--ms-muted);
    }
    .ms5-step-number {
        display: inline-grid;
        place-items: center;
        flex: 0 0 28px;
        width: 28px;
        height: 28px;
        border: 1px solid currentColor;
        border-radius: 50%;
        font-size: 13px;
        font-weight: 750;
    }
    .ms5-step-copy { min-width: 0; }
    .ms5-step-copy strong, .ms5-step-copy small { display: block; }
    .ms5-step-copy strong { color: inherit; font-size: 14px; }
    .ms5-step-copy small { margin-top: 2px; font-size: 12px; }
    .ms5-step.active {
        background: var(--ms-accent-soft);
        border-color: var(--ms-action);
        color: var(--ms-action);
    }
    .ms5-step.complete { color: var(--ms-ink); }
    .st-key-ms-report-empty {
        max-width: 760px;
        margin: 32px auto;
        padding: 30px;
        background: var(--ms-surface) !important;
        border: 1px solid var(--ms-line);
        border-top: 4px solid var(--ms-action);
        border-radius: var(--ms-radius);
    }
    .st-key-ms-report-empty h1 { margin-top: 0; font-size: 32px; }
    .st-key-ms-term-accessibility-bridge,
    .st-key-ms-navigation-reset-bridge {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        overflow: hidden !important;
        pointer-events: none !important;
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

    /* Shadcn-inspired native primitives: composable, low-chrome, one token set. */
    [class*="st-key-ms-ui-card-"] {
        padding: 20px 22px;
        background: var(--ms-panel) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: var(--ms-shadow) !important;
    }
    [class*="st-key-ms-ui-card-muted-"] { background: var(--ms-surface-muted) !important; }
    [class*="st-key-ms-ui-card-accent-"] { border-color: rgba(190, 24, 93, .32) !important; }
    [class*="st-key-ms-ui-card-danger-"] { border-color: rgba(185, 28, 28, .34) !important; }
    [class*="st-key-ms-ui-card-default-sm-"],
    [class*="st-key-ms-ui-card-muted-sm-"] { padding: 14px 16px; }
    [class*="st-key-ms-ui-card-default-lg-"],
    [class*="st-key-ms-ui-card-muted-lg-"],
    [class*="st-key-ms-ui-card-accent-lg-"],
    [class*="st-key-ms-ui-card-danger-lg-"] { padding: 24px; }

    .ms-ui-page-header { max-width: 760px; margin: 8px 0 32px; }
    .ms-ui-page-header h1 {
        margin: 6px 0 0 !important;
        font-size: clamp(2.35rem, 5vw, 3.6rem) !important;
        line-height: 1.06 !important;
        letter-spacing: -.045em !important;
        text-wrap: balance;
    }
    .ms-ui-eyebrow {
        margin: 0 !important;
        color: var(--ms-action) !important;
        font-size: 12px !important;
        font-weight: 750 !important;
        letter-spacing: .12em;
        line-height: 1.4 !important;
        text-transform: uppercase;
    }
    .ms-ui-page-description {
        max-width: 62ch;
        margin: 14px 0 0 !important;
        color: var(--ms-muted) !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
    }
    .ms-ui-section-header { margin: 4px 0 18px; }
    .ms-ui-section-header h2 {
        margin: 4px 0 0 !important;
        font-size: clamp(1.35rem, 2.6vw, 1.75rem) !important;
        line-height: 1.25 !important;
        letter-spacing: -.025em !important;
    }
    .ms-ui-section-description {
        max-width: 68ch;
        margin: 8px 0 0 !important;
        color: var(--ms-muted) !important;
        font-size: 14px !important;
        line-height: 1.65 !important;
    }
    .ms-ui-badge {
        display: inline-flex;
        min-height: 26px;
        align-items: center;
        padding: 3px 9px;
        border: 1px solid var(--ms-line);
        border-radius: 999px;
        background: var(--ms-panel);
        color: var(--ms-ink);
        font-size: 12px;
        font-weight: 650;
        line-height: 1.3;
    }
    .ms-ui-badge-muted { background: var(--ms-surface-muted); color: var(--ms-muted); }
    .ms-ui-badge-accent { background: var(--ms-accent-soft); border-color: rgba(190, 24, 93, .22); color: var(--ms-action); }
    .ms-ui-badge-danger { background: #FEF2F2; border-color: #FECACA; color: var(--ms-danger); }
    .ms-ui-callout {
        display: grid;
        grid-template-columns: 8px minmax(0, 1fr);
        gap: 12px;
        margin: 0;
        padding: 15px 16px;
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius-small);
        background: var(--ms-panel);
    }
    .ms-ui-callout-mark { width: 8px; height: 8px; margin-top: 6px; border-radius: 50%; background: var(--ms-action); }
    .ms-ui-callout-copy strong { display: block; color: var(--ms-ink); font-size: 14px; }
    .ms-ui-callout-copy p { margin: 4px 0 0 !important; color: var(--ms-muted) !important; font-size: 14px !important; line-height: 1.6 !important; }
    .ms-ui-callout-muted { background: var(--ms-surface-muted); }
    .ms-ui-callout-muted .ms-ui-callout-mark { background: var(--ms-muted); }
    .ms-ui-callout-accent { border-color: rgba(190, 24, 93, .25); }
    .ms-ui-callout-danger { border-color: #FECACA; background: #FEF2F2; }
    .ms-ui-callout-danger .ms-ui-callout-mark { background: var(--ms-danger); }
    .ms-ui-metric {
        min-height: 104px;
        padding: 16px;
        border: 1px solid var(--ms-line);
        border-radius: var(--ms-radius-small);
        background: var(--ms-panel);
    }
    .ms-ui-metric > span { display: block; color: var(--ms-muted); font-size: 12px; font-weight: 650; }
    .ms-ui-metric > strong { display: block; margin-top: 8px; color: var(--ms-ink); font-size: 21px; line-height: 1.25; }
    .ms-ui-metric > p { margin: 8px 0 0 !important; color: var(--ms-muted) !important; font-size: 12px !important; line-height: 1.5 !important; }
    .ms-ui-empty-state-copy { max-width: 42rem; margin-bottom: 22px; }
    .ms-ui-empty-state-mark { display: block; width: 36px; height: 4px; margin-bottom: 20px; border-radius: 999px; background: var(--ms-action); }
    .ms-ui-empty-state-copy h2 { margin: 0 !important; font-size: clamp(1.75rem, 4vw, 2.35rem) !important; }
    .ms-ui-empty-state-copy p { margin: 10px 0 0 !important; color: var(--ms-muted) !important; font-size: 15px !important; line-height: 1.65 !important; }

    :where(.stButton, .stDownloadButton) > button {
        min-height: 44px;
        padding: 8px 15px;
        border-color: var(--ms-line) !important;
        border-radius: var(--ms-radius-small) !important;
        background: var(--ms-panel) !important;
        color: var(--ms-ink) !important;
        box-shadow: var(--ms-shadow) !important;
        font-size: 14px;
        font-weight: 650 !important;
        transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease;
        touch-action: manipulation;
    }
    :where(.stButton, .stDownloadButton) > button:hover {
        border-color: var(--ms-border-strong) !important;
        background: var(--ms-surface-muted) !important;
    }
    :where(.stButton, .stDownloadButton) > button[kind="primary"] {
        border-color: var(--ms-action) !important;
        background: var(--ms-action) !important;
        color: var(--ms-on-action) !important;
        box-shadow: none !important;
    }
    :where(.stButton, .stDownloadButton) > button[kind="primary"]:hover {
        border-color: var(--ms-action-hover) !important;
        background: var(--ms-action-hover) !important;
    }

    input:not([role="combobox"]), textarea,
    .stSelectbox div[role="group"], div[data-baseweb="select"] > div {
        min-height: 44px;
        border-color: var(--ms-line) !important;
        border-radius: var(--ms-radius-small) !important;
        background: var(--ms-panel) !important;
        box-shadow: none !important;
        font-size: 15px !important;
    }
    textarea { min-height: 112px; padding: 10px 12px !important; }
    input:not([role="combobox"]):hover, textarea:hover,
    .stSelectbox div[role="group"]:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: var(--ms-border-strong) !important;
    }

    /* Streamlit 1.5x React Aria selectbox: style the shell, not its inner input. */
    .stSelectbox div[role="group"] {
        height: 44px;
        overflow: hidden;
        transition: border-color 160ms ease, outline-color 160ms ease;
    }
    .stSelectbox div[role="group"]:focus-within {
        border-color: var(--ms-action) !important;
        background: var(--ms-panel) !important;
    }
    .stSelectbox input[role="combobox"] {
        height: 42px !important;
        min-height: 42px !important;
        padding: 8px 12px !important;
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        color: var(--ms-ink) !important;
        box-shadow: none !important;
        outline: 0 !important;
        font-size: 15px !important;
    }
    .stSelectbox div[role="group"] > button {
        width: 44px;
        min-width: 44px;
        height: 42px;
        min-height: 42px;
        padding: 0 12px;
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        color: var(--ms-ink) !important;
        box-shadow: none !important;
    }
    .stSelectbox div[role="group"] > button:hover {
        background: var(--ms-surface-muted) !important;
    }
    div:has(> [role="listbox"]) {
        overflow: hidden;
        padding: 4px !important;
        background: var(--ms-panel) !important;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius-small) !important;
        box-shadow: 0 12px 30px rgba(24, 24, 27, .14) !important;
    }
    [role="listbox"] [role="option"] {
        min-height: 40px;
        padding: 0 10px !important;
        border-radius: 6px;
        color: var(--ms-ink) !important;
    }
    [role="listbox"] [role="option"]:hover,
    [role="listbox"] [role="option"][aria-selected="true"] {
        background: var(--ms-surface-muted) !important;
    }
    label, div[data-testid="stWidgetLabel"] { color: var(--ms-ink) !important; font-weight: 600 !important; }

    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 4px;
        width: fit-content;
        max-width: 100%;
        margin-bottom: 18px;
        padding: 4px;
        overflow-x: auto;
        border: 1px solid var(--ms-line);
        border-radius: 10px;
        background: var(--ms-surface-muted);
        scrollbar-width: none;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    div[data-testid="stTabs"] button[role="tab"] {
        min-height: 40px;
        padding: 7px 14px;
        border-radius: 7px;
        color: var(--ms-muted) !important;
        font-size: 14px;
        font-weight: 650;
        white-space: nowrap;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: var(--ms-panel) !important;
        color: var(--ms-ink) !important;
        box-shadow: var(--ms-shadow) !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

    div[data-testid="stAlert"] {
        padding: 14px 16px;
        border: 1px solid var(--ms-line) !important;
        border-radius: var(--ms-radius-small) !important;
        background: var(--ms-panel) !important;
        box-shadow: none !important;
    }
    div[data-testid="stAlert"] p { font-size: 14px !important; line-height: 1.6 !important; }
    div[data-testid="metric-card"] {
        min-height: 104px;
        padding: 16px !important;
        border-radius: var(--ms-radius-small) !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] {
        overflow: hidden;
        border-radius: var(--ms-radius-small) !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] summary { padding: 3px 4px; font-weight: 650; }
    div[data-testid="stForm"] {
        background: var(--ms-panel) !important;
        border-radius: var(--ms-radius) !important;
        box-shadow: none !important;
    }
    hr { border-color: var(--ms-line) !important; }

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
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.25rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: calc(6.25rem + env(safe-area-inset-bottom)) !important;
        }
        body:has(.st-key-ms-inquiry-page) [data-testid="stMainBlockContainer"] {
            padding-bottom: calc(14rem + env(safe-area-inset-bottom)) !important;
        }
        .ms-inquiry-topline {
            align-items: flex-start;
            margin-bottom: 14px;
        }
        .ms-inquiry-title { font-size: 15px; }
        .ms-inquiry-meta {
            max-width: 180px;
            font-size: 11px;
        }
        .st-key-ms-inquiry-context { margin-bottom: 18px; }
        .st-key-ms-inquiry-thread {
            min-height: 260px;
            padding-bottom: 28px;
        }
        .ms-inquiry-empty {
            min-height: 80px;
            gap: 4px;
            padding: 14px 8px;
        }
        .ms-inquiry-empty strong { font-size: 21px; }
        .ms-inquiry-empty span { font-size: 13px; }
        body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"][aria-label="Chat message from user"]
        [data-testid="stChatMessageContent"],
        body:has(.st-key-ms-inquiry-page) [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
        [data-testid="stChatMessageContent"] {
            max-width: 88%;
        }
        body:has(.st-key-ms-inquiry-page) [data-testid="stBottom"] {
            bottom: calc(64px + env(safe-area-inset-bottom)) !important;
        }
        body:has(.st-key-ms-inquiry-page) [data-testid="stBottomBlockContainer"] {
            padding: 8px 12px 10px !important;
        }
        body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] {
            min-height: 72px;
            padding: 8px 10px !important;
            border-radius: 20px !important;
        }
        body:has(.st-key-ms-inquiry-page) [data-testid="stChatInput"] textarea {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        .ms-ui-page-header { margin: 4px 0 24px; }
        .ms-ui-page-header h1 { font-size: clamp(2.15rem, 11vw, 3rem) !important; }
        .ms-ui-page-description { font-size: 15px !important; }
        [class*="st-key-ms-ui-card-"] { padding: 18px 16px; }
        .ms-ui-metric { min-height: 92px; padding: 14px; }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] { width: 100%; }
        div[data-testid="stTabs"] button[role="tab"] { flex: 0 0 auto; min-height: 44px; }
        div[data-testid="stForm"] { padding: 18px 16px; }
        .stMain [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        .stMain [data-testid="stHorizontalBlock"] > div { flex: 1 1 calc(50% - 6px) !important; min-width: 0 !important; }
        .st-key-editorial-product-nav {
            position: fixed !important;
            top: auto;
            right: 0;
            bottom: 0;
            left: 0;
            z-index: 1000;
            margin: 0;
            padding: 8px 8px calc(8px + env(safe-area-inset-bottom));
            background: rgba(5, 8, 17, .92);
            border-top: 1px solid var(--ms-line);
            border-right: 0;
            border-bottom: 0;
            border-left: 0;
            border-radius: 0;
            box-shadow: 0 -10px 34px rgba(0, 0, 0, .34);
            backdrop-filter: blur(22px) saturate(118%);
            -webkit-backdrop-filter: blur(22px) saturate(118%);
            transform: none;
        }
        .st-key-editorial-product-nav [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 4px !important;
            max-width: 640px;
            margin: 0 auto;
        }
        .st-key-editorial-product-nav [data-testid="stHorizontalBlock"] > div {
            width: auto !important;
            min-width: 0 !important;
        }
        .st-key-editorial-product-nav .stButton button {
            min-height: 48px;
            padding: 6px 4px;
            border-color: transparent !important;
            font-size: 13px;
        }
        .st-key-editorial-product-nav .stButton button[kind="secondary"] {
            background: transparent !important;
        }
        .st-key-editorial-product-nav .stButton button[kind="primary"] {
            background: var(--ms-accent-soft) !important;
            border-color: rgba(242, 168, 95, .30) !important;
            color: var(--ms-action) !important;
        }
        .st-key-editorial-product-nav .stButton button[kind="primary"] p,
        .st-key-editorial-product-nav .stButton button[kind="primary"] span {
            color: var(--ms-action) !important;
        }
        body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"]::before {
            inset: 0;
            border-right: 0;
            border-left: 0;
            border-radius: 0;
        }
        body:not(:has(.st-key-ms2-home)) .ms2-page-hero {
            margin-bottom: 18px;
            padding: 26px 20px;
            border-radius: 22px;
        }
        body:not(:has(.st-key-ms2-home)) .ms2-page-hero h1 {
            font-size: clamp(3rem, 18vw, 4.7rem) !important;
        }
        body:not(:has(.st-key-ms2-home)):has(.ms2-page-hero)
        div[data-testid="stHorizontalBlock"]:has(h3) > div[data-testid="stColumn"] {
            min-height: 0;
            padding: 18px 16px;
        }
        .ms-product-celestial-canvas { opacity: .14; }
        .st-key-ms5-profile-card [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) !important;
            gap: 12px !important;
        }
        .st-key-ms5-profile-card [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
        }
        .st-key-ms-term-dictionary [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 8px !important;
        }
        .st-key-ms-term-dictionary [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            min-width: 0 !important;
        }
        .mingshu-hero, .mingshu-bottom-cta { padding: 24px 18px !important; }
        .mingshu-hero-title { font-size: 32px !important; }
        .mingshu-dashboard-grid, .mingshu-hero-grid { grid-template-columns: 1fr !important; }
        body:not(:has(.st-key-ms2-home)) [data-testid="stMainBlockContainer"] h1 { font-size: 2.45rem; }
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
        .ms-term-facts { grid-template-columns: 1fr; }
        .ms5-stepper { grid-template-columns: 1fr; }
        .st-key-ms-report-empty { margin: 16px 0; padding: 22px 18px; }
        .st-key-ms-life-empty { margin: 24px 0; padding: 24px 18px; }
        .st-key-ms-report-empty [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) !important;
        }
        .st-key-ms-report-empty [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
        }
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
