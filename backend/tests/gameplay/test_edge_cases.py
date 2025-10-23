"""Edge case tests to improve branch coverage."""
from datetime import UTC, datetime, timedelta

from ager.adapters.memory_engine import MemoryEngine
from ager.gameplay.engine import GameplayService
from ager.gameplay.rules import default_rules
from ager.gameplay.systems.build import BuildSystem
from ager.gameplay.systems.production import ProductionSystem
from ager.models import Resources


def test_production_with_no_buildings():
    """Test production when village has no buildings."""
    engine = MemoryEngine()
    # Remove all buildings
    engine.buildings[1] = {}
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    now = start + timedelta(hours=1)
    delta = system.apply(now=now, rules=rules)

    # Should produce empty delta since no buildings
    assert delta.is_empty()


def test_production_with_zero_level_building():
    """Test production when building level is 0."""
    engine = MemoryEngine()
    engine.buildings[1]["lumber_mill"] = 0  # Zero level
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    now = start + timedelta(hours=1)
    delta = system.apply(now=now, rules=rules)

    # Lumber mill should not produce anything
    if 1 in delta.resources_changed:
        # Wood should be from other buildings only (clay_pit, iron_mine, farm)
        assert delta.resources_changed[1].wood == 0


def test_build_with_invalid_building_name():
    """Test that build with invalid building name is rejected."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=1000, clay=1000, iron=1000, crop=1000)
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)

    result = system.queue_build(
        village_id=1, building="invalid_building", rules=rules, now=now
    )

    assert result is False


def test_build_max_level_rejected():
    """Test that building beyond level 20 is rejected."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=10000, clay=10000, iron=10000, crop=10000)
    engine.buildings[1]["lumber_mill"] = 20  # Max level
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)

    result = system.queue_build(
        village_id=1, building="lumber_mill", rules=rules, now=now
    )

    assert result is False


def test_build_nonexistent_village():
    """Test that build for nonexistent village is rejected."""
    engine = MemoryEngine()
    system = BuildSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)

    result = system.queue_build(
        village_id=999, building="lumber_mill", rules=rules, now=now
    )

    assert result is False


def test_gameplay_service_merge_multiple_resources():
    """Test GameplayService properly merges resource deltas from multiple systems."""
    engine = MemoryEngine()
    engine.world[1].resources = Resources(wood=1000, clay=1000, iron=1000, crop=1000)

    service = GameplayService(
        production=ProductionSystem(engine),
        build=BuildSystem(engine),
        rules=default_rules(),
    )

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    # Queue a build first
    service.build.queue_build(village_id=1, building="lumber_mill", rules=service.rules, now=start)

    # Tick after some time
    now = start + timedelta(hours=1)
    delta = service.tick(now)

    # Should have production resources
    assert 1 in delta.resources_changed
    # Wood will be reduced due to build cost, but clay/iron/crop should increase
    assert delta.resources_changed[1].clay > 0
