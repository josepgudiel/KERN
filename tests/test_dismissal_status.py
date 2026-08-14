"""The /dismiss write path: two distinct outcomes, one hide behaviour.

Three things are pinned here, each of which was broken or absent before the
dismissal split:

1. `status` and `reason` actually reach the row. The endpoint used to construct
   `Dismissal` without either, so `reason` was unconditionally NULL no matter
   what the caller sent.

2. `rec_type` is stored. It used to be derived as
   `rec_id.split("_")[0] if "_" in rec_id else None` — but `_rec_id()` in
   `recommendations.py` returns `md5(f"{rec_type}:{product}").hexdigest()[:12]`,
   a pure hex digest that can never contain an underscore. The condition was
   therefore always false and `rec_type` was always None, silently, for every
   row ever written. The client now sends it explicitly.

3. Hide-behaviour parity. Splitting one button into two must not change *which*
   cards disappear — only what gets recorded about why.

Note on layer: hiding is a client-side filter. `/action-center` does not consult
`dismissed_recs` and returns every recommendation regardless; the dashboard
filters its response against `/dismissed`. The parity tests below assert that
real contract rather than a server-side filter that does not exist.

Note on engine: these run against SQLite, so they cover the ORM write path and
the endpoint, not the Postgres-only `ADD COLUMN IF NOT EXISTS` migration.
"""
from __future__ import annotations

import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# backend/main.py does `from db import ...`, so the backend directory itself has
# to be importable. Using `backend.db` instead would load a *second* copy of the
# module with its own declarative Base, and rows written through one would be
# invisible to the other.
_BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import main  # noqa: E402
from db import Base, Dismissal  # noqa: E402


@pytest.fixture
def db_factory():
    """A real SQLAlchemy session factory backed by a fresh in-memory SQLite DB."""
    # StaticPool + check_same_thread=False: TestClient dispatches the endpoint on
    # a worker thread, and the default pool would hand that thread its own blank
    # in-memory database, so the assertions would query an empty table.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


@pytest.fixture
def client(monkeypatch, db_factory):
    """TestClient whose /dismiss writes land in the throwaway SQLite DB."""
    monkeypatch.setattr(main, "get_db_session", lambda: db_factory())
    return TestClient(main.app)


@pytest.fixture
def session_id():
    """Register a session so /dismiss resolves it instead of 404-ing."""
    sid = str(uuid.uuid4())
    main.manager.store_session(sid, {"currency": "$"})
    yield sid
    main.manager.delete_session(sid)


def _rows(db_factory) -> list[Dismissal]:
    db = db_factory()
    try:
        return db.query(Dismissal).order_by(Dismissal.rec_id).all()
    finally:
        db.close()


# ── (a) status + reason persist ──────────────────────────────────────────────

def test_done_persists_with_reason(client, db_factory, session_id):
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "a1b2c3d4e5f6",
        "status": "done",
        "reason": "Raised the price on Monday",
        "rec_type": "pricing",
    })
    assert resp.status_code == 200

    row = _rows(db_factory)[0]
    assert row.status == "done"
    assert row.reason == "Raised the price on Monday"


def test_not_relevant_persists_with_reason(client, db_factory, session_id):
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "9f8e7d6c5b4a",
        "status": "not_relevant",
        "reason": "We stopped stocking this item",
        "rec_type": "dead_product",
    })
    assert resp.status_code == 200

    row = _rows(db_factory)[0]
    assert row.status == "not_relevant"
    assert row.reason == "We stopped stocking this item"


@pytest.mark.parametrize("status", ["done", "not_relevant"])
def test_reason_is_optional_and_stored_as_null(client, db_factory, session_id, status):
    """Reason is optional by design — omitting it must not block the dismissal."""
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "0123456789ab",
        "status": status,
        "rec_type": "bundle",
    })
    assert resp.status_code == 200

    row = _rows(db_factory)[0]
    assert row.status == status
    assert row.reason is None


def test_status_is_required(client, session_id):
    """An unlabelled dismissal is exactly the ambiguity this change removes."""
    resp = client.post("/dismiss", json={"session_id": session_id, "rec_id": "abc123def456"})
    assert resp.status_code == 422


def test_legacy_unspecified_is_not_settable_over_the_api(client, session_id):
    """It is a backfill marker for pre-split rows, not a status a caller may claim."""
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "abc123def456",
        "status": "legacy_unspecified",
    })
    assert resp.status_code == 422


# ── (b) rec_type is stored, not silently None ────────────────────────────────

@pytest.mark.parametrize("rec_type", [
    "pricing", "declining", "bundle", "rising",
    "dead_product", "dow_opportunity", "underpriced_rising",
])
def test_rec_type_round_trips(client, db_factory, session_id, rec_type):
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "aabbccddeeff",
        "status": "done",
        "rec_type": rec_type,
    })
    assert resp.status_code == 200

    row = _rows(db_factory)[0]
    assert row.rec_type == rec_type, "rec_type must come from the client, not the rec_id"
    assert row.rec_type is not None


def test_real_generated_rec_id_cannot_yield_a_rec_type_by_parsing(client, db_factory, session_id):
    """Regression guard for the original bug, using a genuinely generated ID.

    `_rec_id()` output is a hex digest, so the old `"_" in rec_id` heuristic can
    never fire. This asserts the ID really is underscore-free *and* that the
    stored rec_type survived anyway — proving it came from the payload.
    """
    from backend.engine.recommendations import _rec_id

    rec_id = _rec_id("pricing", "Drip Coffee")
    assert "_" not in rec_id, "the old parsing heuristic depended on a separator that is never present"

    client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": rec_id,
        "status": "done",
        "rec_type": "pricing",
    })

    assert _rows(db_factory)[0].rec_type == "pricing"


def test_rec_type_absent_from_payload_is_null_not_invented(client, db_factory, session_id):
    """A stale client bundle still dismisses; it just records less."""
    resp = client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": "ffeeddccbbaa",
        "status": "not_relevant",
    })
    assert resp.status_code == 200
    assert _rows(db_factory)[0].rec_type is None


# ── (c) hide-behaviour parity across both statuses ───────────────────────────

@pytest.mark.parametrize("status", ["done", "not_relevant"])
def test_both_statuses_add_to_dismissed_recs(client, session_id, status):
    rec_id = "112233445566"
    client.post("/dismiss", json={
        "session_id": session_id,
        "rec_id": rec_id,
        "status": status,
        "rec_type": "pricing",
    })

    assert rec_id in main.manager.get_session(session_id)["dismissed_recs"]

    resp = client.get("/dismissed", params={"session_id": session_id})
    assert resp.status_code == 200
    assert rec_id in resp.json()["dismissed"]


def test_dismissed_set_is_status_blind(client, session_id):
    """The set the dashboard filters on stays a flat set of IDs.

    If a status ever leaked into this structure, one of the two buttons would
    stop hiding its card — the exact regression the split could introduce.
    """
    client.post("/dismiss", json={
        "session_id": session_id, "rec_id": "aaaaaaaaaaaa",
        "status": "done", "rec_type": "pricing",
    })
    client.post("/dismiss", json={
        "session_id": session_id, "rec_id": "bbbbbbbbbbbb",
        "status": "not_relevant", "rec_type": "bundle",
    })

    dismissed = main.manager.get_session(session_id)["dismissed_recs"]
    assert dismissed == {"aaaaaaaaaaaa", "bbbbbbbbbbbb"}
    assert set(client.get("/dismissed", params={"session_id": session_id}).json()["dismissed"]) == dismissed


def test_two_statuses_write_two_distinguishable_rows(client, db_factory, session_id):
    """The point of the split: the rows must not be interchangeable afterwards."""
    client.post("/dismiss", json={
        "session_id": session_id, "rec_id": "aaaaaaaaaaaa", "status": "done",
        "reason": None, "rec_type": "pricing",
    })
    client.post("/dismiss", json={
        "session_id": session_id, "rec_id": "bbbbbbbbbbbb", "status": "not_relevant",
        "reason": "Seasonal item, already delisted", "rec_type": "dead_product",
    })

    done, not_relevant = _rows(db_factory)
    assert (done.status, done.reason, done.rec_type) == ("done", None, "pricing")
    assert (not_relevant.status, not_relevant.reason, not_relevant.rec_type) == (
        "not_relevant", "Seasonal item, already delisted", "dead_product",
    )
    assert done.status != not_relevant.status


def test_dismissal_still_succeeds_without_a_database(monkeypatch, session_id):
    """DB logging is best-effort; losing it must not break hiding the card."""
    monkeypatch.setattr(main, "get_db_session", lambda: None)
    client = TestClient(main.app)

    resp = client.post("/dismiss", json={
        "session_id": session_id, "rec_id": "cccccccccccc",
        "status": "not_relevant", "rec_type": "rising",
    })
    assert resp.status_code == 200
    assert "cccccccccccc" in main.manager.get_session(session_id)["dismissed_recs"]
