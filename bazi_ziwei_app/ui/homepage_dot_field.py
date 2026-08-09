"""Homepage-only interactive dot-field background."""

from __future__ import annotations

import json

import streamlit as st


DOT_FIELD_CONFIG = {
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


def get_dot_field_config() -> dict[str, object]:
    """Return a copy of the approved visual configuration."""
    return dict(DOT_FIELD_CONFIG)


def build_dot_field_script(config: dict[str, object] | None = None) -> str:
    """Build the parent-page mounting script without external dependencies."""
    payload = json.dumps(config or get_dot_field_config(), ensure_ascii=False)
    template = """
    <script>
    (() => {
      const config = __DOT_FIELD_CONFIG__;
      const parentWindow = window.parent;
      const parentDocument = parentWindow.document;
      const rootSelector = '.st-key-ms2-home';
      const canvasId = 'ms2-dot-field-canvas';
      const reducedMotionQuery = parentWindow.matchMedia('(prefers-reduced-motion: reduce)');
      const coarsePointerQuery = parentWindow.matchMedia('(pointer: coarse)');
      const root = parentDocument.querySelector(rootSelector);
      if (!root) {
        const orphanedCanvas = parentDocument.getElementById(canvasId);
        if (orphanedCanvas) orphanedCanvas.remove();
        return;
      }

      if (typeof parentWindow.__ms2DotFieldCleanup === 'function') {
        parentWindow.__ms2DotFieldCleanup();
      }

      const canvas = parentDocument.createElement('canvas');
      canvas.id = canvasId;
      canvas.setAttribute('aria-hidden', 'true');
      root.prepend(canvas);
      const context = canvas.getContext('2d');
      let animationFrame = 0;
      let touchTimer = 0;
      let pointer = null;
      let touchUntil = 0;
      let destroyed = false;
      let canvasWidth = 0;
      let canvasHeight = 0;
      let pixelRatio = 1;

      const parseHex = (hex) => {
        const value = hex.replace('#', '');
        return [0, 2, 4].map((offset) => parseInt(value.slice(offset, offset + 2), 16));
      };
      const [red, green, blue] = parseHex(config.color);

      const resizeCanvas = () => {
        const rect = root.getBoundingClientRect();
        const width = Math.max(1, Math.round(rect.width));
        const height = Math.max(1, Math.round(root.scrollHeight));
        const ratio = Math.min(parentWindow.devicePixelRatio || 1, 2);
        if (width !== canvasWidth || height !== canvasHeight || ratio !== pixelRatio) {
          canvasWidth = width;
          canvasHeight = height;
          pixelRatio = ratio;
          canvas.width = Math.round(width * ratio);
          canvas.height = Math.round(height * ratio);
          canvas.style.width = `${width}px`;
          canvas.style.height = `${height}px`;
          context.setTransform(ratio, 0, 0, ratio, 0, 0);
        }
        return { width, height, rect };
      };

      const scheduleDraw = () => {
        if (!destroyed && !animationFrame) {
          animationFrame = parentWindow.requestAnimationFrame(draw);
        }
      };

      const draw = () => {
        animationFrame = 0;
        if (destroyed || !root.isConnected) return;
        const { width, height, rect } = resizeCanvas();
        context.clearRect(0, 0, width, height);
        const touchActive = coarsePointerQuery.matches && Date.now() < touchUntil;
        const canInteract = !reducedMotionQuery.matches && pointer &&
          (!coarsePointerQuery.matches || touchActive);
        const localPointer = canInteract
          ? { x: pointer.x - rect.left, y: pointer.y - rect.top }
          : null;

        for (let y = config.spacing / 2; y < height; y += config.spacing) {
          for (let x = config.spacing / 2; x < width; x += config.spacing) {
            const dx = localPointer ? x - localPointer.x : 0;
            const dy = localPointer ? y - localPointer.y : 0;
            const distance = localPointer ? Math.hypot(dx, dy) : config.cursor_radius + 1;
            const influence = Math.max(0, 1 - distance / config.cursor_radius);
            const length = distance || 1;
            const shift = influence * config.max_displacement;
            const drawX = x + (dx / length) * shift;
            const drawY = y + (dy / length) * shift;
            const radius = config.base_radius +
              (config.active_radius - config.base_radius) * influence;
            const opacity = config.base_opacity +
              (config.active_opacity - config.base_opacity) * influence;
            context.beginPath();
            context.arc(drawX, drawY, radius, 0, Math.PI * 2);
            context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${opacity})`;
            context.fill();
          }
        }

      };

      const onPointerMove = (event) => {
        if (coarsePointerQuery.matches || reducedMotionQuery.matches) return;
        pointer = { x: event.clientX, y: event.clientY };
        scheduleDraw();
      };
      const onPointerLeave = () => {
        pointer = null;
        if (animationFrame) parentWindow.cancelAnimationFrame(animationFrame);
        animationFrame = 0;
        scheduleDraw();
      };
      const onTouchStart = (event) => {
        if (reducedMotionQuery.matches || !event.touches || !event.touches[0]) return;
        pointer = { x: event.touches[0].clientX, y: event.touches[0].clientY };
        touchUntil = Date.now() + config.touch_duration_ms;
        scheduleDraw();
        if (touchTimer) parentWindow.clearTimeout(touchTimer);
        touchTimer = parentWindow.setTimeout(() => {
          pointer = null;
          touchUntil = 0;
          touchTimer = 0;
          scheduleDraw();
        }, config.touch_duration_ms);
      };
      const onVisibilityChange = () => {
        if (parentDocument.hidden && animationFrame) {
          parentWindow.cancelAnimationFrame(animationFrame);
          animationFrame = 0;
        } else if (!parentDocument.hidden) {
          scheduleDraw();
        }
      };
      const onMotionPreferenceChange = () => {
        pointer = null;
        touchUntil = 0;
        if (animationFrame) parentWindow.cancelAnimationFrame(animationFrame);
        animationFrame = 0;
        scheduleDraw();
      };

      const resizeObserver = new parentWindow.ResizeObserver(scheduleDraw);
      const mutationObserver = new parentWindow.MutationObserver(() => {
        if (!root.isConnected) cleanup();
      });

      root.addEventListener('pointermove', onPointerMove, { passive: true });
      root.addEventListener('pointerleave', onPointerLeave, { passive: true });
      root.addEventListener('touchstart', onTouchStart, { passive: true });
      parentDocument.addEventListener('visibilitychange', onVisibilityChange);
      resizeObserver.observe(root);
      mutationObserver.observe(parentDocument.body, { childList: true, subtree: true });
      if (typeof reducedMotionQuery.addEventListener === 'function') {
        reducedMotionQuery.addEventListener('change', onMotionPreferenceChange);
      } else if (typeof reducedMotionQuery.addListener === 'function') {
        reducedMotionQuery.addListener(onMotionPreferenceChange);
      }

      const cleanup = () => {
        if (destroyed) return;
        destroyed = true;
        if (animationFrame) parentWindow.cancelAnimationFrame(animationFrame);
        if (touchTimer) parentWindow.clearTimeout(touchTimer);
        resizeObserver.disconnect();
        mutationObserver.disconnect();
        root.removeEventListener('pointermove', onPointerMove);
        root.removeEventListener('pointerleave', onPointerLeave);
        root.removeEventListener('touchstart', onTouchStart);
        parentDocument.removeEventListener('visibilitychange', onVisibilityChange);
        if (typeof reducedMotionQuery.removeEventListener === 'function') {
          reducedMotionQuery.removeEventListener('change', onMotionPreferenceChange);
        } else if (typeof reducedMotionQuery.removeListener === 'function') {
          reducedMotionQuery.removeListener(onMotionPreferenceChange);
        }
        if (canvas.isConnected) canvas.remove();
        if (parentWindow.__ms2DotFieldCleanup === cleanup) {
          delete parentWindow.__ms2DotFieldCleanup;
        }
      };

      parentWindow.__ms2DotFieldCleanup = cleanup;
      scheduleDraw();
    })();
    </script>
    """
    return template.replace("__DOT_FIELD_CONFIG__", payload)


def render_homepage_dot_field() -> None:
    """Mount the homepage dot field through Streamlit's component bridge."""
    with st.container(key="ms2-dot-field-bridge"):
        st.iframe(build_dot_field_script(), height=1, width=1, tab_index=-1)
