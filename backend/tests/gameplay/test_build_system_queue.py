from datetime import datetime, timedelta, timezone

import pytest

from ager.adapters.memory_engine import MemoryEngine
from ager.gameplay.rules import default_rules
from ager.gameplay.systems.build import BuildSystem
from ager.models import Resources


def test_build_system_insufficient_resources():
    """Test that build is refused when resources are insufficient."""
    engine = MemoryEngine()
    # Set low resources
    engine.world[1].resources = Resources(wood=10, clay=10, iron=10, crop=10)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    # Try to upgrade lumber_mill to level 2 (costs ~77 wood)
    result = system.queue_build(village_id=1, building="lumber_mill", rules=rules, now=now)

    assert result is False
    assert 1 not in system.pending_builds


def test_build_system_queue_occupied():
    """Test that second build is refused when queue is occupied."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=1000, clay=1000, iron=1000, crop=1000)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    # Queue first build
    result1 = system.queue_build(village_id=1, building="lumber_mill", rules=rules, now=now)
    assert result1 is True

    # Try to queue second build - should be refused
    result2 = system.queue_build(village_id=1, building="clay_pit", rules=rules, now=now)
    assert result2 is False


def test_build_system_eta_calculation():
    """Test that ETA is calculated correctly."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=1000, clay=1000, iron=1000, crop=1000)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    result = system.queue_build(village_id=1, building="lumber_mill", rules=rules, now=now)
    assert result is True

    # Check ETA
    build_info = system.pending_builds[1]
    duration_s = rules.duration_s("lumber_mill", 2)  # upgrading to level 2
    expected_eta = now + timedelta(seconds=duration_s)

    assert build_info["eta"] == expected_eta


def test_build_system_completion():
    """Test that build completes correctly and level increments."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=1000, clay=1000, iron=1000, crop=1000)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    # Initial level
    assert engine.buildings[1]["lumber_mill"] == 1

    # Queue build
    result = system.queue_build(village_id=1, building="lumber_mill", rules=rules, now=now)
    assert result is True

    # Before ETA - no completion
    before_eta = now + timedelta(seconds=30)
    delta_before = system.apply(now=before_eta, rules=rules)
    assert delta_before.is_empty()
    assert engine.buildings[1]["lumber_mill"] == 1  # Still level 1

    # After ETA - completion
    duration_s = rules.duration_s("lumber_mill", 2)
    after_eta = now + timedelta(seconds=duration_s + 1)
    delta_after = system.apply(now=after_eta, rules=rules)

    assert not delta_after.is_empty()
    assert (1, "lumber_mill") in delta_after.builds_completed
    assert engine.buildings[1]["lumber_mill"] == 2  # Level incremented
    assert 1 not in system.pending_builds  # Queue cleared


def test_build_system_resource_deduction():
    """Test that resources are deducted when build is queued."""
    engine = MemoryEngine()
    initial_wood = 1000
    engine.world[1].resources = Resources(wood=initial_wood, clay=1000, iron=1000, crop=1000)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    cost = int(rules.cost("lumber_mill", 2))

    result = system.queue_build(village_id=1, building="lumber_mill", rules=rules, now=now)
    assert result is True

    # Resources should be deducted
    assert engine.world[1].resources.wood == initial_wood - cost
