from datetime import UTC, datetime, timedelta

from ager.adapters.memory_engine import MemoryEngine
from ager.gameplay.rules import default_rules
from ager.gameplay.systems.production import ProductionSystem


def test_production_system_zero_delta():
    """Test that Δt=0 produces no delta."""
    engine = MemoryEngine()
    system = ProductionSystem(engine)
    rules = default_rules()

    now = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = now

    delta = system.apply(now=now, rules=rules)

    assert delta.is_empty()


def test_production_system_one_hour():
    """Test production after exactly 1 hour."""
    engine = MemoryEngine()
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    # Advance 1 hour
    now = start + timedelta(hours=1)
    delta = system.apply(now=now, rules=rules)

    assert not delta.is_empty()
    assert 1 in delta.resources_changed

    res = delta.resources_changed[1]
    # Level 1 buildings: lumber_mill, clay_pit, iron_mine = 60/h, farm = 30/h
    assert res.wood == 60  # floor(60.0 * 1.0)
    assert res.clay == 60
    assert res.iron == 60
    assert res.crop == 30


def test_production_system_fractional_hour():
    """Test production with fractional Δt (30 minutes)."""
    engine = MemoryEngine()
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    # Advance 0.5 hours
    now = start + timedelta(minutes=30)
    delta = system.apply(now=now, rules=rules)

    assert not delta.is_empty()
    res = delta.resources_changed[1]
    # floor(60.0 * 0.5) = 30
    assert res.wood == 30
    assert res.clay == 30
    assert res.iron == 30
    assert res.crop == 15  # floor(30.0 * 0.5)


def test_production_system_cumulative():
    """Test cumulative production over 2 ticks."""
    engine = MemoryEngine()
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    # Initial resources
    initial_wood = engine.world[1].resources.wood

    # First tick: +1 hour
    now1 = start + timedelta(hours=1)
    delta1 = system.apply(now=now1, rules=rules)
    assert delta1.resources_changed[1].wood == 60

    after_tick1 = engine.world[1].resources.wood
    assert after_tick1 == initial_wood + 60

    # Second tick: +1 hour more
    now2 = now1 + timedelta(hours=1)
    delta2 = system.apply(now=now2, rules=rules)
    assert delta2.resources_changed[1].wood == 60

    after_tick2 = engine.world[1].resources.wood
    assert after_tick2 == initial_wood + 120


def test_production_system_idempotence():
    """Test idempotence: same now produces empty delta."""
    engine = MemoryEngine()
    system = ProductionSystem(engine)
    rules = default_rules()

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    now = start + timedelta(hours=1)
    delta1 = system.apply(now=now, rules=rules)
    assert not delta1.is_empty()

    # Same now again - should produce empty delta
    delta2 = system.apply(now=now, rules=rules)
    assert delta2.is_empty()
