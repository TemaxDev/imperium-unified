"""ORM models for AGER using SQLModel."""

from __future__ import annotations

from sqlmodel import Field, SQLModel


class Village(SQLModel, table=True):
    """Village ORM model."""

    id: int | None = Field(default=None, primary_key=True)
    name: str


class Resources(SQLModel, table=True):
    """Resources ORM model."""

    village_id: int = Field(primary_key=True, foreign_key="village.id")
    wood: int = 0
    clay: int = 0
    iron: int = 0
    crop: int = 0


class BuildQueue(SQLModel, table=True):
    """Build queue ORM model."""

    __tablename__ = "build_queue"

    id: int | None = Field(default=None, primary_key=True)
    village_id: int = Field(foreign_key="village.id")
    building: str
    level: int
    queued_at: str


class Building(SQLModel, table=True):
    """Building levels ORM model (A7)."""

    __tablename__ = "buildings"

    village_id: int = Field(primary_key=True, foreign_key="village.id")
    building: str = Field(primary_key=True)
    level: int = Field(default=1)


class EngineState(SQLModel, table=True):
    """Engine state ORM model (A7) - tracks last tick per village."""

    __tablename__ = "engine_state"

    village_id: int = Field(primary_key=True, foreign_key="village.id")
    last_tick: str


# A8 Diplomacy Models


class Faction(SQLModel, table=True):
    """Faction ORM model (A8)."""

    __tablename__ = "factions"

    id: int = Field(primary_key=True)
    name: str
    is_player: int = Field(default=0)  # SQLite uses INTEGER for booleans


class Relation(SQLModel, table=True):
    """Relation between factions ORM model (A8).

    Relations are always stored with a < b (normalized pair).
    """

    __tablename__ = "relations"

    a: int = Field(primary_key=True, foreign_key="factions.id")
    b: int = Field(primary_key=True, foreign_key="factions.id")
    stance: str = Field(default="NEUTRAL")
    opinion: float = Field(default=0.0)
    last_updated: str


class Treaty(SQLModel, table=True):
    """Treaty ORM model (A8)."""

    __tablename__ = "treaties"

    id: int | None = Field(default=None, primary_key=True)
    a: int = Field(foreign_key="factions.id")
    b: int = Field(foreign_key="factions.id")
    type: str  # CEASEFIRE, TRADE, ALLIANCE
    status: str = Field(default="ACTIVE")  # ACTIVE, EXPIRED, CANCELLED
    started_at: str
    expires_at: str | None = None


class DiplomacyEvent(SQLModel, table=True):
    """Diplomacy event log ORM model (A8)."""

    __tablename__ = "diplomacy_events"

    id: int | None = Field(default=None, primary_key=True)
    kind: str  # attack, trade, treaty_open, treaty_expire, tick_update
    payload: str  # JSON string
    ts: str  # ISO8601 timestamp
