from fastapi import FastAPI
import sys
from . import __version__

app = FastAPI(title="Imperium Backend", version=__version__)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "imperium-backend",
        "version": __version__,
        "python": sys.version.split()[0],
    }


from pydantic import BaseModel
from typing import Dict


# --- modèles façade ---
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


# --- état mock en mémoire (remplacé par AGER plus tard) ---
WORLD: Dict[int, Village] = {
    1: Village(id=1, name="Capitale"),
}


@app.get("/snapshot")
def snapshot() -> Dict[str, list[Village]]:
    return {"villages": list(WORLD.values())}


@app.get("/village/{vid}")
def get_village(vid: int) -> Village:
    v = WORLD.get(vid)
    if not v:
        raise RuntimeError(f"Village {vid} not found")
    return v


@app.post("/cmd/build")
def cmd_build(cmd: BuildCmd) -> Dict[str, bool]:
    v = WORLD.get(cmd.villageId)
    if not v:
        raise RuntimeError(f"Village {cmd.villageId} not found")
    v.queue.append(f"{cmd.building} -> L{cmd.levelTarget}")
    return {"accepted": True}
