"""Editorial homepage visual system."""


_ELEMENT_PATTERNS = {
    "木": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='160' viewBox='0 0 220 160'%3E%3Cg fill='none' stroke='%236F8D75' stroke-width='1'%3E%3Cpath d='M18 150 C42 110 57 72 67 12 M52 92 C82 78 94 59 108 31 M59 118 C31 103 22 83 17 62'/%3E%3C/g%3E%3C/svg%3E\")",
    "火": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='160' viewBox='0 0 220 160'%3E%3Cg fill='none' stroke='%23B85C4A' stroke-width='1'%3E%3Cpath d='M20 152 C70 126 40 86 88 56 C112 41 103 20 121 6 M91 154 C139 122 116 91 157 62 C179 46 172 23 193 8'/%3E%3C/g%3E%3C/svg%3E\")",
    "土": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='160' viewBox='0 0 240 160'%3E%3Cg fill='none' stroke='%23946F55' stroke-width='1'%3E%3Cpath d='M0 42 C55 27 103 54 156 39 C191 29 215 31 240 38 M0 87 C49 70 105 101 161 82 C191 72 218 74 240 80 M0 132 C58 118 104 143 167 126 C197 118 220 119 240 124'/%3E%3C/g%3E%3C/svg%3E\")",
    "金": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='160' viewBox='0 0 220 160'%3E%3Cg fill='none' stroke='%2371717A' stroke-width='1'%3E%3Cpath d='M14 142 A128 128 0 0 1 178 12 M51 151 A93 93 0 0 1 189 46 M102 154 A53 53 0 0 1 196 100'/%3E%3C/g%3E%3C/svg%3E\")",
    "水": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='160' viewBox='0 0 240 160'%3E%3Cg fill='none' stroke='%235B7187' stroke-width='1'%3E%3Cpath d='M0 38 C32 18 62 58 96 38 S160 18 194 38 S226 58 240 44 M0 82 C32 62 62 102 96 82 S160 62 194 82 S226 102 240 88 M0 126 C32 106 62 146 96 126 S160 106 194 126 S226 146 240 132'/%3E%3C/g%3E%3C/svg%3E\")",
}


def get_homepage_css(element_theme: str = "") -> str:
    """Return the focused homepage CSS with a subtle element line pattern."""
    pattern = _ELEMENT_PATTERNS.get(str(element_theme).strip(), "none")
    return f"""
    <style>
    :root {{
        --ms2-bg: #FAFAFA;
        --ms2-text: #18181B;
        --ms2-muted: #52525B;
        --ms2-line: #E4E4E7;
        --ms2-accent: #EC4899;
        --ms2-paper: #FFFFFF;
    }}

    body:has(.st-key-ms2-home) section[data-testid="stSidebar"] {{
        width: 0 !important;
        min-width: 0 !important;
        transform: translateX(-100%) !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    body:has(.st-key-ms2-home) header[data-testid="stHeader"],
    body:has(.st-key-ms2-home) div[data-testid="stToolbar"],
    body:has(.st-key-ms2-home) div[data-testid="stStatusWidget"],
    body:has(.st-key-ms2-home) div[data-testid="stDecoration"],
    body:has(.st-key-ms2-home) .stDeployButton {{ display: none !important; }}

    body:has(.st-key-ms2-home), body:has(.st-key-ms2-home) .stApp {{ background: var(--ms2-bg); }}
    body:has(.st-key-ms2-home) .main .block-container {{ max-width: 1440px !important; padding: 0 !important; }}
    .st-key-ms2-home, .ms2-home {{ max-width: 1440px; margin: 0 auto; padding: 20px 40px 64px; color: var(--ms2-text); font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }}
    .st-key-ms2-home {{ position: relative; isolation: isolate; overflow: hidden; }}
    #ms2-dot-field-canvas {{ position: absolute; inset: 0; z-index: 0; display: block; pointer-events: none; }}
    .st-key-ms2-home > * {{ position: relative; z-index: 1; }}
    .st-key-ms2-home *, .ms2-home * {{ box-sizing: border-box; }}
    .st-key-ms2-home div[data-testid="stMarkdown"]:has(a[href="#ms2-main"]) {{ position: absolute; left: -9999px; top: auto; }}
    .st-key-ms2-home div[data-testid="stMarkdown"]:has(a[href="#ms2-main"]):focus-within {{ left: 20px; top: 12px; z-index: 1001; }}
    .ms2-product-nav {{ display: flex; justify-content: space-between; align-items: baseline; gap: 20px; padding: 0 0 16px; }}
    .ms2-brand, .ms2-kicker {{ margin: 0; font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
    .ms2-brand {{ font-size: 18px; letter-spacing: .04em; }}
    .ms2-nav-caption {{ margin: 0; color: var(--ms2-muted); font-size: 11px; letter-spacing: .09em; }}
    .st-key-ms2-home [data-testid="stHorizontalBlock"] {{ gap: 12px; }}
    .st-key-ms2-home .stButton > button {{ min-height: 44px; border: 1px solid var(--ms2-text); border-radius: 4px; background: transparent; color: var(--ms2-text); font-size: 14px; font-weight: 700; transition: border-color 180ms ease, color 180ms ease, background-color 180ms ease; touch-action: manipulation; }}
    .st-key-ms2-home .stButton > button:focus-visible {{ outline: 3px solid rgba(236, 72, 153, .35); outline-offset: 2px; }}
    .st-key-ms2-home .stButton > button:hover {{ border-color: var(--ms2-accent); color: var(--ms2-accent); }}
    .st-key-ms2-hero div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child .stButton > button[kind="primary"] {{ min-height: 44px; background: #EC4899; border-color: #EC4899; color: #FFFFFF; }}
    .st-key-ms2-hero div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child .stButton > button[kind="primary"]:hover {{ background: #DB2777; border-color: #DB2777; color: #FFFFFF; }}

    .st-key-ms2-hero {{ position: relative; isolation: isolate; overflow: hidden; border-top: 1px solid var(--ms2-text); border-bottom: 1px solid var(--ms2-text); padding: 48px 0; }}
    .st-key-ms2-hero::before {{ content: ""; position: absolute; inset: 0; z-index: -1; background-image: {pattern}; background-position: left bottom; background-repeat: repeat; opacity: .035; pointer-events: none; }}
    .st-key-ms2-hero div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{ position: relative; z-index: 1; align-self: stretch; }}
    .ms2-hero-copy {{ display: flex; flex-direction: column; justify-content: space-between; min-height: 520px; }}
    .ms2-hero-copy h1 {{ max-width: 7em; font-size: clamp(52px, 7.5vw, 116px); line-height: .98; letter-spacing: -.055em; margin: 0; }}
    .ms2-hero-lede {{ max-width: 34rem; margin: 24px 0 0; color: var(--ms2-muted); font-size: clamp(16px, 1.5vw, 20px); line-height: 1.7; }}

    .ms2-daily-advice {{ align-self: stretch; min-height: 100%; min-width: 0; padding: 28px; border: 1px solid var(--ms2-text); border-radius: 8px; background: rgba(255, 255, 255, .94); display: flex; flex-direction: column; }}
    .ms2-advice-heading {{ display: flex; justify-content: space-between; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--ms2-line); }}
    .ms2-advice-heading p {{ margin: 0; color: var(--ms2-muted); font-size: 12px; }}
    .ms2-daily-advice h2 {{ margin: 24px 0; font-size: clamp(26px, 3vw, 38px); line-height: 1.2; letter-spacing: -.035em; }}
    .ms2-advice-section {{ display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 8px 16px; padding: 16px 0; border-top: 1px solid var(--ms2-line); }}
    .ms2-advice-section > span, .ms2-primary-action > span {{ color: var(--ms2-muted); font-size: 13px; font-weight: 700; }}
    .ms2-advice-section p {{ grid-column: 2; margin: 0; color: var(--ms2-muted); font-size: 14px; line-height: 1.65; }}
    .ms2-element-theme strong {{ font-size: 18px; }}
    .ms2-color-list {{ display: flex; flex-wrap: wrap; gap: 8px 14px; }}
    .ms2-color-chip {{ display: inline-flex; align-items: center; gap: 7px; color: var(--ms2-text); font-size: 14px; font-weight: 700; }}
    .ms2-color-dot {{ width: 14px; height: 14px; flex: 0 0 14px; border: 1px solid rgba(24, 24, 27, .2); border-radius: 50%; background: #A1A1AA; }}
    .ms2-color-green {{ background: #6F8D75; }} .ms2-color-light-blue {{ background: #9DB7C7; }}
    .ms2-color-red {{ background: #B85C4A; }} .ms2-color-orange {{ background: #C97845; }}
    .ms2-color-sand {{ background: #D8C58F; }} .ms2-color-earth {{ background: #946F55; }}
    .ms2-color-white {{ background: #FFFFFF; }} .ms2-color-gold {{ background: #B4975A; }}
    .ms2-color-black {{ background: #18181B; }} .ms2-color-deep-blue {{ background: #4A6178; }}
    .ms2-caution-item + .ms2-caution-item {{ margin-top: 4px; }}
    .ms2-primary-action {{ display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 16px; margin-top: auto; padding: 18px 0; border-top: 1px solid var(--ms2-text); }}
    .ms2-primary-action strong {{ line-height: 1.5; }}
    .ms2-boundary-note {{ margin: 0; padding-top: 14px; border-top: 1px solid var(--ms2-line); color: var(--ms2-muted); font-size: 12px; line-height: 1.6; }}
    .ms2-boundary-note strong {{ margin-right: 8px; color: var(--ms2-text); }}

    @media (max-width: 768px) {{
        .st-key-ms2-home, .ms2-home {{ padding: 12px 20px 48px; }}
        .ms2-product-nav {{ align-items: flex-start; flex-direction: column; }}
        .st-key-ms2-hero {{ padding: 32px 0; }}
        .st-key-ms2-hero div[data-testid="stHorizontalBlock"] {{ flex-direction: column; gap: 32px; }}
        .st-key-ms2-hero div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{ width: 100% !important; }}
        .ms2-hero-copy {{ min-height: auto; }}
        .ms2-daily-advice {{ padding: 20px; }}
        .st-key-ms2-home [data-testid="stHorizontalBlock"] {{ gap: 8px; flex-wrap: wrap; }}
        .st-key-ms2-home [data-testid="stHorizontalBlock"] > div {{ flex: 1 1 calc(50% - 4px) !important; min-width: 0 !important; }}
    }}

    @media (max-width: 420px) {{
        .ms2-advice-heading {{ align-items: flex-start; flex-direction: column; gap: 6px; }}
        .ms2-advice-section, .ms2-primary-action {{ grid-template-columns: 1fr; gap: 8px; }}
        .ms2-advice-section p {{ grid-column: 1; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        #ms2-dot-field-canvas {{ transform: none !important; }}
        .st-key-ms2-home *, .st-key-ms2-home *::before, .st-key-ms2-home *::after {{ scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }}
    }}
    </style>
    """
