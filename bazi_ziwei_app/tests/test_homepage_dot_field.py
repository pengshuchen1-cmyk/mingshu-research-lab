from importlib import import_module
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ui" / "homepage_dot_field.py"


def _dot_field_module():
    assert MODULE_PATH.exists(), "homepage dot-field module has not been implemented"
    return import_module("ui.homepage_dot_field")


def test_dot_field_config_matches_approved_design():
    module = _dot_field_module()

    assert module.get_dot_field_config() == {
        "color": "#7892AE",
        "spacing": 20,
        "base_radius": 1.4,
        "active_radius": 2.2,
        "base_opacity": 0.35,
        "active_opacity": 0.60,
        "cursor_radius": 120,
        "max_displacement": 5,
        "touch_duration_ms": 350,
    }


def test_dot_field_script_has_scope_accessibility_and_cleanup_contracts():
    module = _dot_field_module()
    script = module.build_dot_field_script()

    for token in [
        "ms2-dot-field-canvas",
        "st-key-ms2-home",
        "prefers-reduced-motion: reduce",
        "requestAnimationFrame",
        "cancelAnimationFrame",
        "ResizeObserver",
        "removeEventListener",
        "pointermove",
        "pointerleave",
        "touchstart",
        "visibilitychange",
    ]:
        assert token in script
    assert "fetch(" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_dot_field_script_draws_grid_and_limits_continuous_motion():
    module = _dot_field_module()
    script = module.build_dot_field_script()

    for token in [
        "context.arc",
        "Math.hypot",
        "devicePixelRatio",
        "root.scrollHeight",
        "pointer: coarse",
        "touchUntil",
        "Date.now()",
        "__ms2DotFieldCleanup()",
    ]:
        assert token in script


def test_dot_field_does_not_keep_animating_when_pointer_is_stationary():
    module = _dot_field_module()
    script = module.build_dot_field_script()

    assert "if (!parentDocument.hidden && canInteract" not in script
    assert "parentWindow.setTimeout(() =>" in script


def test_homepage_does_not_mount_the_dynamic_dot_field():
    source = (ROOT / "ui" / "homepage_components.py").read_text(encoding="utf-8")

    assert "homepage_dot_field" not in source
    assert "render_homepage_dot_field" not in source


def test_homepage_css_does_not_reserve_a_canvas_layer():
    css = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

    assert "#ms2-dot-field-canvas" not in css


def test_dot_field_uses_current_streamlit_iframe_api():
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "streamlit.components.v1" not in source
    assert "st.iframe(" in source
    assert "tab_index=-1" in source
