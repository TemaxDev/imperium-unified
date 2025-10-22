"""Configuration et settings pour AGER.

Gère les variables d'environnement et la configuration de l'application.
"""

import os
from typing import Literal

# Type pour les implémentations de moteur disponibles
EngineType = Literal["memory", "file", "sql"]


def get_engine_type() -> EngineType:
    """Retourne le type de moteur à utiliser depuis la variable d'environnement.

    Variable d'environnement:
        AGER_ENGINE: Type de moteur ("memory" ou "file"). Défaut: "memory"

    Returns:
        Type de moteur à instancier
    """
    engine = os.getenv("AGER_ENGINE", "memory").lower()
    if engine not in ("memory", "file", "sql"):
        raise ValueError(
            f"AGER_ENGINE invalide: {engine}. Valeurs acceptées: 'memory', 'file', 'sql'"
        )
    return engine  # type: ignore[return-value]


def get_storage_path() -> str:
    """Retourne le chemin du fichier de stockage pour FileStorageEngine.

    Variable d'environnement:
        AGER_STORAGE_PATH: Chemin du fichier JSON. Défaut: "./data/world.json"

    Returns:
        Chemin absolu ou relatif du fichier de stockage
    """
    return os.getenv("AGER_STORAGE_PATH", "./data/world.json")


def get_db_path() -> str:
    """Retourne le chemin de la base de données SQLite pour SQLiteEngine.

    Variable d'environnement:
        AGER_DB_PATH: Chemin de la base SQLite. Défaut: "./data/ager.db"

    Returns:
        Chemin absolu ou relatif de la base de données
    """
    return os.getenv("AGER_DB_PATH", "./data/ager.db")
