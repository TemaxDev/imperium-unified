"""Modèles DTO stables (façade API)."""

from pydantic import BaseModel


class Resources(BaseModel):
    wood: int = 800
    clay: int = 800
    iron: int = 800
    crop: int = 800


class Village(BaseModel):
    id: int
    name: str
    resources: Resources = Resources()
    queue: list[str] = []


class BuildCmd(BaseModel):
    villageId: int
    building: str
    levelTarget: int
