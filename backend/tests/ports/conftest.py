"""Fixtures pour les tests de contrat du port SimulationEngine."""

import pytest

from ager.adapters.memory_engine import MemoryEngine


@pytest.fixture()
def engine():
    """Fournit une instance fraîche du moteur pour chaque test.

    Cette fixture crée une nouvelle instance pour éviter le partage d'état entre tests.
    Elle est agnostique de l'implémentation : seule l'interface SimulationEngine compte.
    """
    return MemoryEngine()
