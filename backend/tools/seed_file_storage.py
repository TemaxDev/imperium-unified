"""Script de seed pour FileStorageEngine.

Crée un fichier JSON d'état initial pour le FileStorageEngine avec
des villages, ressources et queues de construction pré-remplis.

Usage:
    python -m tools.seed_file_storage
    python -m tools.seed_file_storage --path custom/path.json
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_PATH = Path("data/ager_state.json")


def create_seed_state() -> dict:
    """Crée l'état initial du monde pour le seed.

    Returns:
        Dictionnaire contenant villages, resources et buildQueues
    """
    return {
        "villages": {
            "1": {"id": 1, "name": "Capitale"},
            "2": {"id": 2, "name": "Avant-Poste"},
        },
        "resources": {
            "1": {"wood": 100, "clay": 80, "iron": 90, "crop": 75},
            "2": {"wood": 60, "clay": 40, "iron": 50, "crop": 45},
        },
        "buildQueues": {
            "1": [
                {
                    "building": "farm",
                    "level": 2,
                    "queuedAt": datetime.now(UTC).isoformat(),
                }
            ],
            "2": [],
        },
    }


def main(path: Path = DEFAULT_PATH) -> None:
    """Crée le fichier de seed.

    Args:
        path: Chemin du fichier JSON à créer
    """
    state = create_seed_state()

    # Créer le répertoire parent si nécessaire
    path.parent.mkdir(parents=True, exist_ok=True)

    # Écrire le fichier JSON
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Seed created at: {path.resolve()}")
    print(f"[INFO] Created {len(state['villages'])} villages")
    print("[INFO] Build queues initialized")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed FileStorageEngine state")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_PATH,
        help=f"Path to state file (default: {DEFAULT_PATH})",
    )
    args = parser.parse_args()
    main(args.path)
