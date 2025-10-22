"""Conteneur d'injection de dépendances pour AGER.

Gère l'instanciation et la fourniture du moteur de simulation
selon la configuration (variable d'environnement AGER_ENGINE).
"""

from .adapters.file_engine import FileStorageEngine
from .adapters.memory_engine import MemoryEngine
from .ports import SimulationEngine
from .settings import get_engine_type, get_storage_path

# Instance singleton du moteur (créée à l'import)
_engine: SimulationEngine | None = None


def _create_engine() -> SimulationEngine:
    """Crée une instance du moteur selon la configuration.

    Returns:
        Instance du moteur configuré (Memory ou File)
    """
    engine_type = get_engine_type()

    if engine_type == "memory":
        return MemoryEngine()
    elif engine_type == "file":
        storage_path = get_storage_path()
        return FileStorageEngine(storage_path)
    else:
        raise ValueError(f"Type de moteur inconnu: {engine_type}")


def get_engine() -> SimulationEngine:
    """Retourne l'instance singleton du moteur de simulation.

    Returns:
        Instance du moteur (MemoryEngine ou FileStorageEngine selon config)
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
