from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

VillageId = int


@dataclass
class ResourceDelta:
    wood: int = 0
    clay: int = 0
    iron: int = 0
    crop: int = 0


@dataclass
class SnapshotDelta:
    resources_changed: Dict[VillageId, ResourceDelta] = field(default_factory=dict)
    builds_completed: List[Tuple[VillageId, str]] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.resources_changed and not self.builds_completed
