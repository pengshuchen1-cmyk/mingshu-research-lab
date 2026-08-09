"""Animated placeholder bridge for the homepage Shadcn question input."""

from __future__ import annotations

import json
from collections.abc import Sequence

import streamlit as st


TYPEWRITER_CONFIG = {
    "typing_delay_ms": 95,
    "deleting_delay_ms": 55,
    "hold_delay_ms": 2000,
    "between_delay_ms": 360,
    "initial_delay_ms": 500,
    "input_height_px": 64,
    "input_font_size_px": 18,
    "input_horizontal_padding_px": 20,
    "input_right_padding_px": 88,
    "submit_button_size_px": 54,
}


def build_question_typing_script(
    questions: Sequence[str],
    config: dict[str, int] | None = None,
) -> str:
    """Build a parent-page script that animates only the input placeholder."""
    normalized_questions = [str(question).strip() for question in questions if str(question).strip()]
    payload = json.dumps(
        {
            "questions": normalized_questions,
            "config": config or TYPEWRITER_CONFIG,
        },
        ensure_ascii=False,
    )
    template = r"""
    <script>
    (() => {
      const payload = __TYPEWRITER_PAYLOAD__;
      const questions = payload.questions;
      const config = payload.config;
      const parentWindow = window.parent;
      const parentDocument = parentWindow.document;
      const root = parentDocument.querySelector('.st-key-ms2-question-composer');
      const reducedMotionQuery = parentWindow.matchMedia('(prefers-reduced-motion: reduce)');
      if (!root || !questions.length) return;

      if (typeof parentWindow.__ms2QuestionTypingCleanup === 'function') {
        parentWindow.__ms2QuestionTypingCleanup();
      }

      let input = null;
      let timer = 0;
      let destroyed = false;
      let questionIndex = 0;
      let characterIndex = 0;
      let phase = 'typing';
      let originalPlaceholder = '';
      let inputOverrideStyle = null;
      let buttonOverrideStyle = null;

      const clearTimer = () => {
        if (timer) parentWindow.clearTimeout(timer);
        timer = 0;
      };

      const schedule = (callback, delay) => {
        clearTimer();
        if (!destroyed) timer = parentWindow.setTimeout(callback, delay);
      };

      const findInput = () => {
        const hosts = root.querySelectorAll('[data-ssui-v2-host]');
        for (const host of hosts) {
          const candidate = host.shadowRoot?.querySelector('input[data-slot="input"]');
          if (candidate) return candidate;
        }
        return null;
      };

      const resetCycle = () => {
        questionIndex = 0;
        characterIndex = 0;
        phase = 'typing';
      };

      const applyPresentation = () => {
        const inputRoot = input?.getRootNode();
        if (inputOverrideStyle && inputOverrideStyle.getRootNode() !== inputRoot) {
          inputOverrideStyle.remove();
          inputOverrideStyle = null;
        }
        if (inputRoot && !inputOverrideStyle) {
          inputOverrideStyle = parentDocument.createElement('style');
          inputOverrideStyle.dataset.ms2QuestionInputOverride = 'true';
          inputOverrideStyle.textContent = `
            [data-ssui-component="input"] {
              gap: 0 !important;
              border: 0 !important;
              background: transparent !important;
              box-shadow: none !important;
            }
            [data-ssui-component="input"] label { display: none !important; }
            input[data-slot="input"] {
              height: ${config.input_height_px}px !important;
              min-height: ${config.input_height_px}px !important;
              padding-right: ${config.input_right_padding_px}px !important;
              padding-left: ${config.input_horizontal_padding_px}px !important;
              border: 0 !important;
              border-radius: 999px !important;
              outline: 0 !important;
              background: transparent !important;
              color: #FFFFFF !important;
              caret-color: #FFFFFF !important;
              box-shadow: none !important;
              font-size: ${config.input_font_size_px}px !important;
            }
            input[data-slot="input"]::placeholder {
              color: rgba(255, 255, 255, .68) !important;
              opacity: 1 !important;
            }
            @media (max-width: 768px) {
              input[data-slot="input"] {
                height: 56px !important;
                min-height: 56px !important;
                padding-right: 72px !important;
                font-size: 16px !important;
              }
            }
          `;
          inputRoot.append(inputOverrideStyle);
        }
        input?.setAttribute('aria-label', '命理问题');

        const buttonHost = Array.from(root.querySelectorAll('[data-ssui-v2-host]'))
          .find((host) => host.shadowRoot?.querySelector('button[data-slot="button"]'));
        const buttonRoot = buttonHost?.shadowRoot;
        if (buttonOverrideStyle && buttonOverrideStyle.getRootNode() !== buttonRoot) {
          buttonOverrideStyle.remove();
          buttonOverrideStyle = null;
        }
        if (buttonRoot && !buttonOverrideStyle) {
          buttonOverrideStyle = parentDocument.createElement('style');
          buttonOverrideStyle.dataset.ms2QuestionButtonOverride = 'true';
          buttonOverrideStyle.textContent = `
            button[data-slot="button"] {
              width: ${config.submit_button_size_px}px !important;
              min-width: ${config.submit_button_size_px}px !important;
              height: ${config.submit_button_size_px}px !important;
              min-height: ${config.submit_button_size_px}px !important;
              padding: 0 !important;
              border-radius: 999px !important;
              font-size: 28px !important;
              font-weight: 400 !important;
              line-height: 1 !important;
            }
            @media (max-width: 768px) {
              button[data-slot="button"] {
                width: 48px !important;
                min-width: 48px !important;
                height: 48px !important;
                min-height: 48px !important;
                font-size: 24px !important;
              }
            }
          `;
          buttonRoot.append(buttonOverrideStyle);
        }
        const submitButton = buttonRoot?.querySelector('button[data-slot="button"]');
        submitButton?.setAttribute('aria-label', '询问');
        submitButton?.setAttribute('title', '询问');
      };

      const renderStaticFallback = () => {
        clearTimer();
        if (input && !input.value) input.placeholder = questions[0];
      };

      const step = () => {
        timer = 0;
        if (destroyed) return;
        if (!input?.isConnected) {
          input = null;
          schedule(mountInput, 100);
          return;
        }
        if (parentDocument.hidden) return;
        if (reducedMotionQuery.matches) {
          renderStaticFallback();
          return;
        }
        if (input.value) {
          input.placeholder = '';
          return;
        }

        const characters = Array.from(questions[questionIndex]);
        if (phase === 'typing') {
          if (characterIndex < characters.length) {
            characterIndex += 1;
            input.placeholder = characters.slice(0, characterIndex).join('');
            schedule(step, config.typing_delay_ms);
            return;
          }
          phase = 'deleting';
          schedule(step, config.hold_delay_ms);
          return;
        }

        if (characterIndex > 0) {
          characterIndex -= 1;
          input.placeholder = characters.slice(0, characterIndex).join('');
          schedule(step, config.deleting_delay_ms);
          return;
        }

        questionIndex = (questionIndex + 1) % questions.length;
        phase = 'typing';
        schedule(step, config.between_delay_ms);
      };

      const onInput = () => {
        clearTimer();
        if (input.value) {
          input.placeholder = '';
          return;
        }
        resetCycle();
        schedule(step, config.initial_delay_ms);
      };

      const detachInput = () => {
        if (!input) return;
        input.removeEventListener('input', onInput);
        input = null;
      };

      const mountInput = () => {
        timer = 0;
        if (destroyed || !root.isConnected) return;
        const candidate = findInput();
        if (!candidate) {
          schedule(mountInput, 100);
          return;
        }
        if (candidate !== input) {
          detachInput();
          input = candidate;
          originalPlaceholder = input.placeholder || originalPlaceholder;
          input.addEventListener('input', onInput);
        }
        applyPresentation();
        if (input.value) {
          input.placeholder = '';
          return;
        }
        resetCycle();
        if (reducedMotionQuery.matches) {
          renderStaticFallback();
        } else {
          input.placeholder = '';
          schedule(step, config.initial_delay_ms);
        }
      };

      const onVisibilityChange = () => {
        clearTimer();
        if (!parentDocument.hidden && input && !input.value) {
          resetCycle();
          schedule(step, config.initial_delay_ms);
        }
      };

      const onMotionPreferenceChange = () => {
        resetCycle();
        if (reducedMotionQuery.matches) {
          renderStaticFallback();
        } else if (input && !input.value) {
          input.placeholder = '';
          schedule(step, config.initial_delay_ms);
        }
      };

      const mutationObserver = new parentWindow.MutationObserver(() => {
        if (!root.isConnected) {
          cleanup();
        } else if (!input?.isConnected) {
          schedule(mountInput, 100);
        }
      });

      const cleanup = () => {
        if (destroyed) return;
        destroyed = true;
        clearTimer();
        mutationObserver.disconnect();
        parentDocument.removeEventListener('visibilitychange', onVisibilityChange);
        if (typeof reducedMotionQuery.removeEventListener === 'function') {
          reducedMotionQuery.removeEventListener('change', onMotionPreferenceChange);
        } else if (typeof reducedMotionQuery.removeListener === 'function') {
          reducedMotionQuery.removeListener(onMotionPreferenceChange);
        }
        if (input?.isConnected && !input.value) {
          input.placeholder = originalPlaceholder;
        }
        inputOverrideStyle?.remove();
        buttonOverrideStyle?.remove();
        detachInput();
        if (parentWindow.__ms2QuestionTypingCleanup === cleanup) {
          delete parentWindow.__ms2QuestionTypingCleanup;
        }
      };

      parentDocument.addEventListener('visibilitychange', onVisibilityChange);
      if (typeof reducedMotionQuery.addEventListener === 'function') {
        reducedMotionQuery.addEventListener('change', onMotionPreferenceChange);
      } else if (typeof reducedMotionQuery.addListener === 'function') {
        reducedMotionQuery.addListener(onMotionPreferenceChange);
      }
      mutationObserver.observe(parentDocument.body, { childList: true, subtree: true });
      parentWindow.__ms2QuestionTypingCleanup = cleanup;
      mountInput();
    })();
    </script>
    """
    return template.replace("__TYPEWRITER_PAYLOAD__", payload)


def render_question_typing_effect(
    questions: Sequence[str],
) -> None:
    """Mount the homepage placeholder animation through a tiny iframe bridge."""
    with st.container(key="ms2-typing-placeholder-bridge"):
        st.iframe(
            build_question_typing_script(questions),
            height=1,
            width=1,
            tab_index=-1,
        )
