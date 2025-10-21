"""Tests unitaires pour FileStorageEngine."""

import json
import tempfile
from pathlib import Path

import pytest

from ager.adapters.file_engine import FileStorageEngine
from ager.models import BuildCmd, Village


@pytest.fixture()
def temp_storage():
    """Crée un fichier de stockage temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_world.json"
        yield str(storage_path)


def test_engine_creates_storage_if_missing(temp_storage):
    """Le moteur crée le fichier de stockage s'il n'existe pas."""
    engine = FileStorageEngine(temp_storage)
    assert Path(temp_storage).exists()
    assert len(engine.snapshot()) >= 1  # Village par défaut


def test_engine_loads_existing_storage(temp_storage):
    """Le moteur charge correctement un fichier existant."""
    # Créer un fichier de test
    data = {
        "villages": {
            "42": {
                "id": 42,
                "name": "TestVillage",
                "resources": {"wood": 100, "clay": 200, "iron": 300, "crop": 400},
                "queue": ["test"],
            }
        }
    }
    Path(temp_storage).parent.mkdir(parents=True, exist_ok=True)
    Path(temp_storage).write_text(json.dumps(data))

    # Charger
    engine = FileStorageEngine(temp_storage)
    villages = engine.snapshot()
    assert len(villages) == 1
    assert villages[0].id == 42
    assert villages[0].name == "TestVillage"
    assert villages[0].resources.wood == 100


def test_snapshot_returns_villages(temp_storage):
    """snapshot() retourne la liste des villages."""
    engine = FileStorageEngine(temp_storage)
    result = engine.snapshot()
    assert isinstance(result, list)
    assert all(isinstance(v, Village) for v in result)


def test_get_village_existing(temp_storage):
    """get_village() retourne un village existant."""
    engine = FileStorageEngine(temp_storage)
    villages = engine.snapshot()
    if villages:
        vid = villages[0].id
        result = engine.get_village(vid)
        assert result is not None
        assert result.id == vid


def test_get_village_nonexistent(temp_storage):
    """get_village() retourne None pour un village inexistant."""
    engine = FileStorageEngine(temp_storage)
    result = engine.get_village(999_999)
    assert result is None


def test_queue_build_persists_to_file(temp_storage):
    """queue_build() persiste la modification dans le fichier."""
    engine = FileStorageEngine(temp_storage)
    villages = engine.snapshot()
    assert len(villages) > 0

    vid = villages[0].id
    cmd = BuildCmd(villageId=vid, building="Farm", levelTarget=2)
    result = engine.queue_build(cmd)
    assert result is True

    # Vérifier que le fichier a été mis à jour
    data = json.loads(Path(temp_storage).read_text())
    village_data = data["villages"][str(vid)]
    assert any("Farm" in item for item in village_data["queue"])


def test_queue_build_reloads_correctly(temp_storage):
    """Une nouvelle instance recharge correctement les données persistées."""
    # Première instance : ajouter une commande
    engine1 = FileStorageEngine(temp_storage)
    villages = engine1.snapshot()
    vid = villages[0].id
    cmd = BuildCmd(villageId=vid, building="LumberCamp", levelTarget=3)
    engine1.queue_build(cmd)

    # Deuxième instance : vérifier que la commande est présente
    engine2 = FileStorageEngine(temp_storage)
    village = engine2.get_village(vid)
    assert village is not None
    assert any("LumberCamp" in item for item in village.queue)


def test_queue_build_invalid_village(temp_storage):
    """queue_build() refuse une commande pour un village inexistant."""
    engine = FileStorageEngine(temp_storage)
    cmd = BuildCmd(villageId=999_999, building="Farm", levelTarget=1)
    result = engine.queue_build(cmd)
    assert result is False


def test_queue_build_invalid_command(temp_storage):
    """queue_build() refuse une commande invalide."""
    engine = FileStorageEngine(temp_storage)
    villages = engine.snapshot()
    if villages:
        vid = villages[0].id

        # Building vide
        cmd1 = BuildCmd(villageId=vid, building="", levelTarget=1)
        assert engine.queue_build(cmd1) is False

        # Level invalide
        cmd2 = BuildCmd(villageId=vid, building="Farm", levelTarget=0)
        assert engine.queue_build(cmd2) is False
