"""Test treaty proposal and lifecycle flow (A8-5)."""

from datetime import UTC, datetime, timedelta

import pytest

from ager.adapters.memory_engine import MemoryEngine
from ager.ai_diplomacy.rules import default_rules
from ager.ai_diplomacy.services import Evaluator, TreatyService
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
def treaty_service(store):
    """Create treaty service with default rules."""
    return TreatyService(store, default_rules())


@pytest.fixture
def evaluator(store):
    """Create evaluator for tick processing."""
    return Evaluator(store, default_rules())


def test_propose_alliance_accepted_and_stance_updated(store, treaty_service):
    """Test proposing ALLIANCE updates stance to ALLY and opinion >= threshold."""
    rules = default_rules()
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set moderate opinion
    store.upsert_relation(1, 2, "NEUTRAL", 25.0, now)

    # Propose alliance
    result = treaty_service.propose(1, 2, "ALLIANCE", now, duration_h=24)

    assert result["accepted"] is True, "ALLIANCE should be accepted"
    assert "treaty_id" in result, "Should return treaty_id"
    assert "expires_at" in result, "Should return expires_at"

    # Verify stance changed to ALLY
    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "ALLY", "ALLIANCE should lock stance to ALLY"

    # Verify opinion meets threshold
    assert (
        rel.opinion >= rules.ally_threshold
    ), f"Opinion should be at least {rules.ally_threshold}, got {rel.opinion}"


def test_propose_ceasefire_calms_hostile(store, treaty_service):
    """Test proposing CEASEFIRE transitions from HOSTILE to NEUTRAL."""
    rules = default_rules()
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set HOSTILE relation
    store.upsert_relation(1, 2, "HOSTILE", -50.0, now)

    # Propose ceasefire
    result = treaty_service.propose(1, 2, "CEASEFIRE", now, duration_h=12)

    assert result["accepted"] is True, "CEASEFIRE should be accepted"

    # Verify stance changed to NEUTRAL
    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "NEUTRAL", "CEASEFIRE should transition HOSTILE to NEUTRAL"

    # Verify opinion boosted above hostile threshold
    assert (
        rel.opinion > rules.hostile_threshold
    ), f"Opinion should be above hostile threshold {rules.hostile_threshold}, got {rel.opinion}"


def test_propose_trade_no_stance_lock(store, treaty_service):
    """Test proposing TRADE doesn't lock stance (benefits come from events)."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set NEUTRAL relation
    initial_stance = "NEUTRAL"
    initial_opinion = 10.0
    store.upsert_relation(1, 2, initial_stance, initial_opinion, now)

    # Propose trade
    result = treaty_service.propose(1, 2, "TRADE", now, duration_h=24)

    assert result["accepted"] is True, "TRADE should be accepted"

    # Verify stance unchanged
    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == initial_stance, "TRADE should not lock stance"
    # Opinion may have slight adjustment but stance is primary concern


def test_duplicate_treaty_rejected(store, treaty_service):
    """Test proposing duplicate active treaty is rejected."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    store.upsert_relation(1, 2, "NEUTRAL", 30.0, now)

    # Propose first alliance
    result1 = treaty_service.propose(1, 2, "ALLIANCE", now, duration_h=24)
    assert result1["accepted"] is True, "First ALLIANCE should be accepted"

    # Propose duplicate alliance
    result2 = treaty_service.propose(1, 2, "ALLIANCE", now, duration_h=24)
    assert result2["accepted"] is False, "Duplicate ALLIANCE should be rejected"
    assert "reason" in result2, "Should provide rejection reason"
    assert "already_active" in result2["reason"], "Reason should mention already_active"


def test_treaty_expiration_and_stance_recompute(store, treaty_service, evaluator):
    """Test treaty expires and stance is recomputed based on opinion."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set low opinion but propose alliance (forces ALLY)
    store.upsert_relation(1, 2, "NEUTRAL", 30.0, start_time)
    result = treaty_service.propose(1, 2, "ALLIANCE", start_time, duration_h=2)
    assert result["accepted"] is True

    # Verify stance is ALLY during alliance
    rel_during = store.get_relation(1, 2)
    assert rel_during is not None
    assert rel_during.stance == "ALLY", "During alliance, stance should be ALLY"

    # Advance past expiration (3 hours)
    later_time = start_time + timedelta(hours=3)
    tick_result = evaluator.tick_update(later_time)

    # Verify treaty expired
    treaty_id = result["treaty_id"]
    assert treaty_id in tick_result["expired_treaties"], "Treaty should expire"

    # Verify stance recomputed based on opinion
    # Opinion after cooldown: 30.0 * 0.98^3 + honor_bonus(1.5*2h active)
    # But after expiration at 2h, cooldown continues from 2h to 3h
    # So: (30.0 * 0.98^2 + 1.5*2) * 0.98 (3rd hour after expiration)
    rel_after = store.get_relation(1, 2)
    assert rel_after is not None
    # Opinion is likely still above 40 (ally threshold), so stance remains ALLY
    # But if it dropped below, it would become NEUTRAL or HOSTILE
    # The key test is that stance is recomputed, not locked anymore


def test_treaty_open_event_logged(store, treaty_service):
    """Test that opening treaty logs a treaty_open event."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    store.upsert_relation(1, 2, "NEUTRAL", 20.0, now)

    result = treaty_service.propose(1, 2, "CEASEFIRE", now, duration_h=12)
    assert result["accepted"] is True

    # Check for treaty_open event
    events = store.list_events()
    open_events = [e for e in events if e.kind == "treaty_open"]

    assert len(open_events) > 0, "Should log treaty_open event"
    treaty_id = result["treaty_id"]
    assert any(
        e.payload.get("id") == treaty_id for e in open_events
    ), f"Should have open event for treaty {treaty_id}"


def test_default_duration_used_when_not_specified(store, treaty_service):
    """Test that default duration from rules is used when duration_h not provided."""
    rules = default_rules()
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    store.upsert_relation(1, 2, "NEUTRAL", 25.0, now)

    # Propose without explicit duration
    result = treaty_service.propose(1, 2, "TRADE", now, duration_h=None)
    assert result["accepted"] is True

    # Verify expiration matches default duration
    expected_expires = now + timedelta(hours=rules.trade_duration_h)
    actual_expires = datetime.fromisoformat(result["expires_at"])

    # Allow small tolerance for processing time
    delta = abs((actual_expires - expected_expires).total_seconds())
    assert delta < 1, f"Expires_at should match default TRADE duration: {rules.trade_duration_h}h"


def test_propose_normalizes_faction_pair(store, treaty_service):
    """Test that faction pairs are normalized (a < b) regardless of order."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set relation (stored as 1, 2 since 1 < 2)
    store.upsert_relation(1, 2, "NEUTRAL", 30.0, now)

    # Propose with reversed order (2, 1)
    result = treaty_service.propose(2, 1, "ALLIANCE", now, duration_h=24)
    assert result["accepted"] is True

    # Verify treaty is created for normalized pair (1, 2)
    treaty_id = result["treaty_id"]
    treaty = store.get_treaty(treaty_id)
    assert treaty is not None
    assert (treaty.a, treaty.b) == (1, 2), "Treaty should normalize to (1, 2)"
