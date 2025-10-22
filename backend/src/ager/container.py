"""Conteneur d'injection de dépendances pour AGER.

Gère l'instanciation et la fourniture du moteur de simulation
selon la configuration (variable d'environnement AGER_ENGINE).
"""

from pathlib import Path

from .adapters.file_engine import FileStorageEngine
from .adapters.memory_engine import MemoryEngine
from .adapters.sql_engine import SQLiteEngine
from .ports import SimulationEngine
from .settings import get_db_path, get_engine_type, get_storage_path

# Instance singleton du moteur (créée à l'import)
_engine: SimulationEngine | None = None


def _create_engine() -> SimulationEngine:
    """Crée une instance du moteur selon la configuration.

    Returns:
        Instance du moteur configuré (Memory, File ou SQL)
    """
    engine_type = get_engine_type()

    if engine_type == "memory":
        return MemoryEngine()
    elif engine_type == "file":
        storage_path = get_storage_path()
        return FileStorageEngine(storage_path)
    elif engine_type == "sql":
        db_path = Path(get_db_path())
        return SQLiteEngine(db_path)
    else:
        raise ValueError(f"Type de moteur inconnu: {engine_type}")


def get_engine() -> SimulationEngine:
    """Retourne l'instance singleton du moteur de simulation.

    Returns:
        Instance du moteur (MemoryEngine, FileStorageEngine ou SQLiteEngine selon config)
    """
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def reset_engine() -> None:
    """Réinitialise le moteur (utile pour les tests).

    Force la recréation du moteur au prochain appel de get_engine().
    """
    global _engine
    _engine = None
