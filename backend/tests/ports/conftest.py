"""Fixtures pour les tests de contrat du port SimulationEngine."""

import os
import tempfile
from pathlib import Path

import pytest

from ager.adapters.file_engine import FileStorageEngine
from ager.adapters.memory_engine import MemoryEngine
from ager.adapters.sql_engine import SQLiteEngine
from ager.ports import SimulationEngine


@pytest.fixture()
def engine() -> SimulationEngine:
    """Fournit une instance fraîche du moteur pour chaque test.

    Le type de moteur est déterminé par la variable d'environnement TEST_ENGINE_IMPL:
    - "memory" (défaut): MemoryEngine
    - "file": FileStorageEngine avec stockage temporaire
    - "sql": SQLiteEngine avec base de données temporaire

    Cette fixture crée une nouvelle instance pour éviter le partage d'état entre tests.
    Elle est agnostique de l'implémentation : seule l'interface SimulationEngine compte.
    """
    engine_type = os.getenv("TEST_ENGINE_IMPL", "memory").lower()

    if engine_type == "memory":
        return MemoryEngine()
    elif engine_type == "file":
        # Créer un fichier temporaire pour chaque test
        tmpdir = tempfile.mkdtemp()
        storage_path = Path(tmpdir) / "test_world.json"
        return FileStorageEngine(str(storage_path))
    elif engine_type == "sql":
        # Créer une base de données temporaire pour chaque test
        tmpdir = tempfile.mkdtemp()
        db_path = Path(tmpdir) / "test_ager.db"
        return SQLiteEngine(db_path)
    else:
        raise ValueError(
            f"TEST_ENGINE_IMPL invalide: {engine_type}. " "Valeurs: 'memory', 'file', 'sql'"
        )
