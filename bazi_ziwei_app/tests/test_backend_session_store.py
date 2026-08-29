from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from backend.session_store import SessionCapacityError, SessionStore


def _confirm(store: SessionStore, session_id: str, marker: str = "one"):
    state, preview_id, token = store.create_preview(session_id, f"input-{marker}", f"chart-{marker}")
    assert state == "ok" and preview_id and token
    state, reservation = store.begin_confirmation(
        session_id, preview_id, token, f"chart-{marker}", f"input-{marker}"
    )
    assert state == "ok" and reservation
    state, chart_id = store.finish_confirmation(
        session_id,
        reservation,
        f"input-{marker}",
        f"chart-{marker}",
        {"profile": {"name": "sensitive"}},
        {"pillars": [marker]},
    )
    assert state == "ok" and chart_id
    return chart_id


def test_confirmation_reservation_is_atomic_under_concurrency():
    store = SessionStore(30)
    session_id, _ = store.issue()
    _, preview_id, token = store.create_preview(session_id, "input", "chart")

    def begin():
        return store.begin_confirmation(
            session_id, preview_id, token, "chart", "input"
        )[0]

    with ThreadPoolExecutor(max_workers=8) as pool:
        states = list(pool.map(lambda _: begin(), range(8)))
    assert states.count("ok") == 1
    assert states.count("conflict") == 7


def test_get_returns_deep_snapshot_not_mutable_internal_record():
    store = SessionStore(30)
    session_id, _ = store.issue()
    first_id = _confirm(store, session_id)
    state, snapshot = store.get(session_id, first_id)
    assert state == "ok" and snapshot
    _confirm(store, session_id, "two")
    assert snapshot.facts == {"pillars": ["one"]}
    snapshot.facts["pillars"].append("caller mutation")
    assert first_id not in store._charts


def test_finish_owns_copies_and_chart_switch_does_not_clear_caller_facts():
    store = SessionStore(30)
    session_id, _ = store.issue()
    state, preview_id, token = store.create_preview(session_id, "input-one", "chart-one")
    assert state == "ok" and preview_id and token
    state, reservation = store.begin_confirmation(
        session_id, preview_id, token, "chart-one", "input-one"
    )
    assert state == "ok" and reservation
    caller_chart = {"profile": {"name": "sensitive"}}
    caller_facts = {"pillars": ["original"]}
    state, chart_id = store.finish_confirmation(
        session_id,
        reservation,
        "input-one",
        "chart-one",
        caller_chart,
        caller_facts,
    )
    assert state == "ok" and chart_id

    caller_chart["profile"]["name"] = "caller mutation"
    caller_facts["pillars"].append("caller mutation")
    state, snapshot = store.get(session_id, chart_id)
    assert state == "ok" and snapshot
    assert snapshot.facts == {"pillars": ["original"]}
    assert store._charts[chart_id].chart["profile"]["name"] == "sensitive"

    _confirm(store, session_id, "two")
    assert caller_chart == {"profile": {"name": "caller mutation"}}
    assert caller_facts == {"pillars": ["original", "caller mutation"]}


def test_idle_cleanup_scrubs_sensitive_state_and_removes_tombstone():
    now = [10.0]
    store = SessionStore(5, clock=lambda: now[0])
    session_id, _ = store.issue()
    chart_id = _confirm(store, session_id)
    record = store._charts[chart_id]
    now[0] += 6
    store.cleanup()
    assert record.chart == {}
    assert record.facts == {}
    assert chart_id not in store._charts
    assert chart_id in store._tombstones
    now[0] += 6
    store.cleanup()
    assert chart_id not in store._tombstones


def test_tombstones_have_hard_capacity_bound():
    now = [10.0]
    store = SessionStore(30, clock=lambda: now[0], tombstone_limit=2)
    session_id, _ = store.issue()
    for index in range(5):
        _confirm(store, session_id, str(index))
    assert len(store._tombstones) == 2


def test_clear_removes_all_sensitive_and_session_state():
    store = SessionStore(30)
    session_id, _ = store.issue()
    chart_id = _confirm(store, session_id)
    record = store._charts[chart_id]
    store.clear()
    assert record.chart == {}
    assert record.facts == {}
    assert store.counts() == (0, 0, 0)


def test_active_session_capacity_never_evicts_sensitive_sessions():
    store = SessionStore(30, session_capacity=1)
    session_id, _ = store.issue()
    chart_id = _confirm(store, session_id)
    with pytest.raises(SessionCapacityError):
        store.issue()
    assert store.counts()[0] == 1
    state, snapshot = store.get(session_id, chart_id)
    assert state == "ok" and snapshot
