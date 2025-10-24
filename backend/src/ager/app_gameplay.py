from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends

from .container import get_engine
from .gameplay.engine import GameplayService
from .gameplay.rules import default_rules
from .gameplay.systems.build import BuildSystem
from .gameplay.systems.production import ProductionSystem
from .ports import SimulationEngine

router = APIRouter(prefix="", tags=["gameplay-internal"])


def get_gameplay_service(engine: SimulationEngine = Depends(get_engine)) -> GameplayService:
    """Dependency to get GameplayService with current engine."""
    return GameplayService(
        production=ProductionSystem(engine),
        build=BuildSystem(engine),
        rules=default_rules(),
    )


@router.post("/cmd/tick")
def cmd_tick(
    now: str | None = None, service: GameplayService = Depends(get_gameplay_service)
) -> dict[str, Any]:
    """Execute gameplay tick (production + build completions).

    Args:
        now: Optional ISO format datetime string. If not provided, uses current UTC time.
        service: Injected GameplayService

    Returns:
        Dictionary with resources_changed and builds_completed
    """
    dt = datetime.now(UTC) if not now else datetime.fromisoformat(now)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    delta = service.tick(dt)

    return {
        "resources_changed": {str(k): vars(v) for k, v in delta.resources_changed.items()},
        "builds_completed": [(vid, b) for (vid, b) in delta.builds_completed],
    }


@router.get("/rules")
def get_rules(service: GameplayService = Depends(get_gameplay_service)) -> dict[str, Any]:
    """Get current gameplay rules.

    Returns:
        Dictionary with version, base_rates, base_costs, base_durations_s
    """
    r = service.rules
    return {
        "version": r.version,
        "base_rates": r.base_rates,
        "base_costs": r.base_costs,
        "base_durations_s": r.base_durations_s,
    }
