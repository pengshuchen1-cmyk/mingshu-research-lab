"""Composable, Shadcn-inspired primitives built with native Streamlit layout."""

from __future__ import annotations

from html import escape
import re
from typing import Literal

import streamlit as st


Tone = Literal["default", "muted", "accent", "danger"]
Size = Literal["sm", "md", "lg"]


def _safe_key(value: str) -> str:
    """Return a stable Streamlit key fragment suitable for CSS selectors."""
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value).strip())
    return normalized.strip("-") or "surface"


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def card(
    key: str,
    *,
    tone: Tone = "default",
    size: Size = "md",
    gap: str = "small",
):
    """Return a native Streamlit container styled as a composable card."""
    return st.container(
        border=True,
        key=f"ms-ui-card-{tone}-{size}-{_safe_key(key)}",
        gap=gap,
    )


def badge(label: object, *, variant: Tone = "muted") -> None:
    """Render a compact semantic badge."""
    _html(
        f'<span class="ms-ui-badge ms-ui-badge-{variant}">'
        f"{escape(str(label))}</span>"
    )


def page_header(
    title: object,
    description: object | None = None,
    *,
    eyebrow: object | None = None,
) -> None:
    """Render the single H1 heading used at the start of an application page."""
    eyebrow_html = (
        f'<p class="ms-ui-eyebrow">{escape(str(eyebrow))}</p>'
        if eyebrow is not None
        else ""
    )
    description_html = (
        f'<p class="ms-ui-page-description">{escape(str(description))}</p>'
        if description is not None
        else ""
    )
    _html(
        '<header class="ms-ui-page-header">'
        f"{eyebrow_html}<h1>{escape(str(title))}</h1>{description_html}</header>"
    )


def section_header(
    title: object,
    description: object | None = None,
    *,
    eyebrow: object | None = None,
) -> None:
    """Render a consistent H2 section heading and optional supporting copy."""
    eyebrow_html = (
        f'<p class="ms-ui-eyebrow">{escape(str(eyebrow))}</p>'
        if eyebrow is not None
        else ""
    )
    description_html = (
        f'<p class="ms-ui-section-description">{escape(str(description))}</p>'
        if description is not None
        else ""
    )
    _html(
        '<div class="ms-ui-section-header">'
        f"{eyebrow_html}<h2>{escape(str(title))}</h2>{description_html}</div>"
    )


def callout(
    title: object,
    description: object,
    *,
    variant: Tone = "default",
) -> None:
    """Render a concise alert/callout without introducing another component runtime."""
    role = "alert" if variant == "danger" else "status"
    _html(
        f'<aside class="ms-ui-callout ms-ui-callout-{variant}" role="{role}">'
        '<span class="ms-ui-callout-mark" aria-hidden="true"></span>'
        '<div class="ms-ui-callout-copy">'
        f"<strong>{escape(str(title))}</strong>"
        f"<p>{escape(str(description))}</p>"
        "</div></aside>"
    )


def metric_card(
    label: object,
    value: object,
    description: object | None = None,
) -> None:
    """Render a compact metric card with stable typographic hierarchy."""
    description_html = (
        f'<p>{escape(str(description))}</p>' if description is not None else ""
    )
    _html(
        '<article class="ms-ui-metric">'
        f'<span>{escape(str(label))}</span><strong>{escape(str(value))}</strong>'
        f"{description_html}</article>"
    )


def empty_state_header(title: object, description: object) -> None:
    """Render compact empty-state copy while leaving actions to native buttons."""
    _html(
        '<div class="ms-ui-empty-state-copy">'
        '<span class="ms-ui-empty-state-mark" aria-hidden="true"></span>'
        f"<h2>{escape(str(title))}</h2>"
        f"<p>{escape(str(description))}</p></div>"
    )
