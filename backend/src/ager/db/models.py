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
