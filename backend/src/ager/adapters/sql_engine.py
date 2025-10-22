from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ..models import BuildCmd, Resources, Village

DDL = [
    """CREATE TABLE IF NOT EXISTS villages (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS resources (
        village_id INTEGER PRIMARY KEY,
        wood INTEGER DEFAULT 0,
        clay INTEGER DEFAULT 0,
        iron INTEGER DEFAULT 0,
        crop INTEGER DEFAULT 0,
        FOREIGN KEY(village_id) REFERENCES villages(id)
    )""",
    """CREATE TABLE IF NOT EXISTS build_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        building TEXT NOT NULL,
        level INTEGER NOT NULL,
        queued_at TEXT NOT NULL,
        FOREIGN KEY(village_id) REFERENCES villages(id)
    )""",
]


class SQLiteEngine:
    """Adaptateur SQLite pour le port SimulationEngine."""

    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        # check_same_thread=False si besoin futur multi-threads (FastAPI)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        with self._conn:
            for stmt in DDL:
                self._conn.execute(stmt)

        # seed minimal si vide
        cur = self._conn.execute("SELECT COUNT(*) AS c FROM villages")
        if cur.fetchone()["c"] == 0:
            with self._conn:
                self._conn.execute("INSERT INTO villages(id,name) VALUES (?,?)", (1, "Capitale"))
                self._conn.execute(
                    "INSERT INTO resources(village_id,wood,clay,iron,crop) " "VALUES (?,?,?,?,?)",
                    (1, 800, 800, 800, 800),
                )

    # --- Port methods -----------------------------------------------------

    def snapshot(self) -> list[Village]:
        """Retourne la liste de tous les villages."""
        cursor = self._conn.execute("SELECT id, name FROM villages")
        villages = []
        for row in cursor.fetchall():
            village_id = row["id"]
            name = row["name"]

            # Récupérer les ressources
            res_row = self._conn.execute(
                "SELECT wood, clay, iron, crop FROM resources WHERE village_id=?",
                (village_id,),
            ).fetchone()

            if res_row:
                resources = Resources(
                    wood=res_row["wood"],
                    clay=res_row["clay"],
                    iron=res_row["iron"],
                    crop=res_row["crop"],
                )
            else:
                resources = Resources()

            # Récupérer la queue de construction
            queue_rows = self._conn.execute(
                "SELECT building, level FROM build_queue WHERE village_id=? " "ORDER BY queued_at",
                (village_id,),
            ).fetchall()
            queue = [f"{r['building']} -> L{r['level']}" for r in queue_rows]

            villages.append(Village(id=village_id, name=name, resources=resources, queue=queue))

        return villages

    def get_village(self, vid: int) -> Village | None:
        """Récupère un village par son ID."""
        row = self._conn.execute("SELECT id, name FROM villages WHERE id=?", (vid,)).fetchone()
        if not row:
            return None

        # Récupérer les ressources
        res_row = self._conn.execute(
            "SELECT wood, clay, iron, crop FROM resources WHERE village_id=?",
            (vid,),
        ).fetchone()

        if res_row:
            resources = Resources(
                wood=res_row["wood"],
                clay=res_row["clay"],
                iron=res_row["iron"],
                crop=res_row["crop"],
            )
        else:
            resources = Resources()

        # Récupérer la queue de construction
        queue_rows = self._conn.execute(
            "SELECT building, level FROM build_queue WHERE village_id=? " "ORDER BY queued_at",
            (vid,),
        ).fetchall()
        queue = [f"{r['building']} -> L{r['level']}" for r in queue_rows]

        return Village(id=row["id"], name=row["name"], resources=resources, queue=queue)

    def queue_build(self, cmd: BuildCmd) -> bool:
        """Ajoute une commande de construction à la queue."""
        # Vérifier que le village existe
        v = self.get_village(cmd.villageId)
        if not v:
            return False

        # Vérifier la validité de la commande
        if not cmd.building or cmd.levelTarget <= 0:
            return False

        # Ajouter à la queue
        with self._conn:
            self._conn.execute(
                "INSERT INTO build_queue(village_id, building, level, queued_at) "
                "VALUES (?,?,?,?)",
                (
                    cmd.villageId,
                    cmd.building,
                    cmd.levelTarget,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return True
