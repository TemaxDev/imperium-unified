from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .deltas import SnapshotDelta
from .rules import Rules, default_rules
from .systems.build import BuildSystem
from .systems.production import ProductionSystem


@dataclass
class GameplayService:
    production: ProductionSystem
    build: BuildSystem
    rules: Rules = default_rules()

    def tick(self, now: datetime) -> SnapshotDelta:
        """Execute one gameplay tick: production then build completions.

        Args:
            now: Current datetime (timezone-aware)

        Returns:
            Merged SnapshotDelta with all changes
        """
        # Ordonner: Production puis Build
        d1 = self.production.apply(now=now, rules=self.rules)
        d2 = self.build.apply(now=now, rules=self.rules)

        # Merge deltas
        merged = SnapshotDelta()
        merged.resources_changed.update(d1.resources_changed)
        merged.builds_completed.extend(d1.builds_completed)

        # Merge d2 resources (if any)
        for vid, res in d2.resources_changed.items():
            if vid in merged.resources_changed:
                m = merged.resources_changed[vid]
                m.wood += res.wood
                m.clay += res.clay
                m.iron += res.iron
                m.crop += res.crop
            else:
                merged.resources_changed[vid] = res

        merged.builds_completed.extend(d2.builds_completed)

        return merged
