"""Test diplomacy rules coherence: thresholds, locks, cooldown (A8-5)."""

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


def test_stance_thresholds_ally(store, evaluator):
    """Test opinion >= 40 results in ALLY stance."""
    # Set opinion to 50 (above ally threshold of 40)
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    store.upsert_relation(1, 2, "NEUTRAL", 50.0, now)

    # Tick to recompute stance
    evaluator.tick_update(now)

    # Verify stance is ALLY
    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "ALLY", f"Expected ALLY for opinion={rel.opinion}, got {rel.stance}"


def test_stance_thresholds_hostile(store, evaluator):
    """Test opinion <= -40 results in HOSTILE stance."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    store.upsert_relation(1, 2, "NEUTRAL", -50.0, now)

    evaluator.tick_update(now)

    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "HOSTILE", f"Expected HOSTILE for opinion={rel.opinion}, got {rel.stance}"


def test_stance_thresholds_neutral(store, evaluator):
    """Test opinion in [-40, 40) results in NEUTRAL stance."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    store.upsert_relation(1, 2, "HOSTILE", 0.0, now)  # Reset from HOSTILE

    evaluator.tick_update(now)

    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "NEUTRAL", f"Expected NEUTRAL for opinion={rel.opinion}, got {rel.stance}"


def test_alliance_treaty_locks_ally_stance(store, evaluator):
    """Test active ALLIANCE treaty forces ALLY stance regardless of opinion."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = now + timedelta(hours=24)

    # Set low opinion but open alliance
    store.upsert_relation(1, 2, "NEUTRAL", 10.0, now)  # Below ally threshold
    store.open_treaty(1, 2, "ALLIANCE", now, expires_at)

    evaluator.tick_update(now)

    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance == "ALLY", "ALLIANCE treaty should lock stance to ALLY"
    assert rel.opinion >= 10.0  # Opinion may have honor bonus


def test_ceasefire_treaty_locks_minimum_neutral(store, evaluator):
    """Test CEASEFIRE treaty enforces minimum NEUTRAL stance."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = now + timedelta(hours=12)

    # Set HOSTILE opinion and stance
    store.upsert_relation(1, 2, "HOSTILE", -50.0, now)
    store.open_treaty(1, 2, "CEASEFIRE", now, expires_at)

    evaluator.tick_update(now)

    rel = store.get_relation(1, 2)
    assert rel is not None
    assert rel.stance in ("NEUTRAL", "ALLY"), "CEASEFIRE should enforce min NEUTRAL stance"


def test_cooldown_factor_applied_over_time(store, evaluator):
    """Test opinion cooldown multiplies by 0.98 per hour."""
    rules = default_rules()
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set initial opinion
    initial_op = 50.0
    store.upsert_relation(1, 2, "ALLY", initial_op, start_time)

    # Advance 1 hour
    later_time = start_time + timedelta(hours=1)
    evaluator.tick_update(later_time)

    rel = store.get_relation(1, 2)
    assert rel is not None

    # Expected: 50 * 0.98 = 49.0
    expected = initial_op * rules.cooldown_factor
    assert (
        abs(rel.opinion - expected) < 1e-6
    ), f"Opinion should decay by cooldown_factor: expected ~{expected}, got {rel.opinion}"


def test_cooldown_zero_delta_no_change(store, evaluator):
    """Test that calling tick with same timestamp doesn't change opinion."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    initial_op = 50.0
    store.upsert_relation(1, 2, "ALLY", initial_op, now)

    # First tick
    evaluator.tick_update(now)
    rel_after_first = store.get_relation(1, 2)
    assert rel_after_first is not None
    op_after_first = rel_after_first.opinion

    # Second tick with same timestamp
    evaluator.tick_update(now)
    rel_after_second = store.get_relation(1, 2)
    assert rel_after_second is not None

    # Opinion should not change (idempotent)
    assert (
        abs(rel_after_second.opinion - op_after_first) < 1e-6
    ), "Tick with dt=0 should be idempotent"


def test_honor_bonus_for_alliance(store, evaluator):
    """Test that active alliance adds honor bonus over time."""
    rules = default_rules()
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = start_time + timedelta(hours=72)

    # Set moderate opinion and alliance
    initial_op = 30.0
    store.upsert_relation(1, 2, "NEUTRAL", initial_op, start_time)
    store.open_treaty(1, 2, "ALLIANCE", start_time, expires_at)

    # Advance 2 hours
    later_time = start_time + timedelta(hours=2)
    evaluator.tick_update(later_time)

    rel = store.get_relation(1, 2)
    assert rel is not None

    # Expected: cooldown + honor bonus
    # opinion_after = (30.0 * 0.98^2) + (1.5 * 2)
    cooldown_factor = rules.cooldown_factor**2
    expected = (initial_op * cooldown_factor) + (rules.honor_bonus_per_hour * 2)

    assert (
        abs(rel.opinion - expected) < 1e-6
    ), f"Alliance should add honor bonus: expected ~{expected}, got {rel.opinion}"


def test_last_updated_advances_on_tick(store, evaluator):
    """Test that last_updated timestamp advances after tick."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    store.upsert_relation(1, 2, "NEUTRAL", 20.0, start_time)

    later_time = start_time + timedelta(hours=1)
    evaluator.tick_update(later_time)

    rel = store.get_relation(1, 2)
    assert rel is not None
    updated = datetime.fromisoformat(rel.last_updated)

    assert updated == later_time, f"last_updated should advance to {later_time}, got {updated}"
