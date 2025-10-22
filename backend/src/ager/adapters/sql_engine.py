from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import select

from ..db.migrations.runner import apply_migrations
from ..db.models import BuildQueue as BuildQueueORM
from ..db.models import Resources as ResourcesORM
from ..db.models import Village as VillageORM
from ..db.session import get_session
from ..models import BuildCmd, Resources, Village


class SQLiteEngine:
    """Adaptateur SQLite pour le port SimulationEngine (avec ORM)."""

    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)

        # Apply migrations (creates tables + seed if needed)
        migrations_dir = Path(__file__).parent.parent / "db" / "migrations"
        apply_migrations(self._db_path, migrations_dir)

    # --- Port methods -----------------------------------------------------

    def snapshot(self) -> list[Village]:
        """Retourne la liste de tous les villages."""
        with get_session(self._db_path) as session:
            villages_orm = session.exec(select(VillageORM)).all()
            villages = []

            for v_orm in villages_orm:
                if v_orm.id is None:
                    continue

                # Récupérer les ressources
                res_orm = session.exec(
                    select(ResourcesORM).where(ResourcesORM.village_id == v_orm.id)
                ).first()

                if res_orm:
                    resources = Resources(
                        wood=res_orm.wood,
                        clay=res_orm.clay,
                        iron=res_orm.iron,
                        crop=res_orm.crop,
                    )
                else:
                    resources = Resources()

                # Récupérer la queue de construction
                queue_orm = session.exec(
                    select(BuildQueueORM)
                    .where(BuildQueueORM.village_id == v_orm.id)
                    .order_by(BuildQueueORM.queued_at)
                ).all()
                queue = [f"{q.building} -> L{q.level}" for q in queue_orm]

                villages.append(
                    Village(id=v_orm.id, name=v_orm.name, resources=resources, queue=queue)
                )

            return villages

    def get_village(self, vid: int) -> Village | None:
        """Récupère un village par son ID."""
        with get_session(self._db_path) as session:
            v_orm = session.get(VillageORM, vid)
            if not v_orm or v_orm.id is None:
                return None

            # Récupérer les ressources
            res_orm = session.exec(
                select(ResourcesORM).where(ResourcesORM.village_id == vid)
            ).first()

            if res_orm:
                resources = Resources(
                    wood=res_orm.wood,
                    clay=res_orm.clay,
                    iron=res_orm.iron,
                    crop=res_orm.crop,
                )
            else:
                resources = Resources()

            # Récupérer la queue de construction
            queue_orm = session.exec(
                select(BuildQueueORM)
                .where(BuildQueueORM.village_id == vid)
                .order_by(BuildQueueORM.queued_at)
            ).all()
            queue = [f"{q.building} -> L{q.level}" for q in queue_orm]

            return Village(id=v_orm.id, name=v_orm.name, resources=resources, queue=queue)

    def queue_build(self, cmd: BuildCmd) -> bool:
        """Ajoute une commande de construction à la queue."""
        with get_session(self._db_path) as session:
            # Vérifier que le village existe
            v_orm = session.get(VillageORM, cmd.villageId)
            if not v_orm:
                return False

            # Vérifier la validité de la commande
            if not cmd.building or cmd.levelTarget <= 0:
                return False

            # Ajouter à la queue
            build_queue_entry = BuildQueueORM(
                village_id=cmd.villageId,
                building=cmd.building,
                level=cmd.levelTarget,
                queued_at=datetime.now(UTC).isoformat(),
            )
            session.add(build_queue_entry)
            session.commit()

            return True
