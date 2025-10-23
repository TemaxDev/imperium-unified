from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

BUILDINGS = ("lumber_mill", "clay_pit", "iron_mine", "farm")


@dataclass(frozen=True)
class Rules:
    version: str = "v1"
    base_rates: Dict[str, float] | None = None  # units/hour
    base_costs: Dict[str, float] | None = None  # resource-equivalent
    base_durations_s: Dict[str, float] | None = None  # seconds

    def rate(self, building: str, level: int) -> float:
        assert building in BUILDINGS, f"unknown building: {building}"
        assert 1 <= level <= 20, "level out of bounds [1..20]"
        return self.base_rates[building] * (1.15 ** (level - 1))

    def cost(self, building: str, level: int) -> float:
        assert building in BUILDINGS and 1 <= level <= 20
        return self.base_costs[building] * (1.28 ** (level - 1))

    def duration_s(self, building: str, level: int) -> float:
        assert building in BUILDINGS and 1 <= level <= 20
        return self.base_durations_s[building] * (1.32 ** (level - 1))


def default_rules() -> Rules:
    return Rules(
        base_rates={
            "lumber_mill": 60.0,
            "clay_pit": 60.0,
            "iron_mine": 60.0,
            "farm": 30.0,
        },
        base_costs={
            "lumber_mill": 60.0,
            "clay_pit": 60.0,
            "iron_mine": 60.0,
            "farm": 50.0,
        },
        base_durations_s={
            "lumber_mill": 60.0,
            "clay_pit": 60.0,
            "iron_mine": 60.0,
            "farm": 45.0,
        },
    )
