"""Adaptateur FileStorageEngine pour SimulationEngine.

Implémentation persistante utilisant un fichier JSON pour stocker l'état du monde.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models import BuildCmd, Resources, Village


class FileStorageEngine:
    """Moteur de simulation avec persistance fichier JSON.

    Implémente l'interface SimulationEngine avec stockage sur disque.
    Le fichier est lu au démarrage et écrit à chaque modification.
    """

    def __init__(self, storage_path: str = "./data/world.json") -> None:
        """Initialise le moteur avec le chemin de stockage.

        Args:
            storage_path: Chemin du fichier JSON de stockage
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()
        self.world = self._load_world()
        # A7 gameplay persistence (loaded from JSON)
        self.buildings: dict[int, dict[str, int]] = {}
        self.engine_state: dict[int, dict[str, datetime]] = {}
        self._load_gameplay_state()

    def _ensure_storage_exists(self) -> None:
        """Crée le répertoire de stockage et le fichier s'ils n'existent pas."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            # Initialiser avec un village par défaut (A7 includes buildings and engineState)
            default_world = {
                "villages": {
                    "1": {
                        "id": 1,
                        "name": "Capitale",
                        "resources": {"wood": 800, "clay": 800, "iron": 800, "crop": 800},
                        "queue": [],
                    }
                },
                "buildings": {
                    "1": {"lumber_mill": 1, "clay_pit": 1, "iron_mine": 1, "farm": 1}
                },
                "engineState": {
                    "1": {"last_tick": datetime.now(timezone.utc).isoformat()}
                },
            }
            self.storage_path.write_text(json.dumps(default_world, indent=2))

    def _load_world(self) -> dict[int, Village]:
        """Charge le monde depuis le fichier JSON.

        Supporte deux formats:
        1. Format legacy: resources dans chaque village
        2. Format seed: resources séparées dans data["resources"]

        Returns:
            Dictionnaire village_id -> Village
        """
        data = json.loads(self.storage_path.read_text())
        world: dict[int, Village] = {}

        # Charger resources séparées si présentes (format seed)
        resources_map = data.get("resources", {})

        for vid_str, v_data in data.get("villages", {}).items():
            vid = int(vid_str)

            # Priorité: resources dans village, sinon resources séparées, sinon défaut
            if "resources" in v_data:
                resources = Resources(**v_data["resources"])
            elif vid_str in resources_map:
                resources = Resources(**resources_map[vid_str])
            else:
                resources = Resources()

            # Charger queue: priorité buildQueues séparées, sinon queue dans village
            build_queues = data.get("buildQueues", {})
            if vid_str in build_queues:
                # Convertir format buildQueues vers queue simplifiée
                queue = [
                    f"{item['building']} -> L{item.get('level', 1)}"
                    for item in build_queues[vid_str]
                ]
            else:
                queue = v_data.get("queue", [])

            world[vid] = Village(
                id=v_data["id"],
                name=v_data["name"],
                resources=resources,
                queue=queue,
            )
        return world

    def _save_world(self) -> None:
        """Sauvegarde le monde dans le fichier JSON."""
        data: dict[str, Any] = {"villages": {}}
        for vid, village in self.world.items():
            data["villages"][str(vid)] = {
                "id": village.id,
                "name": village.name,
                "resources": {
                    "wood": village.resources.wood,
                    "clay": village.resources.clay,
                    "iron": village.resources.iron,
                    "crop": village.resources.crop,
                },
                "queue": village.queue,
            }
        self.storage_path.write_text(json.dumps(data, indent=2))

    def snapshot(self) -> list[Village]:
        """Retourne la liste de tous les villages.

        Returns:
            Liste de tous les villages du monde
        """
        return list(self.world.values())

    def get_village(self, vid: int) -> Village | None:
        """Récupère un village par son ID.

        Args:
            vid: ID du village

        Returns:
            Le village si trouvé, None sinon
        """
        return self.world.get(vid)

    def queue_build(self, cmd: BuildCmd) -> bool:
        """Ajoute une commande de construction à la queue d'un village.

        Args:
            cmd: Commande de construction

        Returns:
            True si la commande a été acceptée, False sinon
        """
        village = self.world.get(cmd.villageId)
        if not village:
            return False
        if not cmd.building or cmd.levelTarget <= 0:
            return False

        # Ajouter à la queue
        village.queue.append(f"{cmd.building} -> L{cmd.levelTarget}")

        # Persister immédiatement
        self._save_world()

        return True

    def _load_gameplay_state(self) -> None:
        """Load A7 gameplay state (buildings, engineState) from JSON."""
        data = json.loads(self.storage_path.read_text())

        # Load buildings
        buildings_data = data.get("buildings", {})
        for vid_str, bldgs in buildings_data.items():
            self.buildings[int(vid_str)] = bldgs

        # Load engine_state
        engine_state_data = data.get("engineState", {})
        for vid_str, state in engine_state_data.items():
            vid = int(vid_str)
            last_tick_str = state.get("last_tick")
            if last_tick_str:
                # Parse ISO format datetime
                last_tick = datetime.fromisoformat(last_tick_str)
                if last_tick.tzinfo is None:
                    last_tick = last_tick.replace(tzinfo=timezone.utc)
                self.engine_state[vid] = {"last_tick": last_tick}

        # Initialize defaults if missing
        for vid in self.world.keys():
            if vid not in self.buildings:
                self.buildings[vid] = {
                    "lumber_mill": 1,
                    "clay_pit": 1,
                    "iron_mine": 1,
                    "farm": 1,
                }
            if vid not in self.engine_state:
                self.engine_state[vid] = {"last_tick": datetime.now(timezone.utc)}
