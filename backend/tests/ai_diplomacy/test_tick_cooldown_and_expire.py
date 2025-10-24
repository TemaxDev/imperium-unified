"""Test tick updates and treaty expiration (A8-5)."""

from datetime import UTC, datetime, timedelta

import pytest

from ager.adapters.memory_engine import MemoryEngine
from ager.ai_diplomacy.rules import default_rules
from ager.ai_diplomacy.services import Evaluator
from ager.ai_diplomacy.services.store_impl import MemoryDiploStore


@pytest.fixture
def engine():
    """Create fresh memory engine for each test."""
    return MemoryEngine()


@pytest.fixture
def store(engine):
    """Create diplomacy store from engine."""
    return MemoryDiploStore(engine)


@pytest.fixture
def evaluator(store):
    """Create evaluator with default rules."""
    return Evaluator(store, default_rules())


def test_treaty_expires_after_duration(store, evaluator):
    """Test that treaty expires when time exceeds expires_at."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    duration_h = 1
    expires_at = start_time + timedelta(hours=duration_h)

    # Open ceasefire for 1 hour
    treaty_id = store.open_treaty(1, 2, "CEASEFIRE", start_time, expires_at)

    # Advance 2 hours (past expiration)
    later_time = start_time + timedelta(hours=2)
    result = evaluator.tick_update(later_time)

    # Verify treaty expired
    assert treaty_id in result["expired_treaties"], "Treaty should be in expired list"

    # Verify treaty status is EXPIRED
    treaty = store.get_treaty(treaty_id)
    assert treaty is not None
    assert treaty.status == "EXPIRED", f"Treaty status should be EXPIRED, got {treaty.status}"


def test_treaty_expire_event_logged(store, evaluator):
    """Test that treaty expiration logs an event."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = start_time + timedelta(hours=1)

    treaty_id = store.open_treaty(1, 2, "TRADE", start_time, expires_at)

    # Advance past expiration
    later_time = start_time + timedelta(hours=2)
    evaluator.tick_update(later_time)

    # Check for treaty_expire event
    events = store.list_events()
    expire_events = [e for e in events if e.kind == "treaty_expire"]

    assert len(expire_events) > 0, "Should log treaty_expire event"
    assert any(
        e.payload.get("id") == treaty_id for e in expire_events
    ), f"Should have expire event for treaty {treaty_id}"


def test_stance_recomputed_after_treaty_expires(store, evaluator):
    """Test that stance is recomputed correctly after treaty expiration."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = start_time + timedelta(hours=1)

    # Set hostile opinion but ceasefire (forces NEUTRAL)
    store.upsert_relation(1, 2, "NEUTRAL", -45.0, start_time)
    store.open_treaty(1, 2, "CEASEFIRE", start_time, expires_at)

    # Verify ceasefire locks to NEUTRAL
    evaluator.tick_update(start_time)
    rel_during = store.get_relation(1, 2)
    assert rel_during is not None
    assert rel_during.stance == "NEUTRAL", "CEASEFIRE should lock to NEUTRAL"

    # Advance past expiration
    later_time = start_time + timedelta(hours=2)
    evaluator.tick_update(later_time)

    # Verify stance reverts to HOSTILE (opinion below -40)
    rel_after = store.get_relation(1, 2)
    assert rel_after is not None
    assert (
        rel_after.stance == "HOSTILE"
    ), f"After ceasefire expires with opinion={rel_after.opinion}, stance should be HOSTILE"


def test_multiple_relations_updated_in_single_tick(store, evaluator):
    """Test that tick updates multiple relations correctly."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set up multiple relations with different opinions
    store.upsert_relation(1, 2, "NEUTRAL", 30.0, start_time)
    store.upsert_relation(1, 3, "NEUTRAL", -30.0, start_time)
    store.upsert_relation(2, 3, "NEUTRAL", 0.0, start_time)

    # Advance 1 hour
    later_time = start_time + timedelta(hours=1)
    result = evaluator.tick_update(later_time)

    # All 3 relations should be updated (cooldown applied)
    assert len(result["updated_relations"]) == 3, "Should update all 3 relations"

    # Verify cooldown applied
    rules = default_rules()
    rel_12 = store.get_relation(1, 2)
    assert rel_12 is not None
    expected_12 = 30.0 * rules.cooldown_factor
    assert abs(rel_12.opinion - expected_12) < 1e-6, "Cooldown should apply to (1,2)"


def test_no_expiration_if_treaty_not_expired(store, evaluator):
    """Test that active treaties don't expire before their time."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = start_time + timedelta(hours=10)  # Far in future

    treaty_id = store.open_treaty(1, 2, "ALLIANCE", start_time, expires_at)

    # Advance only 1 hour (still active)
    later_time = start_time + timedelta(hours=1)
    result = evaluator.tick_update(later_time)

    # Verify treaty NOT expired
    assert treaty_id not in result["expired_treaties"], "Treaty should still be active"

    treaty = store.get_treaty(treaty_id)
    assert treaty is not None
    assert treaty.status == "ACTIVE", f"Treaty should be ACTIVE, got {treaty.status}"


def test_tick_update_event_logged(store, evaluator):
    """Test that each tick logs a tick_update event."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    store.upsert_relation(1, 2, "NEUTRAL", 20.0, start_time)

    later_time = start_time + timedelta(hours=1)
    result = evaluator.tick_update(later_time)

    # Verify tick_update event in result
    assert len(result["events"]) > 0, "Should have events in result"
    assert any(
        e["kind"] == "tick_update" for e in result["events"]
    ), "Should have tick_update event"

    # Verify event in store
    events = store.list_events()
    tick_events = [e for e in events if e.kind == "tick_update"]
    assert len(tick_events) > 0, "Should log tick_update event in store"
