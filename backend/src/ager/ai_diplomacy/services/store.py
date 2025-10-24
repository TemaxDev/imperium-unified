"""Diplomacy storage abstraction (A8).

Provides a facade for reading/writing factions, relations, treaties,
and events across Memory/File/SQL implementations.
"""

from datetime import datetime
from typing import Protocol

from ..dtos import DiplomacyEvent, Faction, Relation, Treaty, TreatyStatus, TreatyType


def normalize_pair(a: int, b: int) -> tuple[int, int]:
    """Normalize faction pair to (min, max) ordering.

    Contract: relations are always stored with a < b.
    """
    return (min(a, b), max(a, b))


class DiploStore(Protocol):
    """Storage protocol for diplomacy data.

    All implementations (Memory/File/SQL) must provide these methods.
    Relations are always normalized to (a < b) internally.
    """

    # Factions
    def list_factions(self) -> list[Faction]:
        """Return all factions."""
        ...

    def get_faction(self, faction_id: int) -> Faction | None:
        """Return faction by id, or None if not found."""
        ...

    # Relations (always normalized a < b)
    def get_relation(self, a: int, b: int) -> Relation | None:
        """Get relation between factions (auto-normalizes a,b)."""
        ...

    def upsert_relation(self, a: int, b: int, stance: str, opinion: float, now: datetime) -> None:
        """Create or update relation (auto-normalizes a,b)."""
        ...

    def list_relations(self) -> list[Relation]:
        """Return all relations."""
        ...

    # Treaties (always normalized a < b)
    def list_treaties(self) -> list[Treaty]:
        """Return all treaties."""
        ...

    def get_treaty(self, treaty_id: int) -> Treaty | None:
        """Get treaty by id."""
        ...

    def open_treaty(
        self,
        a: int,
        b: int,
        treaty_type: TreatyType,
        started_at: datetime,
        expires_at: datetime | None = None,
    ) -> int:
        """Open new treaty (auto-normalizes a,b).

        Returns treaty_id.
        """
        ...

    def update_treaty_status(self, treaty_id: int, status: TreatyStatus) -> None:
        """Update treaty status (ACTIVE/EXPIRED/CANCELLED)."""
        ...

    # Events log
    def log_event(self, kind: str, payload: dict, ts: datetime) -> None:
        """Log diplomacy event for audit."""
        ...

    def list_events(
        self, since: datetime | None = None, limit: int | None = None
    ) -> list[DiplomacyEvent]:
        """List events, optionally filtered by time and limited."""
        ...
