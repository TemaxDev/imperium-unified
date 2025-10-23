from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ..deltas import ResourceDelta, SnapshotDelta
from ..rules import BUILDINGS, Rules

if TYPE_CHECKING:
    from ...ports import SimulationEngine


class ProductionSystem:
    """Accrual déterministe.

    Intégré avec les adapters pour lire/écrire:
      - buildings (levels)
      - engine_state.last_tick
      - resources
    """

    def __init__(self, engine: SimulationEngine):
        """Initialize production system with engine reference.

        Args:
            engine: The simulation engine (MemoryEngine, FileStorageEngine, or SQLiteEngine)
        """
        self.engine = engine

    def apply(self, *, now: datetime, rules: Rules) -> SnapshotDelta:
        """Calculate and apply resource production since last tick.

        Args:
            now: Current datetime (timezone-aware)
            rules: Game rules for production calculations

        Returns:
            SnapshotDelta with resources_changed
        """
        delta = SnapshotDelta()

        # Get all villages from engine
        villages = self.engine.snapshot()

        for village in villages:
            vid = village.id
            if vid is None:
                continue

            # Get last_tick from engine_state (adapter-specific)
            if not hasattr(self.engine, "engine_state"):
                continue

            engine_state = self.engine.engine_state.get(vid)
            if not engine_state:
                continue

            last_tick = engine_state.get("last_tick")
            if not last_tick:
                continue

            # Calculate Δt in hours
            delta_seconds = (now - last_tick).total_seconds()
            if delta_seconds <= 0:
                # No time passed or time went backwards - idempotent
                continue

            delta_hours = delta_seconds / 3600.0

            # Get buildings for this village
            if not hasattr(self.engine, "buildings"):
                continue

            buildings = self.engine.buildings.get(vid, {})

            # Calculate production for each building
            resource_delta = ResourceDelta()
            for building in BUILDINGS:
                level = buildings.get(building, 0)
                if level <= 0:
                    continue

                # Calculate production: rate(level) * Δt
                rate_per_hour = rules.rate(building, level)
                production = int(rate_per_hour * delta_hours)  # floor

                # Map building to resource
                if building == "lumber_mill":
                    resource_delta.wood += production
                elif building == "clay_pit":
                    resource_delta.clay += production
                elif building == "iron_mine":
                    resource_delta.iron += production
                elif building == "farm":
                    resource_delta.crop += production

            # Apply production to village resources
            if resource_delta.wood or resource_delta.clay or resource_delta.iron or resource_delta.crop:
                village.resources.wood += resource_delta.wood
                village.resources.clay += resource_delta.clay
                village.resources.iron += resource_delta.iron
                village.resources.crop += resource_delta.crop
                delta.resources_changed[vid] = resource_delta

            # Update last_tick
            engine_state["last_tick"] = now

        return delta
