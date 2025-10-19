"""Tests d'initialisation du module AGER."""

import ager


def test_ager_version() -> None:
    """Vérifie que la version AGER est définie."""
    assert hasattr(ager, "__version__")
    assert isinstance(ager.__version__, str)
    assert "0.1.0" in ager.__version__
