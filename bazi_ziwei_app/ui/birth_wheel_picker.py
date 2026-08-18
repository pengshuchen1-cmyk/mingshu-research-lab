"""Dependency-free five-column birth date/time wheel for Streamlit v2."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import streamlit as st


BIRTH_WHEEL_COMPONENT_KEY = "profile_birth_wheel"
WHEEL_COLUMN_IDS = ("year", "month", "day", "hour", "minute")

_WHEEL_HTML = '<div class="birth-wheel" aria-label="出生日期与时间滚轮"></div>'

_WHEEL_CSS = r"""
:host {
  display: block;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  color: #111;
  font: 13px/1.35 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
.birth-wheel {
  --row-height: 44px;
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  width: 100%;
  min-width: 0;
  height: calc(var(--row-height) * 5);
  overflow: hidden;
  border: 0;
  border-radius: 22px;
  background: #fff;
}
.birth-wheel::before {
  content: "";
  position: absolute;
  z-index: 0;
  inset: calc(var(--row-height) * 2) 0 auto;
  height: var(--row-height);
  border-radius: 12px;
  background: #f0f2f1;
  pointer-events: none;
}
.wheel-column {
  position: relative;
  z-index: 1;
  min-width: 0;
  height: 100%;
  margin: 0;
  padding: calc(var(--row-height) * 2) 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: none;
  scroll-snap-type: y mandatory;
  -webkit-overflow-scrolling: touch;
  mask-image: linear-gradient(to bottom, transparent 0, #000 24%, #000 76%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 24%, #000 76%, transparent 100%);
}
.wheel-column::-webkit-scrollbar { display: none; }
.wheel-option {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-width: 0;
  height: var(--row-height);
  padding: 0 2px;
  border: 0;
  background: transparent;
  color: #71717a;
  font: inherit;
  font-size: clamp(11px, 3.15vw, 14px);
  font-variant-numeric: tabular-nums;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  scroll-snap-align: center;
  touch-action: manipulation;
}
.wheel-option[aria-selected="true"] {
  color: #111;
  font-weight: 650;
}
.wheel-column:focus-visible {
  outline: 1px solid rgba(0, 0, 0, .36);
  outline-offset: -1px;
  border-radius: 12px;
}
@media (max-width: 420px) {
  :host { font-size: 12px; }
  .birth-wheel { border-radius: 18px; }
  .wheel-option { font-size: 11px; padding-inline: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .wheel-column { scroll-behavior: auto !important; }
}
"""

_WHEEL_JS = r"""
export default function(component) {
  const { data, parentElement, setStateValue } = component;
  const root = parentElement.querySelector('.birth-wheel');
  if (!root || !data || !Array.isArray(data.columns)) return;

  const rowHeight = 44;
  const generation = Symbol('birth-wheel-render');
  root._wheelGeneration = generation;
  const selected = {};
  for (const column of data.columns) selected[column.id] = column.selected;

  const publish = (id, value) => {
    if (root._wheelGeneration !== generation) return;
    if (Object.is(selected[id], value)) return;
    selected[id] = value;
    setStateValue('selection', { ...selected });
  };

  root.replaceChildren();
  for (const column of data.columns) {
    const listbox = document.createElement('div');
    listbox.className = 'wheel-column';
    listbox.tabIndex = 0;
    listbox.setAttribute('role', 'listbox');
    listbox.setAttribute('aria-label', column.label);

    let selectedIndex = Math.max(0, column.items.findIndex(
      (item) => Object.is(item.value, column.selected)
    ));
    const buttons = [];
    column.items.forEach((item, index) => {
      const option = document.createElement('button');
      option.type = 'button';
      option.className = 'wheel-option';
      option.id = `${column.id}-${index}`;
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', index === selectedIndex ? 'true' : 'false');
      option.tabIndex = -1;
      option.textContent = String(item.label);
      option.onclick = () => selectIndex(index, true);
      buttons.push(option);
      listbox.appendChild(option);
    });

    const selectIndex = (nextIndex, userInitiated) => {
      const bounded = Math.max(0, Math.min(buttons.length - 1, nextIndex));
      selectedIndex = bounded;
      buttons.forEach((button, index) => {
        button.setAttribute('aria-selected', index === bounded ? 'true' : 'false');
      });
      listbox.setAttribute('aria-activedescendant', `${column.id}-${bounded}`);
      listbox.scrollTo({
        top: bounded * rowHeight,
        behavior: 'auto'
      });
      if (userInitiated) publish(column.id, column.items[bounded].value);
    };

    listbox.onscroll = () => {
      if (root._wheelGeneration !== generation) return;
      const index = Math.max(0, Math.min(buttons.length - 1, Math.round(listbox.scrollTop / rowHeight)));
      if (index === selectedIndex) return;
      selectedIndex = index;
      buttons.forEach((button, itemIndex) => {
        button.setAttribute('aria-selected', itemIndex === index ? 'true' : 'false');
      });
      listbox.setAttribute('aria-activedescendant', `${column.id}-${index}`);
      publish(column.id, column.items[index].value);
    };
    listbox.onkeydown = (event) => {
      let next = selectedIndex;
      if (event.key === 'ArrowDown') next += 1;
      else if (event.key === 'ArrowUp') next -= 1;
      else if (event.key === 'PageDown') next += 5;
      else if (event.key === 'PageUp') next -= 5;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = buttons.length - 1;
      else return;
      event.preventDefault();
      selectIndex(next, true);
    };
    root.appendChild(listbox);
    requestAnimationFrame(() => selectIndex(selectedIndex, false));
  }
}
"""

_birth_wheel = st.components.v2.component(
    "mingshu_birth_wheel",
    html=_WHEEL_HTML,
    css=_WHEEL_CSS,
    js=_WHEEL_JS,
)


def wheel_column(column_id: str, label: str, values: Sequence[Any], selected: Any, formatter: Callable[[Any], str]) -> dict[str, Any]:
    """Build a JSON-safe wheel column from server-owned values and labels."""
    if column_id not in WHEEL_COLUMN_IDS:
        raise ValueError(f"unsupported wheel column: {column_id}")
    items = [{"value": value, "label": str(formatter(value))} for value in values]
    if not items:
        raise ValueError(f"wheel column {column_id} cannot be empty")
    if not any(_same_scalar(selected, item["value"]) for item in items):
        selected = items[0]["value"]
    return {"id": column_id, "label": str(label), "items": items, "selected": selected}


def validate_wheel_selection(raw: Any, columns: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Whitelist a component result against the exact server-provided options."""
    if not isinstance(raw, Mapping) or set(raw) != set(WHEEL_COLUMN_IDS):
        return None
    validated: dict[str, Any] = {}
    by_id = {str(column.get("id")): column for column in columns}
    if set(by_id) != set(WHEEL_COLUMN_IDS):
        return None
    for column_id in WHEEL_COLUMN_IDS:
        candidate = raw[column_id]
        allowed = [item.get("value") for item in by_id[column_id].get("items", ()) if isinstance(item, Mapping)]
        match = next((value for value in allowed if _same_scalar(candidate, value)), _MISSING)
        if match is _MISSING:
            return None
        validated[column_id] = match
    return validated


def render_birth_wheel(
    columns: Sequence[Mapping[str, Any]],
    *,
    on_change: Callable[[], None] | None = None,
) -> dict[str, Any] | None:
    """Mount the wheel and return only a fully validated selection."""
    payload = {"columns": [dict(column) for column in columns]}
    default = {"selection": {str(column["id"]): column["selected"] for column in columns}}
    result = _birth_wheel(
        key=BIRTH_WHEEL_COMPONENT_KEY,
        data=payload,
        default=default,
        height=220,
        on_selection_change=on_change,
    )
    return validate_wheel_selection(result.get("selection"), columns)


def _same_scalar(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


_MISSING = object()
