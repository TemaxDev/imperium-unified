from __future__ import annotations

from dataclasses import dataclass, field

VillageId = int


@dataclass
class ResourceDelta:
    wood: int = 0
    clay: int = 0
    iron: int = 0
    crop: int = 0


@dataclass
class SnapshotDelta:
    resources_changed: dict[VillageId, ResourceDelta] = field(default_factory=dict)
    builds_completed: list[tuple[VillageId, str]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.resources_changed and not self.builds_completed
