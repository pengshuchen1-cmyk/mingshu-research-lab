from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_chunui_web_shell_has_single_column_type_card_and_motion_contracts():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

    assert "width: min(100%, 920px) !important" in css
    assert "font-size: var(--cc-font-lg) !important" in css
    assert "font-size: var(--cc-font-base) !important" in css
    assert "font-size: var(--cc-font-sm) !important" in css
    assert "border-radius: var(--cc-radius-card) !important" in css
    assert "min-height: 54px" in css
    assert "min-height: 58px !important" in css
    assert "transform: scale(.97) !important" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    reduced = css.rsplit("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert "animation: none !important" in reduced


def test_chunui_primitives_expose_floating_header_apple_card_and_empty_state_hooks():
    source = (ROOT / "ui" / "primitives.py").read_text(encoding="utf-8")

    assert "cc-floating-page-header" in source
    assert "cc-apple-card" in source
    assert "cc-empty-state" in source
    assert "escape(str(title))" in source
    assert "unsafe_allow_html=True" in source


def test_chunui_today_score_and_profile_cards_are_visually_quiet():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]

    assert ".ms-today-score-copy strong { font-size: var(--cc-font-lg) !important; }" in final
    assert ".ms-my-summary h2" in final
    assert "color: var(--cc-foreground) !important" in final
    assert "background: var(--cc-card) !important" in final
    small_copy = final.rsplit(
        ".ms-today-score-copy span,", 1
    )[1].split("}", 1)[0]
    assert ".ms-today-score-copy small" in small_copy
    assert ".ms-today-score-copy p" in small_copy
    assert ".ms-reflection-card > span" in small_copy
    assert "font-size: var(--cc-font-sm) !important" in small_copy
    facts = final.split(".ms-my-facts strong {", 1)[1].split("}", 1)[0]
    assert "font-size: var(--cc-font-base) !important" in facts


def test_inquiry_input_dock_clears_floating_tabbar_and_safe_area():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]

    assert 'body:has(.st-key-ms-inquiry-page) [data-testid="stBottom"]' in final
    assert "bottom: calc(92px + env(safe-area-inset-bottom))" in final
    assert "left: 50vw !important" in final
    assert "width: min(calc(100vw - 32px), 880px)" in final
    assert "transform: translateX(-50%) !important" in final
    assert "background: transparent !important" in final
    assert '[data-testid="stBottomBlockContainer"]' in final


def test_content_cards_and_inputs_clear_legacy_heavy_blur_but_chrome_keeps_light_blur():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    no_blur = final.split(
        'body:not(:has(.st-key-ms2-home)):has(.ms2-page-hero)', 1
    )[1].split("}", 1)[0]

    for selector in (
        'div[data-testid="stExpander"]',
        'div[data-testid="stForm"]',
        '[data-testid="stNotification"]',
        '[data-testid="stChatInput"]',
        '[data-testid="stFileUploaderDropzone"]',
    ):
        assert selector in no_blur
    assert "backdrop-filter: none !important" in no_blur
    assert "-webkit-backdrop-filter: none !important" in no_blur
    nav = final.split(".st-key-editorial-product-nav {", 1)[1].split("}", 1)[0]
    assert "backdrop-filter: blur(12px)" in nav


def test_tab_active_state_keeps_stable_height_while_ai_remains_emphasized():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    active = final.split(
        '.st-key-editorial-product-nav .stButton button[kind="primary"] {', 1
    )[1].split("}", 1)[0]
    inquiry = final.split(
        ".st-key-editorial_nav_inquiry .stButton button,", 1
    )[1].split("}", 1)[0]

    assert "min-height: 54px !important" in active
    assert "min-height: 58px !important" in inquiry


def test_ai_tab_uses_soft_green_while_form_indicators_remain_neutral():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]

    inquiry_copy = final.split(
        ".st-key-editorial-product-nav .st-key-editorial_nav_inquiry .stButton button p,",
        1,
    )[1].split("}", 1)[0]
    assert 'button[kind="primary"] p' in inquiry_copy
    assert 'button[kind="secondary"] p' in inquiry_copy
    assert "color: var(--cc-primary-foreground) !important" in inquiry_copy
    assert 'input[type="radio"], input[type="checkbox"]' in final
    assert "accent-color: #52525B !important" in final
    assert '[role="radio"][aria-checked="true"]' in final
    assert 'label[data-testid="stRadioOption"][data-selected="true"] > div > div > div' in final
    assert '[data-testid="stCheckbox"] label:has(input:checked)' in final
    assert 'button[data-testid="stBaseButton-primary"] div[data-testid="stMarkdownContainer"] p' in final
    assert 'button[data-testid="stBaseButton-secondary"] div[data-testid="stMarkdownContainer"] p' in final
    precise_rule = final.split(
        'button[data-testid="stBaseButton-primary"] div[data-testid="stMarkdownContainer"] p,',
        1,
    )[1].split("}", 1)[0]
    assert "color: var(--cc-primary-foreground) !important" in precise_rule


def test_form_controls_have_one_neutral_shell_and_unstyled_inner_control():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]

    shell = final.split('.stTextInput div[data-baseweb="input"],', 1)[1].split("}", 1)[0]
    assert '.stTextArea div[data-baseweb="base-input"]' in shell
    assert '.stApp [data-testid="stTextInputRootElement"]' in shell
    assert '.stApp [data-testid="stTextAreaRootElement"]' in shell
    assert '.stSelectbox div[role="group"]' in shell
    assert "border: .5px solid var(--cc-border) !important" in shell
    assert "box-shadow: none !important" in shell
    inner = final.split(".stTextInput input,", 1)[1].split("}", 1)[0]
    assert ".stTextArea textarea" in inner
    assert '.stApp [data-testid="stTextInputRootElement"] input' in inner
    assert '.stApp [data-testid="stTextAreaRootElement"] textarea' in inner
    assert '.stSelectbox input[role="combobox"]' in inner
    assert "border: 0 !important" in inner
    assert "outline: 0 !important" in inner
    assert "box-shadow: none !important" in inner
    keyboard_focus = final.split(
        '.stApp .stTextInput input:not([role="combobox"]):focus-visible,', 1
    )[1].split("}", 1)[0]
    assert ".stApp .stTextArea textarea:focus-visible" in keyboard_focus
    assert '[data-testid="stTextInputRootElement"] input:focus-visible' in keyboard_focus
    assert "outline: 0 !important" in keyboard_focus
    assert "box-shadow: none !important" in keyboard_focus
    focus = final.split('.stTextInput div[data-baseweb="input"]:focus-within,', 1)[1].split("}", 1)[0]
    assert '.stApp [data-testid="stTextInputRootElement"]:focus-within' in focus
    assert '.stApp [data-testid="stTextAreaRootElement"]:focus-within' in focus
    assert "border: 1px solid rgba(0,0,0,.36) !important" in focus
    assert "outline: 0 !important" in focus
    assert "box-shadow: none !important" in focus
    assert "outline: 2px solid" not in focus
    assert "var(--cc-primary)" not in focus
    selected = final.split('[role="listbox"] [role="option"][aria-selected="true"] {', 1)[1].split("}", 1)[0]
    assert "background: #EEEEF0 !important" in selected
    assert "var(--cc-primary)" not in selected
    portal_selector = 'body:not(:has(.st-key-ms2-home)) [role="listbox"] [role="option"][aria-selected="true"]'
    assert portal_selector in final
    assert 'body:not(:has(.st-key-ms2-home)) [role="listbox"] [role="option"]:hover > *' in final
    assert '.stApp [role="listbox"] [role="option"][aria-selected="true"]' not in final
    precise_selected = final.split(
        portal_selector + " {", 1
    )[1].split("}", 1)[0]
    assert "background: #EEEEF0 !important" in precise_selected
    assert "color: var(--cc-foreground) !important" in precise_selected


def test_soft_green_is_button_only_and_magenta_is_forbidden():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    master = (ROOT / "design-system" / "chunui" / "MASTER.md").read_text(encoding="utf-8")
    combined = (css + master).lower().replace(" ", "")

    assert "#ff0a78" not in combined
    assert "255,10,120" not in combined
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    primary = final.split('.stApp .stButton button[kind="primary"]', 1)[1].split("}", 1)[0]
    assert "background: var(--cc-primary) !important" in primary
    assert "color: var(--cc-primary-foreground) !important" in primary
    assert 'button[kind="primaryFormSubmit"]' in final
    assert 'button[data-testid="stBaseButton-primaryFormSubmit"]' in final
    active = final.split('.st-key-editorial-product-nav .stButton button[kind="primary"] {', 1)[1].split("}", 1)[0]
    assert "background: #E9E9EC !important" in active
    assert "border: 0 !important" in active
    for key in ("today", "chart", "report", "account"):
        assert f".st-key-editorial_nav_{key} .stButton button[kind=\"primary\"]" in final


def test_empty_state_hooks_remove_nested_cards_and_colored_marker():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    rule = final.split(".ms-ui-empty-state-copy,", 1)[1].split("}", 1)[0]

    assert ".st-key-ms-life-empty" in rule
    assert ".st-key-ms-report-empty" in rule
    assert "border: 0 !important" in rule
    assert "background: transparent !important" in rule
    assert "box-shadow: none !important" in rule
    assert ".ms-ui-empty-state-mark { display: none !important; }" in final


def test_profile_step_active_state_is_neutral_not_green():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    active = final.split(".ms5-step.active {", 1)[1].split("}", 1)[0]

    assert "background: #E9E9EC !important" in active
    assert "border-color: var(--cc-border) !important" in active
    assert "color: var(--cc-foreground) !important" in active
    assert "var(--cc-primary)" not in active
    assert "var(--ms-accent-soft)" not in active


def test_profile_page_uses_main_axis_without_nested_card_shell():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    axis = final.split("body:has(.st-key-ms5-profile-card) .st-key-ms5-profile-card,", 1)[1].split("}", 1)[0]
    shell = final.split(
        ".st-key-ms5-profile-card,\n    .st-key-ms5-profile-card > div,", 1
    )[1].split("}", 1)[0]

    assert ".st-key-ms5-profile-card" in axis
    assert "width: 100% !important" in axis
    assert "max-width: none !important" in axis
    assert 'div[data-testid="stVerticalBlockBorderWrapper"]' in shell
    assert 'div[data-testid="stForm"]' in shell
    assert "border: 0 !important" in shell
    assert "background: transparent !important" in shell
    assert "box-shadow: none !important" in shell
    precise_form = final.split(
        'body:has(.st-key-ms5-profile-card) .st-key-ms5-profile-card div[data-testid="stForm"] {',
        1,
    )[1].split("}", 1)[0]
    assert "border: 0 !important" in precise_form
    assert "background: transparent !important" in precise_form
    assert "box-shadow: none !important" in precise_form


def test_profile_controls_are_flat_without_radio_pills_or_field_shadows():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    radio = final.split(
        'body:has(.st-key-ms5-profile-card) div[role="radiogroup"] label,',
        1,
    )[1].split("}", 1)[0]
    fields = final.split(
        "body:has(.st-key-ms5-profile-card) .st-key-ms5-profile-card .stButton button,",
        1,
    )[1].split("}", 1)[0]

    assert 'label:has(input:checked)' in radio
    assert 'label[data-testid="stRadioOption"][data-selected="true"]' in radio
    assert "border-radius: 0 !important" in radio
    assert "background: transparent !important" in radio
    assert "box-shadow: none !important" in radio
    assert '[data-testid="stFormSubmitButton"] button' in fields
    assert '[data-testid="stTextInputRootElement"]' in fields
    assert 'div[data-baseweb="select"] > div' in fields
    assert "box-shadow: none !important" in fields


def test_page_header_backing_spans_main_axis_on_desktop_and_mobile():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    desktop = final.split(".ms-ui-page-header {", 1)[1].split("}", 1)[0]
    mobile = final.split("@media (max-width: 640px)", 1)[1]
    mobile_header = mobile.split(".ms-ui-page-header {", 1)[1].split("}", 1)[0]

    assert "width: calc(100% + 40px) !important" in desktop
    assert "max-width: none !important" in desktop
    assert "margin-inline: -20px !important" in desktop
    assert "width: calc(100% + 32px) !important" in mobile_header
    assert "max-width: none !important" in mobile_header


def test_page_headers_use_pale_green_atmosphere_over_gray_content():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]
    header = final.split(
        ".ms-ui-page-header,\n    body:not(:has(.st-key-ms2-home)) .ms2-page-hero {",
        1,
    )[1].split("}", 1)[0]

    assert "--cc-content-background: #f2f4f3" in css
    assert "--cc-header-green: #e2f1e9" in css
    assert "--cc-header-green-soft: #f0f7f3" in css
    assert 'body:not(:has(.st-key-ms2-home)) [data-testid="stAppViewContainer"]' in final
    assert 'body:not(:has(.st-key-ms2-home)) [data-testid="stMain"]' in final
    assert "background: var(--cc-content-background) !important" in final
    assert "radial-gradient(circle at 88% 10%" in header
    assert "linear-gradient(135deg, var(--cc-header-green)" in header
    assert "border-bottom: .5px solid rgba(23, 78, 60, .08) !important" in header
    assert "box-shadow: none !important" in header
    assert "backdrop-filter" not in header
    assert ".ms-ui-page-header .ms-ui-eyebrow" in final
    assert ".ms-ui-page-header .ms-ui-page-description" in final


def test_preview_summary_is_compact_structured_and_mobile_safe():
    css = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
    final = css.split("/* ChunUI Web SSOT", 1)[1]

    assert ".ms5-preview-summary" in final
    assert "grid-template-columns: minmax(88px, .32fr) minmax(0, 1fr)" in final
    assert "overflow-wrap: anywhere" in final
    mobile = final.split("@media (max-width: 640px)", 1)[1]
    assert ".ms5-preview-row { grid-template-columns: 1fr" in mobile
