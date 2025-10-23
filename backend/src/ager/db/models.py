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
