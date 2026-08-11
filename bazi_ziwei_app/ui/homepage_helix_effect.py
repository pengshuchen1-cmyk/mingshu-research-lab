"""Dependency-free animated celestial helix for the public homepage."""

from __future__ import annotations

import json

import streamlit as st


HELIX_CONFIG = {
    "target_selector": ".st-key-ms2-hero",
    "canvas_class": "ms2-helix-canvas",
    "variant": "home",
    "star_count": 42,
    "helix_samples": 60,
    "rotation_speed": 0.00018,
    "target_fps": 24,
}


def build_helix_background_script(config: dict[str, int | float] | None = None) -> str:
    """Build the parent-page Canvas animation without a remote runtime dependency."""
    payload = json.dumps(config or HELIX_CONFIG)
    template = r"""
    <script>
    (() => {
      const config = __HELIX_CONFIG__;
      const parentWindow = window.parent;
      const parentDocument = parentWindow.document;
      const hero = parentDocument.querySelector(config.target_selector || '.st-key-ms2-hero');
      if (!hero) return;

      if (typeof parentWindow.__ms2HelixCleanup === 'function') {
        parentWindow.__ms2HelixCleanup();
      }

      const canvas = parentDocument.createElement('canvas');
      canvas.className = config.canvas_class || 'ms2-helix-canvas';
      canvas.setAttribute('aria-hidden', 'true');
      canvas.dataset.ms2Helix = 'true';
      canvas.dataset.variant = config.variant || 'home';
      canvas.dataset.frame = '0';
      hero.prepend(canvas);

      // Keep the default compositor path: desynchronized 2D surfaces can advance
      // normally while remaining absent from browser captures and some WebViews.
      const ctx = canvas.getContext('2d', { alpha: true });
      if (!ctx) {
        canvas.remove();
        return;
      }

      const motionQuery = parentWindow.matchMedia('(prefers-reduced-motion: reduce)');
      const compactQuery = parentWindow.matchMedia('(max-width: 860px)');
      let reducedMotion = motionQuery.matches;
      let compact = compactQuery.matches;
      let raf = 0;
      let destroyed = false;
      let width = 1;
      let height = 1;
      let dpr = 1;
      let lastPaint = 0;
      let frameCount = 0;
      let backdropCanvas = null;
      let renderedCompact = null;

      const seededRandom = (() => {
        let seed = 0x6d736832;
        return () => {
          seed = (seed * 1664525 + 1013904223) >>> 0;
          return seed / 4294967296;
        };
      })();

      const rebuildBackdrop = () => {
        const backdropDpr = Math.min(dpr, 1);
        const backdropWidth = Math.max(1, Math.round(width * backdropDpr));
        const backdropHeight = Math.max(1, Math.round(height * backdropDpr));
        backdropCanvas = typeof parentWindow.OffscreenCanvas === 'function'
          ? new parentWindow.OffscreenCanvas(backdropWidth, backdropHeight)
          : parentDocument.createElement('canvas');
        backdropCanvas.width = backdropWidth;
        backdropCanvas.height = backdropHeight;
        const backdropCtx = backdropCanvas.getContext('2d', { alpha: true });
        if (!backdropCtx) return;
        backdropCtx.setTransform(backdropDpr, 0, 0, backdropDpr, 0, 0);

        const glow = backdropCtx.createRadialGradient(
          width * (compact ? .82 : .78), height * .47, 0,
          width * (compact ? .82 : .78), height * .47,
          Math.max(width, height) * (compact ? .44 : .50),
        );
        glow.addColorStop(0, 'rgba(194, 61, 19, .18)');
        glow.addColorStop(.34, 'rgba(111, 31, 21, .10)');
        glow.addColorStop(1, 'rgba(2, 5, 15, 0)');
        backdropCtx.fillStyle = glow;
        backdropCtx.fillRect(0, 0, width, height);

        const starCount = compact ? Math.round(config.star_count * .55) : config.star_count;
        for (let index = 0; index < starCount; index += 1) {
          const x = seededRandom() * width;
          const y = seededRandom() * height;
          const radius = (.45 + seededRandom() * 1.25) * (compact ? .78 : 1);
          const alpha = .22 + seededRandom() * .56;
          backdropCtx.beginPath();
          backdropCtx.arc(x, y, radius, 0, Math.PI * 2);
          backdropCtx.fillStyle = `rgba(255, 224, 177, ${alpha})`;
          backdropCtx.fill();
        }
      };

      const resize = (force = false) => {
        const bounds = hero.getBoundingClientRect();
        const nextWidth = Math.max(1, Math.round(bounds.width));
        const nextHeight = Math.max(1, Math.round(bounds.height));
        if (
          !force
          && nextWidth === width
          && nextHeight === height
          && renderedCompact === compact
        ) return false;
        width = nextWidth;
        height = nextHeight;
        renderedCompact = compact;
        const requestedDpr = Math.min(parentWindow.devicePixelRatio || 1, 2);
        const maxBackingPixels = 4000000;
        const pixelBudgetDpr = Math.sqrt(maxBackingPixels / Math.max(1, width * height));
        dpr = Math.min(requestedDpr, pixelBudgetDpr);
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        rebuildBackdrop();
        return true;
      };

      const pointAt = (t, strand, rotation) => {
        const turns = compact ? 2.05 : 2.35;
        const phase = t * Math.PI * 2 * turns + rotation + (strand ? Math.PI : 0);
        const startX = compact ? .55 : .52;
        const startY = compact ? -.12 : -.18;
        const endX = compact ? .92 : .90;
        const endY = compact ? .92 : 1.14;
        const baseX = width * (startX + (endX - startX) * t);
        const baseY = height * (startY + (endY - startY) * t);
        const axisX = width * (endX - startX);
        const axisY = height * (endY - startY);
        const axisLength = Math.hypot(axisX, axisY) || 1;
        const perpX = -axisY / axisLength;
        const perpY = axisX / axisLength;
        const radius = Math.min(width, height) * (compact ? .13 : .18);
        const depth = Math.sin(phase);
        const offset = Math.cos(phase) * radius;
        const perspective = .70 + (depth + 1) * .19;
        return {
          x: baseX + perpX * offset * perspective,
          y: baseY + perpY * offset * perspective,
          depth,
          perspective,
        };
      };

      const buildHelix = (rotation) => {
        const compactScale = compact ? .72 : 1;
        const sampleCount = Math.max(36, Math.round(config.helix_samples * compactScale));
        const rails = [[], []];

        for (let index = 0; index < sampleCount; index += 1) {
          const t = -.08 + (index / (sampleCount - 1)) * 1.16;
          for (let strand = 0; strand < 2; strand += 1) {
            const point = pointAt(t, strand, rotation);
            rails[strand].push(point);
          }
        }
        return { rails, sampleCount };
      };

      const drawHelix = (rotation) => {
        const { rails, sampleCount } = buildHelix(rotation);
        const sceneAlpha = config.variant === 'product' ? .30 : 1;
        ctx.globalCompositeOperation = 'lighter';
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        // Two broad, batched rail strokes provide glow without per-segment shadows.
        ctx.shadowColor = 'rgba(238, 75, 25, .72)';
        ctx.shadowBlur = compact ? 10 : 16;
        for (const rail of rails) {
          ctx.beginPath();
          rail.forEach((point, index) => {
            if (index === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          });
          ctx.strokeStyle = `rgba(224, 72, 24, ${.18 * sceneAlpha})`;
          ctx.lineWidth = compact ? 7 : 10;
          ctx.stroke();
        }

        // Rungs share one simple stroke; no per-rung gradients or shadows.
        ctx.shadowBlur = 0;
        ctx.beginPath();
        const rungStep = compact ? 7 : 6;
        for (let index = 2; index < sampleCount - 2; index += rungStep) {
          const a = rails[0][index];
          const b = rails[1][index];
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
        }
        ctx.strokeStyle = `rgba(255, 190, 104, ${.58 * sceneAlpha})`;
        ctx.lineWidth = compact ? 1.15 : 1.65;
        ctx.stroke();

        // Rail cores are two continuous paths rather than per-segment primitives.
        rails.forEach((rail, strand) => {
          ctx.beginPath();
          rail.forEach((point, index) => {
            if (index === 0) ctx.moveTo(point.x, point.y);
            else ctx.lineTo(point.x, point.y);
          });
          ctx.strokeStyle = strand
            ? `rgba(255, 111, 36, ${.82 * sceneAlpha})`
            : `rgba(255, 215, 125, ${.90 * sceneAlpha})`;
          ctx.lineWidth = compact ? 1.65 : 2.25;
          ctx.stroke();
        });

        // Nodes are grouped into one fill per strand; depth only changes radius.
        const nodeStep = compact ? 5 : 4;
        rails.forEach((rail, strand) => {
          ctx.beginPath();
          for (let index = 1; index < sampleCount - 1; index += nodeStep) {
            const point = rail[index];
            const foreground = (point.depth + 1) / 2;
            const radius = (compact ? 2.2 : 2.7) + foreground * (compact ? 2.3 : 3.2);
            ctx.moveTo(point.x + radius, point.y);
            ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
          }
          ctx.fillStyle = strand
            ? `rgba(255, 124, 43, ${.88 * sceneAlpha})`
            : `rgba(255, 232, 171, ${.94 * sceneAlpha})`;
          ctx.fill();
        });
        ctx.globalCompositeOperation = 'source-over';
        ctx.shadowBlur = 0;
      };

      const paintFrame = (now) => {
        if (destroyed) return;
        ctx.clearRect(0, 0, width, height);
        if (backdropCanvas) {
          ctx.drawImage(
            backdropCanvas,
            0, 0, backdropCanvas.width, backdropCanvas.height,
            0, 0, width, height,
          );
        }
        const staticFrame = reducedMotion || config.variant === 'product';
        drawHelix(staticFrame ? .72 : now * config.rotation_speed);
        frameCount += 1;
        canvas.dataset.frame = String(frameCount);
      };

      const tick = (now) => {
        if (destroyed || reducedMotion || config.variant === 'product' || parentDocument.hidden) return;
        const configuredFps = compact
          ? Math.min(config.target_fps, 18)
          : Math.min(config.target_fps, 24);
        const targetFps = Math.max(1, configuredFps);
        const frameInterval = 1000 / targetFps;
        if (now - lastPaint >= frameInterval) {
          lastPaint = now;
          paintFrame(now);
        }
        raf = parentWindow.requestAnimationFrame(tick);
      };

      const start = () => {
        if (raf) parentWindow.cancelAnimationFrame(raf);
        raf = 0;
        lastPaint = 0;
        if (reducedMotion || config.variant === 'product') paintFrame(performance.now());
        else if (!parentDocument.hidden) raf = parentWindow.requestAnimationFrame(tick);
      };

      const onMotionChange = (event) => {
        reducedMotion = event.matches;
        if (config.variant !== 'product') start();
      };
      const onCompactChange = (event) => {
        compact = event.matches;
        resize(true);
        start();
      };
      const onVisibilityChange = () => {
        if (parentDocument.hidden) {
          if (raf) parentWindow.cancelAnimationFrame(raf);
          raf = 0;
        } else {
          if (config.variant !== 'product') start();
        }
      };

      const onResize = () => {
        if (!resize()) return;
        if (reducedMotion || config.variant === 'product') paintFrame(performance.now());
      };
      const resizeObserver = new parentWindow.ResizeObserver(onResize);
      resizeObserver.observe(hero);
      parentDocument.addEventListener('visibilitychange', onVisibilityChange);
      motionQuery.addEventListener('change', onMotionChange);
      compactQuery.addEventListener('change', onCompactChange);

      const cleanup = () => {
        if (destroyed) return;
        destroyed = true;
        if (raf) parentWindow.cancelAnimationFrame(raf);
        resizeObserver.disconnect();
        parentDocument.removeEventListener('visibilitychange', onVisibilityChange);
        motionQuery.removeEventListener('change', onMotionChange);
        compactQuery.removeEventListener('change', onCompactChange);
        canvas.remove();
        if (parentWindow.__ms2HelixCleanup === cleanup) {
          delete parentWindow.__ms2HelixCleanup;
        }
      };

      parentWindow.__ms2HelixCleanup = cleanup;
      resize(true);
      start();
    })();
    </script>
    """
    return template.replace("__HELIX_CONFIG__", payload)


def render_helix_background() -> None:
    """Mount the animated canvas through a hidden Streamlit iframe bridge."""
    with st.container(key="ms2-helix-bridge"):
        st.iframe(
            build_helix_background_script(),
            height=1,
            width=1,
            tab_index=-1,
        )


def render_product_background() -> None:
    """Mount a quieter shared celestial backdrop behind all product pages."""
    product_config = {
        **HELIX_CONFIG,
        "target_selector": ".stMain",
        "canvas_class": "ms-product-celestial-canvas",
        "variant": "product",
        "star_count": 30,
        "helix_samples": 48,
        "rotation_speed": 0.00012,
    }
    with st.container(key="ms-product-celestial-bridge"):
        st.iframe(
            build_helix_background_script(product_config),
            height=1,
            width=1,
            tab_index=-1,
        )
