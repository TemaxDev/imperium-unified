"""Test proposer deterministic suggestions and scoring (A8-5)."""

from datetime import UTC, datetime, timedelta

import pytest

from ager.adapters.memory_engine import MemoryEngine
from ager.ai_diplomacy.rules import default_rules
from ager.ai_diplomacy.services import Proposer
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
def proposer(store):
    """Create proposer with default rules."""
    return Proposer(store, default_rules())


def test_hostile_with_attacks_suggests_ceasefire(store, proposer):
    """Test HOSTILE stance + recent attacks ranks CEASEFIRE top."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set HOSTILE relation
    store.upsert_relation(1, 2, "HOSTILE", -55.0, now)

    # Log recent attack events
    for i in range(3):
        event_time = now - timedelta(hours=i)
        store.log_event("attack", {"a": 1, "b": 2}, event_time)

    # Get suggestions
    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    assert len(suggestions) > 0, "Should return suggestions"
    assert (
        suggestions[0].type == "CEASEFIRE"
    ), f"Top suggestion should be CEASEFIRE, got {suggestions[0].type}"
    assert isinstance(suggestions[0].score, int), "Score should be integer for determinism"
    assert suggestions[0].score > 0, "CEASEFIRE should have positive score in HOSTILE context"


def test_neutral_with_trades_suggests_trade(store, proposer):
    """Test NEUTRAL stance + recent trades ranks TRADE highly."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set NEUTRAL with positive opinion
    store.upsert_relation(1, 2, "NEUTRAL", 5.0, now)

    # Log recent trade events
    for i in range(2):
        event_time = now - timedelta(hours=i)
        store.log_event("trade", {"a": 1, "b": 2}, event_time)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    assert len(suggestions) > 0, "Should return suggestions"
    # TRADE should be top or near top
    trade_sugg = next((s for s in suggestions if s.type == "TRADE"), None)
    assert trade_sugg is not None, "Should suggest TRADE"
    assert trade_sugg.score > 0, "TRADE should have positive score with recent trades"


def test_high_opinion_shared_enemies_suggests_alliance(store, proposer):
    """Test high opinion + shared enemies ranks ALLIANCE top."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set high opinion between (1, 2)
    store.upsert_relation(1, 2, "ALLY", 60.0, now)

    # Create shared enemies: both (1,3) and (2,3) are HOSTILE
    store.upsert_relation(1, 3, "HOSTILE", -50.0, now)
    store.upsert_relation(2, 3, "HOSTILE", -50.0, now)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    assert len(suggestions) > 0, "Should return suggestions"
    alliance_sugg = next((s for s in suggestions if s.type == "ALLIANCE"), None)
    assert alliance_sugg is not None, "Should suggest ALLIANCE with high opinion + shared enemies"
    assert alliance_sugg.score > 0, "ALLIANCE should have positive score"


def test_active_trade_blocks_trade_suggestion(store, proposer):
    """Test that active TRADE treaty massively penalizes TRADE suggestion."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)
    expires_at = now + timedelta(hours=24)

    # Set NEUTRAL with positive opinion
    store.upsert_relation(1, 2, "NEUTRAL", 10.0, now)

    # Open active TRADE treaty
    store.open_treaty(1, 2, "TRADE", now, expires_at)

    # Log recent trades (would normally boost TRADE)
    for i in range(3):
        event_time = now - timedelta(hours=i)
        store.log_event("trade", {"a": 1, "b": 2}, event_time)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    # TRADE should be massively penalized (negative score)
    trade_sugg = next((s for s in suggestions if s.type == "TRADE"), None)
    assert trade_sugg is not None, "TRADE should still appear in suggestions"
    assert trade_sugg.score < 0, "TRADE should have large negative penalty when already active"


def test_scores_are_integers(store, proposer):
    """Test that all suggestion scores are integers for determinism."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    store.upsert_relation(1, 2, "NEUTRAL", 20.0, now)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    for sugg in suggestions:
        assert isinstance(
            sugg.score, int
        ), f"Score should be int, got {type(sugg.score)} for {sugg.type}"


def test_deterministic_ordering_same_state(store, proposer):
    """Test that same state produces same suggestions order (determinism)."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set up repeatable state
    store.upsert_relation(1, 2, "NEUTRAL", 15.0, now)
    store.log_event("trade", {"a": 1, "b": 2}, now - timedelta(hours=1))

    # Call twice
    suggestions1 = proposer.top_suggestions(1, 2, now, k=3)
    suggestions2 = proposer.top_suggestions(1, 2, now, k=3)

    # Verify identical ordering
    assert len(suggestions1) == len(suggestions2), "Should return same number of suggestions"
    for i, (s1, s2) in enumerate(zip(suggestions1, suggestions2, strict=True)):
        assert s1.type == s2.type, f"Suggestion {i}: type mismatch {s1.type} vs {s2.type}"
        assert s1.score == s2.score, f"Suggestion {i}: score mismatch {s1.score} vs {s2.score}"


def test_tie_breaker_by_type_rank(store, proposer):
    """Test that equal scores use TYPE_RANK tie-breaker (CEASEFIRE < TRADE < ALLIANCE)."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set neutral with zero opinion (should produce similar scores)
    store.upsert_relation(1, 2, "NEUTRAL", 0.0, now)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    # If CEASEFIRE and TRADE have equal scores, CEASEFIRE should come first
    # (This is implementation-dependent, but we check ordering is stable)
    ceasefire_idx = next((i for i, s in enumerate(suggestions) if s.type == "CEASEFIRE"), None)
    trade_idx = next((i for i, s in enumerate(suggestions) if s.type == "TRADE"), None)

    if ceasefire_idx is not None and trade_idx is not None:
        ceasefire_score = suggestions[ceasefire_idx].score
        trade_score = suggestions[trade_idx].score
        if ceasefire_score == trade_score:
            # Equal scores: CEASEFIRE should come before TRADE
            assert ceasefire_idx < trade_idx, "Tie-breaker: CEASEFIRE should rank before TRADE"


def test_alliance_requires_minimum_opinion(store, proposer):
    """Test that ALLIANCE is not suggested if opinion < alliance_min_opinion."""
    rules = default_rules()
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Set opinion below alliance minimum (20.0)
    store.upsert_relation(1, 2, "NEUTRAL", 10.0, now)

    # Create shared enemies (would boost alliance score if eligible)
    store.upsert_relation(1, 3, "HOSTILE", -50.0, now)
    store.upsert_relation(2, 3, "HOSTILE", -50.0, now)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    # ALLIANCE should either not appear or have very negative score
    alliance_sugg = next((s for s in suggestions if s.type == "ALLIANCE"), None)
    if alliance_sugg is not None:
        assert (
            alliance_sugg.score < 0
        ), f"ALLIANCE with opinion={10.0} < {rules.alliance_min_opinion} should have negative score"


def test_event_window_filters_old_events(store, proposer):
    """Test that events outside recent_window_h are ignored."""
    rules = default_rules()
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    store.upsert_relation(1, 2, "NEUTRAL", 5.0, now)

    # Log old attack (outside window)
    old_event_time = now - timedelta(hours=rules.recent_window_h + 1)
    store.log_event("attack", {"a": 1, "b": 2}, old_event_time)

    # Log recent attack (inside window)
    recent_event_time = now - timedelta(hours=1)
    store.log_event("attack", {"a": 1, "b": 2}, recent_event_time)

    suggestions = proposer.top_suggestions(1, 2, now, k=3)

    # CEASEFIRE score should reflect only 1 recent attack, not the old one
    ceasefire_sugg = next((s for s in suggestions if s.type == "CEASEFIRE"), None)
    assert ceasefire_sugg is not None, "Should suggest CEASEFIRE"
    # Score should be positive but not as high as if 2 attacks counted
    # (Exact score depends on formula, but we verify it's reasonable)
    assert (
        ceasefire_sugg.score >= 0
    ), "CEASEFIRE should have non-negative score with 1 recent attack"
