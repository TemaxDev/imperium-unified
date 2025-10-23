from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ..deltas import SnapshotDelta
from ..rules import BUILDINGS, Rules

if TYPE_CHECKING:
    from ...ports import SimulationEngine


class BuildSystem:
    """Queue unique/village; débit à l'enqueue; level++ à ETA."""

    def __init__(self, engine: SimulationEngine):
        """Initialize build system with engine reference.

        Args:
            engine: The simulation engine (MemoryEngine, FileStorageEngine, or SQLiteEngine)
        """
        self.engine = engine
        # Track pending builds: {village_id: {"building": str, "target_level": int, "eta": datetime}}
        self.pending_builds: dict[int, dict] = {}

    def queue_build(self, *, village_id: int, building: str, rules: Rules, now: datetime) -> bool:
        """Queue a building upgrade if resources are sufficient.

        Args:
            village_id: ID of the village
            building: Building name (must be in BUILDINGS)
            rules: Game rules for cost and duration
            now: Current datetime

        Returns:
            True if queued successfully, False if insufficient resources or queue occupied
        """
        if building not in BUILDINGS:
            return False

        # Check if queue is already occupied
        if village_id in self.pending_builds:
            return False

        # Get village
        village = self.engine.get_village(village_id)
        if not village:
            return False

        # Get current building level
        if not hasattr(self.engine, "buildings"):
            return False

        buildings = self.engine.buildings.get(village_id, {})
        current_level = buildings.get(building, 0)
        target_level = current_level + 1

        if target_level > 20:
            return False

        # Calculate cost
        cost = int(rules.cost(building, target_level))

        # Check resources (simple: all buildings cost same resource mix for now)
        # For simplicity, we'll deduct from wood primarily
        if village.resources.wood < cost:
            return False

        # Deduct resources
        village.resources.wood -= cost

        # Calculate ETA
        duration_s = rules.duration_s(building, target_level)
        eta = now + timedelta(seconds=duration_s)

        # Queue the build
        self.pending_builds[village_id] = {
            "building": building,
            "target_level": target_level,
            "eta": eta,
        }

        return True

    def apply(self, *, now: datetime, rules: Rules) -> SnapshotDelta:
        """Process build completions where ETA <= now.

        Args:
            now: Current datetime
            rules: Game rules (not used but kept for interface consistency)

        Returns:
            SnapshotDelta with builds_completed
        """
        delta = SnapshotDelta()

        completed_villages = []

        for village_id, build_info in self.pending_builds.items():
            eta = build_info["eta"]
            if eta <= now:
                # Build is complete
                building = build_info["building"]
                target_level = build_info["target_level"]

                # Update building level
                if hasattr(self.engine, "buildings"):
                    if village_id not in self.engine.buildings:
                        self.engine.buildings[village_id] = {}
                    self.engine.buildings[village_id][building] = target_level

                # Record completion
                delta.builds_completed.append((village_id, building))
                completed_villages.append(village_id)

        # Clear completed builds from queue
        for village_id in completed_villages:
            del self.pending_builds[village_id]

        return delta
