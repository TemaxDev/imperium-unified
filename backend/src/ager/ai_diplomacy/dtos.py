"""Data Transfer Objects for AI Diplomacy (A8)."""

from dataclasses import dataclass
from typing import Literal

StanceType = Literal["ALLY", "NEUTRAL", "HOSTILE"]
TreatyType = Literal["CEASEFIRE", "TRADE", "ALLIANCE"]
TreatyStatus = Literal["ACTIVE", "EXPIRED", "CANCELLED"]


@dataclass
class Faction:
    """Faction DTO."""

    id: int
    name: str
    is_player: bool


@dataclass
class Relation:
    """Relation between two factions (a < b)."""

    a: int
    b: int
    stance: StanceType
    opinion: float
    last_updated: str  # ISO8601


@dataclass
class Treaty:
    """Treaty between two factions."""

    id: int
    a: int
    b: int
    type: TreatyType
    status: TreatyStatus
    started_at: str  # ISO8601
    expires_at: str | None  # ISO8601 or None


@dataclass
class DiplomacyEvent:
    """Event log entry for audit."""

    id: int
    kind: str  # "attack" | "trade" | "treaty_open" | "treaty_expire" | "tick_update"
    payload: dict
    ts: str  # ISO8601


@dataclass
class Suggestion:
    """AI diplomatic suggestion."""

    type: TreatyType
    score: int  # Integer score for deterministic ordering
    reason: str
