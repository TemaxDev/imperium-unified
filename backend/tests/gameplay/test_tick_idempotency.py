from datetime import UTC, datetime, timedelta

from ager.adapters.memory_engine import MemoryEngine
from ager.gameplay.engine import GameplayService
from ager.gameplay.rules import default_rules
from ager.gameplay.systems.build import BuildSystem
from ager.gameplay.systems.production import ProductionSystem


def test_tick_idempotency_same_now():
    """Test that calling tick with same 'now' twice produces empty delta on second call."""
    engine = MemoryEngine()
    service = GameplayService(
        production=ProductionSystem(engine),
        build=BuildSystem(engine),
        rules=default_rules(),
    )

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    now = start + timedelta(hours=1)

    # First tick - should produce changes
    delta1 = service.tick(now)
    assert not delta1.is_empty()
    assert 1 in delta1.resources_changed

    # Second tick with same now - should be empty (idempotent)
    delta2 = service.tick(now)
    assert delta2.is_empty()


def test_tick_idempotency_backwards_time():
    """Test that tick with earlier 'now' produces empty delta."""
    engine = MemoryEngine()
    service = GameplayService(
        production=ProductionSystem(engine),
        build=BuildSystem(engine),
        rules=default_rules(),
    )

    start = datetime(2025, 10, 22, 12, 0, 0, tzinfo=UTC)
    engine.engine_state[1]["last_tick"] = start

    # Advance to +2 hours
    now1 = start + timedelta(hours=2)
    delta1 = service.tick(now1)
    assert not delta1.is_empty()

    # Try to tick at +1 hour (in the past) - should be empty
    now2 = start + timedelta(hours=1)
    delta2 = service.tick(now2)
    assert delta2.is_empty()
