import sys

from fastapi import FastAPI, HTTPException

from . import __version__
from .ai_diplomacy.api import router as diplomacy_router
from .app_gameplay import router as gameplay_router
from .container import get_engine
from .models import BuildCmd, Village

app = FastAPI(title="Imperium Backend", version=__version__)

# Include gameplay routes (A7)
app.include_router(gameplay_router)

# Include diplomacy routes (A8)
app.include_router(diplomacy_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "imperium-backend",
        "version": __version__,
        "python": sys.version.split()[0],
    }


# --- routes façade (via port/engine) ---
@app.get("/snapshot")
def snapshot() -> dict[str, list[Village]]:
    return {"villages": get_engine().snapshot()}


@app.get("/village/{vid}")
def get_village(vid: int) -> Village:
    v = get_engine().get_village(vid)
    if not v:
        raise HTTPException(status_code=404, detail="Village not found")
    return v


@app.post("/cmd/build")
def cmd_build(cmd: BuildCmd) -> dict[str, bool]:
    ok = get_engine().queue_build(cmd)
    if not ok:
        raise HTTPException(status_code=422, detail="Invalid build command")
    return {"accepted": True}
