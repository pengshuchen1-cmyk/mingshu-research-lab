"""Origin-inspired immersive homepage visual system."""


def get_homepage_css() -> str:
    """Return homepage-only CSS; inner shadcn Shadow DOM remains untouched."""
    return """
    <style>
    :root {
        --ms2-ink: #FFFFFF;
        --ms2-muted: rgba(255, 255, 255, .74);
        --ms2-glass: rgba(255, 255, 255, .11);
        --ms2-glass-strong: rgba(11, 35, 55, .20);
        --ms2-line: rgba(255, 255, 255, .20);
        --ms2-focus: #FFFFFF;
    }

    body:has(.st-key-ms2-home) section[data-testid="stSidebar"] {
        width: 0 !important;
        min-width: 0 !important;
        transform: translateX(-100%) !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    body:has(.st-key-ms2-home) header[data-testid="stHeader"],
    body:has(.st-key-ms2-home) div[data-testid="stToolbar"],
    body:has(.st-key-ms2-home) div[data-testid="stStatusWidget"],
    body:has(.st-key-ms2-home) div[data-testid="stDecoration"],
    body:has(.st-key-ms2-home) .stDeployButton { display: none !important; }

    body:has(.st-key-ms2-home),
    body:has(.st-key-ms2-home) #root,
    body:has(.st-key-ms2-home) .stApp,
    body:has(.st-key-ms2-home) .stMain,
    body:has(.st-key-ms2-home) .stMain > div,
    body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"] {
        background: transparent !important;
    }
    body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: none !important;
        min-height: 100dvh;
        padding: 24px !important;
    }
    .st-key-ms2-home {
        width: 100%;
        color: var(--ms2-ink);
        font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    .st-key-ms2-home *, .st-key-ms2-home *::before, .st-key-ms2-home *::after {
        box-sizing: border-box;
    }
    .st-key-ms2-home > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-typing-placeholder-bridge),
    .st-key-ms2-typing-placeholder-bridge {
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        margin: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    .st-key-ms2-hero {
        position: relative;
        z-index: 1;
        display: grid;
        width: calc(100% + 48px) !important;
        max-width: none !important;
        min-height: max(808px, 100dvh);
        place-items: center;
        overflow: hidden;
        margin: -60px -24px -24px;
        padding: 0;
    }
    .st-key-ms2-hero::before,
    .st-key-ms2-hero::after {
        position: absolute;
        inset: 0;
        z-index: 1;
        pointer-events: none;
        content: "";
    }
    .st-key-ms2-hero::before {
        background:
            linear-gradient(180deg, rgba(3, 31, 55, .10) 0%, rgba(3, 27, 48, .08) 42%, rgba(4, 17, 29, .78) 100%),
            linear-gradient(90deg, rgba(3, 28, 49, .18), transparent 48%, rgba(3, 28, 49, .10));
    }
    .st-key-ms2-hero::after {
        background: linear-gradient(180deg, transparent 68%, rgba(3, 12, 20, .40) 100%);
    }
    .st-key-ms2-hero > div[data-testid="stElementContainer"]:has([data-testid="stImage"]) {
        position: absolute !important;
        inset: 0;
        z-index: 0;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        pointer-events: none;
    }
    .st-key-ms2-hero > div[data-testid="stElementContainer"]:has([data-testid="stImage"]) > div,
    .st-key-ms2-hero > div[data-testid="stElementContainer"]:has([data-testid="stImage"])
    [data-testid="stFullScreenFrame"],
    .st-key-ms2-hero > div[data-testid="stElementContainer"]:has([data-testid="stImage"])
    [data-testid="stFullScreenFrame"] > div,
    .st-key-ms2-hero [data-testid="stImageContainer"],
    .st-key-ms2-hero [data-testid="stImage"] {
        width: 100% !important;
        height: 100% !important;
    }
    .st-key-ms2-hero [data-testid="stImage"] img {
        display: block;
        width: 100% !important;
        height: 100% !important;
        object-fit: cover;
        object-position: center center;
    }
    .st-key-ms2-hero > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-hero-content) {
        position: absolute !important;
        inset: 0;
        z-index: 3;
        display: flex !important;
        width: 100% !important;
        max-width: none !important;
        height: 100% !important;
        margin: 0 !important;
        padding: clamp(160px, 23vh, 224px) 32px 56px;
        align-items: center;
        justify-content: center;
    }
    .st-key-ms2-hero-content {
        position: relative;
        z-index: 3;
        flex: 0 1 1120px !important;
        width: min(100%, 1120px) !important;
        max-width: 1120px !important;
        margin: 0 auto;
        text-align: center;
    }
    .st-key-ms2-hero-content > div { width: 100%; }
    .st-key-ms2-hero-content [data-testid="stMarkdownContainer"] p,
    .st-key-ms2-hero-content [data-testid="stMarkdownContainer"] strong {
        color: inherit !important;
    }
    .ms2-hero-copy { margin-top: 0; }
    .ms2-hero-copy h1 {
        margin: 0;
        color: var(--ms2-ink) !important;
        font-family: "Noto Serif SC", "Songti SC", STSong, Georgia, serif;
        font-size: clamp(60px, 7vw, 96px);
        font-weight: 300;
        line-height: .96;
        letter-spacing: -.065em;
        text-wrap: balance;
        text-shadow: 0 2px 28px rgba(1, 13, 23, .18);
    }
    .ms2-hero-copy h1 em { font-weight: 300; }
    .st-key-ms2-hero-content [data-testid="stMarkdownContainer"] .ms2-hero-lede {
        margin: 36px auto 0;
        color: rgba(255, 255, 255, .74) !important;
        font-size: clamp(16px, 1.55vw, 20px);
        font-weight: 400;
        line-height: 1.65 !important;
        text-shadow: 0 1px 18px rgba(1, 13, 23, .26);
    }
    .st-key-ms2-hero-content [data-testid="stMarkdownContainer"] .ms2-hero-lede strong {
        color: #FFFFFF !important;
        font-weight: 650;
    }

    .st-key-ms2-question-composer {
        position: relative;
        width: min(100%, 1040px);
        margin: 32px auto 0;
        padding: 8px;
        border: 1px solid var(--ms2-line);
        border-radius: 999px;
        background: var(--ms2-glass);
        box-shadow: 0 18px 28px rgba(0, 0, 0, .20);
        backdrop-filter: blur(24px) saturate(110%);
        -webkit-backdrop-filter: blur(24px) saturate(110%);
        text-align: left;
    }
    .st-key-ms2-question-composer > div:first-child [data-testid="stHorizontalBlock"] {
        position: relative;
        display: block !important;
        min-height: 64px;
    }
    .st-key-ms2-question-composer > div:first-child [data-testid="stHorizontalBlock"]
    > div[data-testid="stColumn"]:first-child {
        width: 100% !important;
        min-width: 0 !important;
        flex: 0 0 100% !important;
    }
    .st-key-ms2-question-composer > div:first-child [data-testid="stHorizontalBlock"]
    > div[data-testid="stColumn"]:last-child {
        position: absolute !important;
        top: 5px;
        right: 5px;
        z-index: 4;
        width: 54px !important;
        min-width: 54px !important;
        height: 54px;
        flex: 0 0 54px !important;
    }
    .st-key-ms2-question-composer [data-testid="stColumn"] { min-width: 0 !important; }
    .st-key-ms2-question-composer > div { width: 100%; }
    .st-key-ms2-hero-content [data-testid="stMarkdownContainer"] .ms2-trust-note {
        margin: 22px 0 0 !important;
        color: rgba(255, 255, 255, .68) !important;
        font-size: 13px;
        letter-spacing: .08em;
        line-height: 1.5 !important;
        text-align: center;
    }

    @media (max-width: 768px) {
        body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"]
        > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }
        body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"] {
            min-height: 100dvh;
            padding: 0 16px !important;
        }
        .st-key-ms2-hero {
            width: calc(100% + 32px) !important;
            min-height: 100dvh;
            margin: 0 -16px;
            padding: 0;
        }
        .st-key-ms2-hero > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-hero-content) {
            padding: max(72px, env(safe-area-inset-top)) 20px 48px;
        }
        .st-key-ms2-hero-content { width: min(100%, 560px); }
        .ms2-hero-copy { margin-top: 18px; }
        .ms2-hero-copy h1 {
            font-size: clamp(48px, 15vw, 68px);
            line-height: 1.02;
        }
        .ms2-hero-lede {
            margin-top: 24px;
            font-size: 16px;
        }
        .ms2-hero-lede br { display: none; }
        .st-key-ms2-question-composer {
            margin-top: 28px;
            padding: 6px;
            border-radius: 999px;
        }
        .st-key-ms2-question-composer > div:first-child [data-testid="stHorizontalBlock"] {
            display: block !important;
            min-height: 56px;
        }
        .st-key-ms2-question-composer > div:first-child [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:last-child {
            top: 5px;
            right: 5px;
            width: 48px !important;
            min-width: 48px !important;
            height: 48px;
            flex-basis: 48px !important;
        }
        .ms2-trust-note { font-size: 12px; letter-spacing: .04em; }
    }

    @media (max-width: 420px) {
        .st-key-ms2-hero { padding-right: 16px; padding-left: 16px; }
        .ms2-hero-copy h1 { font-size: 50px; }
        .st-key-ms2-question-composer { width: 100%; }
    }

    @media (max-width: 768px) and (orientation: landscape) {
        .st-key-ms2-hero { min-height: 680px; }
    }

    @media (prefers-reduced-motion: reduce) {
        .st-key-ms2-home *, .st-key-ms2-home *::before, .st-key-ms2-home *::after {
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
        }
    }
    </style>
    """
