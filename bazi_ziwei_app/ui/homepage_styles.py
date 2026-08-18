"""Legacy static homepage visual system."""


def get_homepage_css() -> str:
    """Return homepage-only CSS; Shadcn internals are styled by the input bridge."""
    return """
    <style>
    :root {
        --ms2-ink: #FFFDF9;
        --ms2-muted: rgba(255, 250, 242, .68);
        --ms2-focus: #FFF4DC;
        --ms2-font: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
            "Microsoft YaHei", sans-serif;
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
        background: #030714 !important;
    }
    body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: none !important;
        min-height: 100dvh;
        padding: 24px !important;
    }
    body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"]
    > [data-testid="stVerticalBlock"] { gap: 0 !important; }

    .st-key-ms2-home {
        width: 100%;
        color: var(--ms2-ink);
        font-family: var(--ms2-font);
    }
    .st-key-ms2-home *, .st-key-ms2-home *::before, .st-key-ms2-home *::after {
        box-sizing: border-box;
    }
    .st-key-ms2-home div[data-testid="stLayoutWrapper"]:has(> .st-key-ms2-typing-placeholder-bridge),
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
        grid-template-columns: minmax(0, 1fr);
        width: calc(100% + 48px) !important;
        max-width: none !important;
        min-height: max(680px, 100dvh);
        margin: -24px -24px -24px;
        overflow: hidden;
        isolation: isolate;
        background:
            radial-gradient(circle at 78% 42%, rgba(117, 35, 20, .30), transparent 48%),
            radial-gradient(circle at 15% 84%, rgba(8, 43, 73, .34), transparent 48%),
            #020611;
    }
    .st-key-ms2-hero::before,
    .st-key-ms2-hero::after {
        position: absolute;
        inset: 0;
        pointer-events: none;
        content: "";
    }
    .st-key-ms2-hero::before {
        z-index: 1;
        background:
            linear-gradient(90deg, rgba(2, 6, 18, .72) 0%, rgba(2, 6, 18, .30) 38%, transparent 68%),
            linear-gradient(180deg, rgba(2, 6, 17, .10) 0%, transparent 48%, rgba(2, 5, 12, .36) 100%);
    }
    .st-key-ms2-hero::after {
        z-index: 3;
        background: radial-gradient(ellipse at center, transparent 46%, rgba(1, 3, 10, .38) 100%);
        box-shadow: inset 0 0 150px rgba(0, 0, 0, .34);
    }

    .st-key-ms2-hero > div[data-testid="stElementContainer"]:has([data-testid="stImage"]) {
        position: absolute !important;
        inset: 0;
        z-index: 0;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        opacity: .08;
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
        filter: saturate(.62) contrast(1.08) brightness(.42) blur(.5px);
    }
    .st-key-ms2-hero > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-hero-content) {
        position: absolute !important;
        inset: 0;
        z-index: 4;
        width: 100% !important;
        max-width: none !important;
        height: 100% !important;
        margin: 0 !important;
    }
    .st-key-ms2-hero-content {
        position: relative;
        z-index: 4;
        width: 100% !important;
        height: 100% !important;
        max-width: none !important;
        margin: 0;
        font-family: var(--ms2-font);
    }
    .st-key-ms2-hero-content > div { width: 100%; height: 100%; }

    .ms2-masthead {
        position: absolute;
        top: clamp(28px, 4vh, 48px);
        left: clamp(28px, 4vw, 72px);
        z-index: 8;
        color: #FFFFFF;
        font-family: var(--ms2-font);
    }
    .ms2-brand {
        display: flex;
        gap: 12px;
        align-items: center;
        font-size: 20px;
        font-weight: 720;
        letter-spacing: -.025em;
        text-shadow: 0 2px 16px rgba(0, 0, 0, .26);
    }
    .ms2-brand svg {
        width: 42px;
        height: 32px;
        overflow: visible;
        fill: none;
        stroke: currentColor;
        stroke-width: 2.5;
        stroke-linecap: round;
        stroke-linejoin: round;
    }

    .st-key-ms2-hero-stage {
        position: absolute;
        inset: clamp(108px, 14vh, 148px) clamp(28px, 4vw, 72px) clamp(28px, 4vh, 50px);
        display: flex !important;
        width: auto !important;
        height: auto !important;
        align-items: flex-end;
        margin: 0 !important;
    }
    .st-key-ms2-hero-stage > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-primary-panel) {
        display: contents !important;
    }
    .st-key-ms2-primary-panel {
        position: absolute;
        bottom: clamp(0px, 2vh, 18px);
        left: clamp(16px, 9vw, 156px);
        width: min(100%, 680px) !important;
        height: auto !important;
        margin: 0;
        flex: 0 0 auto !important;
    }
    .st-key-ms2-primary-panel > div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] p,
    .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] strong {
        color: inherit !important;
    }
    .ms2-hero-copy { margin: 0; }
    .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-hero-kicker {
        width: max-content;
        max-width: 100%;
        margin: 0 0 10px;
        color: rgba(255, 253, 249, .88) !important;
        font-size: clamp(20px, 2vw, 28px);
        font-weight: 650;
        line-height: 1.18 !important;
        letter-spacing: -.02em;
        text-shadow: 0 2px 24px rgba(0, 0, 0, .36);
    }
    .ms2-hero-copy h1 {
        margin: 0;
        color: #FFFFFF !important;
        font-family: var(--ms2-font);
        font-size: clamp(100px, 10.8vw, 166px);
        font-weight: 760;
        line-height: .84;
        letter-spacing: -.085em;
        text-shadow: 0 4px 34px rgba(0, 0, 0, .30);
    }
    .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-hero-lede {
        width: max-content;
        max-width: 100%;
        margin: 24px 0 0;
        color: rgba(255, 253, 249, .72) !important;
        font-size: clamp(15px, 1.25vw, 18px);
        font-weight: 480;
        line-height: 1.6 !important;
        text-shadow: 0 1px 18px rgba(0, 0, 0, .42);
    }

    .st-key-ms2-start-action {
        width: max-content !important;
        margin: 24px 0 0;
    }
    .st-key-ms2-start-action .stButton > button {
        min-height: 48px;
        padding: 0 22px;
        border: 1px solid rgba(255, 255, 255, .30) !important;
        border-radius: 999px !important;
        background: rgba(255, 255, 255, .90) !important;
        color: #151319 !important;
        box-shadow: 0 12px 28px rgba(1, 4, 12, .20) !important;
        font-size: 13px;
        font-weight: 780 !important;
        letter-spacing: .07em;
        transition: transform 180ms ease-out, background-color 180ms ease-out, box-shadow 180ms ease-out;
    }
    .st-key-ms2-start-action .stButton > button p,
    .st-key-ms2-start-action .stButton > button span { color: #151319 !important; }
    .st-key-ms2-start-action .stButton > button:hover {
        transform: translateY(-2px);
        background: #FFFFFF !important;
        box-shadow: 0 16px 34px rgba(1, 4, 12, .28) !important;
    }
    .st-key-ms2-start-action .stButton > button:focus-visible {
        outline: 3px solid var(--ms2-focus) !important;
        outline-offset: 3px !important;
    }

    .st-key-ms2-question-composer {
        position: relative;
        width: min(100%, 660px);
        margin: 22px 0 0;
        padding: 7px;
        border: 1px solid rgba(255, 250, 242, .34);
        border-radius: 999px;
        background: rgba(20, 17, 22, .50);
        box-shadow: 0 18px 38px rgba(0, 0, 0, .30);
        backdrop-filter: blur(22px) saturate(118%);
        -webkit-backdrop-filter: blur(22px) saturate(118%);
        text-align: left;
        transition: border-color 180ms ease-out, box-shadow 180ms ease-out;
    }
    .st-key-ms2-question-composer:focus-within {
        border-color: rgba(255, 244, 220, .78);
        box-shadow: 0 0 0 3px rgba(255, 236, 198, .10), 0 18px 38px rgba(0, 0, 0, .32);
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
    .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-trust-note {
        margin: 14px 0 0 !important;
        color: rgba(255, 250, 242, .56) !important;
        font-size: 12px;
        font-weight: 520;
        letter-spacing: .08em;
        line-height: 1.5 !important;
    }

    @media (max-width: 860px) {
        body:has(.st-key-ms2-home) [data-testid="stMainBlockContainer"] {
            min-height: 100dvh;
            padding: 0 16px !important;
        }
        .st-key-ms2-hero {
            width: calc(100% + 32px) !important;
            min-height: 100dvh;
            height: auto;
            margin: 0 -16px;
        }
        .st-key-ms2-hero [data-testid="stImage"] img {
            object-position: 64% center;
            filter: saturate(.56) contrast(1.06) brightness(.34) blur(.6px);
        }
        .st-key-ms2-hero::before {
            background:
                linear-gradient(90deg, rgba(2, 6, 18, .56) 0%, rgba(2, 6, 18, .20) 72%, transparent 100%),
                linear-gradient(180deg, rgba(2, 6, 17, .10) 0%, transparent 45%, rgba(2, 5, 12, .44) 100%);
        }
        .st-key-ms2-hero > div[data-testid="stLayoutWrapper"]:has(.st-key-ms2-hero-content) {
            position: relative !important;
            inset: auto;
            left: 50%;
            width: 100vw !important;
            min-width: 0 !important;
            min-height: 100dvh;
            height: auto !important;
            justify-self: stretch;
            transform: translateX(-50%);
        }
        .st-key-ms2-hero > div[data-testid="stLayoutWrapper"] > .st-key-ms2-hero-content {
            width: 100vw !important;
            min-width: 100vw !important;
            max-width: 100vw !important;
            min-height: 100dvh;
            height: auto !important;
            flex: 0 0 100vw !important;
        }
        .st-key-ms2-hero-content > div { min-height: 0 !important; height: auto !important; }
        .ms2-masthead {
            top: max(22px, env(safe-area-inset-top));
            left: 20px;
        }
        .ms2-brand { gap: 8px; font-size: 16px; }
        .ms2-brand svg { width: 34px; height: 27px; }
        .st-key-ms2-hero-stage {
            position: relative;
            inset: auto;
            display: flex !important;
            width: 100% !important;
            max-width: none !important;
            min-height: 100dvh;
            align-items: flex-start;
            margin: 0 !important;
            padding: max(112px, calc(env(safe-area-inset-top) + 82px)) 20px max(34px, env(safe-area-inset-bottom));
        }
        .st-key-ms2-primary-panel {
            position: static;
            width: 100% !important;
            max-width: 620px;
            height: auto !important;
            margin: 0;
        }
        .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-hero-kicker {
            margin-bottom: 8px;
            font-size: 18px;
        }
        .ms2-hero-copy h1 {
            font-size: clamp(76px, 25vw, 112px);
            line-height: .88;
        }
        .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-hero-lede {
            width: min(100%, 420px);
            margin-top: 18px;
            font-size: 15px;
        }
        .st-key-ms2-start-action { margin-top: 20px; }
        .st-key-ms2-start-action .stButton > button {
            min-height: 46px;
            padding: 0 19px;
            font-size: 12px;
        }
        .st-key-ms2-question-composer {
            width: 100%;
            margin-top: 18px;
            padding: 6px;
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
        .st-key-ms2-primary-panel [data-testid="stMarkdownContainer"] .ms2-trust-note {
            margin-top: 10px !important;
            font-size: 11px;
            letter-spacing: .045em;
        }
    }

    @media (max-width: 430px) {
        .st-key-ms2-hero-stage { padding-right: 16px; padding-left: 16px; }
        .ms2-hero-copy h1 { font-size: 82px; }
    }

    @media (max-width: 860px) and (orientation: landscape) {
        .st-key-ms2-hero { min-height: 640px; }
        .st-key-ms2-hero-stage { min-height: 640px; }
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
