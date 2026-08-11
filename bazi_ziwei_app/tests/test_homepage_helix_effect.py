from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source() -> str:
    return (ROOT / "ui" / "homepage_helix_effect.py").read_text(encoding="utf-8")


def test_helix_uses_local_canvas_animation_without_remote_runtime():
    source = _source()

    assert source.count("hero.prepend(canvas)") == 1
    assert "getContext('2d', { alpha: true })" in source
    assert "desynchronized: true" not in source
    for token in [
        "createElement('canvas')",
        "requestAnimationFrame",
        "ResizeObserver",
        "drawHelix",
        "rebuildBackdrop",
        "ctx.drawImage(",
        "globalCompositeOperation = 'lighter'",
    ]:
        assert token in source
    for remote in ["https://", "http://", "three.min.js", "cdn.jsdelivr"]:
        assert remote not in source


def test_helix_batches_two_rails_rungs_nodes_and_glow():
    source = _source()

    assert "const rails = [[], []]" in source
    assert "for (let strand = 0; strand < 2" in source
    assert "ctx.lineTo(b.x, b.y)" in source
    assert "const rungStep = compact ? 7 : 6" in source
    assert "const nodeStep = compact ? 5 : 4" in source
    assert "rails.forEach((rail, strand)" in source
    assert source.count("ctx.shadowBlur") <= 3
    assert "createLinearGradient" not in source
    assert "primitives.sort" not in source


def test_home_helix_has_one_dominant_multi_turn_scene():
    source = _source()

    assert "const turns = compact ? 2.05 : 2.35" in source
    assert source.count("const drawHelix =") == 1
    assert source.count("drawHelix(") == 1
    assert "paintHelix" not in source
    assert "layer === 'depth'" not in source
    assert "startX = compact ? .55 : .52" in source


def test_helix_axis_stays_centered_inside_the_viewport():
    source = _source()

    assert "endX = compact ? .92 : .90" in source
    assert "Math.min(width, height) * (compact ? .13 : .18)" in source


def test_static_atmosphere_and_stars_are_cached_offscreen():
    source = _source()

    assert "new parentWindow.OffscreenCanvas" in source
    assert "const backdropDpr = Math.min(dpr, 1)" in source
    assert "rebuildBackdrop()" in source
    assert "ctx.drawImage(" in source
    assert "drawStars" not in source
    assert "star.speed" not in source


def test_animation_is_responsive_accessible_and_cleans_up():
    source = _source()

    assert "prefers-reduced-motion: reduce" in source
    assert "motionQuery.addEventListener('change', onMotionChange)" in source
    assert "Math.min(parentWindow.devicePixelRatio || 1, 2)" in source
    assert "const maxBackingPixels = 4000000" in source
    assert "Math.sqrt(maxBackingPixels / Math.max(1, width * height))" in source
    assert "dpr = Math.min(requestedDpr, pixelBudgetDpr)" in source
    assert "Math.min(config.target_fps, 18)" in source
    assert "Math.min(config.target_fps, 24)" in source
    assert "const compactScale = compact ? .72 : 1" in source
    assert "visibilitychange" in source
    assert "resizeObserver.disconnect()" in source
    assert "cancelAnimationFrame" in source
    assert "aria-hidden" in source
    assert "if (destroyed || reducedMotion || config.variant === 'product' || parentDocument.hidden) return" in source
    assert "if (reducedMotion || config.variant === 'product') paintFrame(performance.now())" in source
    assert "pointer" not in source.lower()


def test_render_loop_has_one_scheduler_and_resize_does_not_spawn_a_loop():
    source = _source()

    assert "requestAnimationFrame(tick)" in source
    assert "requestAnimationFrame(draw)" not in source
    resize = source.split("const resize = (force = false) =>", 1)[1].split("const pointAt", 1)[0]
    assert "requestAnimationFrame" not in resize
    assert "paintFrame" not in resize


def test_unchanged_resize_does_not_reallocate_or_repaint_static_product():
    source = _source()

    assert "let renderedCompact = null" in source
    assert "nextWidth === width" in source
    assert "nextHeight === height" in source
    assert "renderedCompact === compact" in source
    assert ") return false" in source
    assert "if (!resize()) return" in source
    assert source.count("resize(true)") == 2
    assert "if (config.variant !== 'product') start()" in source
    assert "const staticFrame = reducedMotion || config.variant === 'product'" in source


def test_product_variant_reuses_the_animation_with_a_quieter_profile():
    source = _source()

    assert "def render_product_background" in source
    assert '"target_selector": ".stMain"' in source
    assert '"canvas_class": "ms-product-celestial-canvas"' in source
    assert "if (reducedMotion || config.variant === 'product') paintFrame(performance.now())" in source
    product = source.split("def render_product_background", 1)[1]
    assert '"target_fps"' not in product
