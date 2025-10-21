"""Adaptateur FileStorageEngine pour SimulationEngine.

Implémentation persistante utilisant un fichier JSON pour stocker l'état du monde.
"""

import json
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

    def _ensure_storage_exists(self) -> None:
        """Crée le répertoire de stockage et le fichier s'ils n'existent pas."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            # Initialiser avec un village par défaut
            default_world = {
                "villages": {
                    "1": {
                        "id": 1,
                        "name": "Capitale",
                        "resources": {"wood": 800, "clay": 800, "iron": 800, "crop": 800},
                        "queue": [],
                    }
                }
            }
            self.storage_path.write_text(json.dumps(default_world, indent=2))

    def _load_world(self) -> dict[int, Village]:
        """Charge le monde depuis le fichier JSON.

        Returns:
            Dictionnaire village_id -> Village
        """
        data = json.loads(self.storage_path.read_text())
        world: dict[int, Village] = {}
        for vid_str, v_data in data.get("villages", {}).items():
            vid = int(vid_str)
            world[vid] = Village(
                id=v_data["id"],
                name=v_data["name"],
                resources=Resources(**v_data.get("resources", {})),
                queue=v_data.get("queue", []),
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
