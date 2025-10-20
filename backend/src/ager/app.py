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
