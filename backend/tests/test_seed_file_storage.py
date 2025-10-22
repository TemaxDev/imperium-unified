"""Tests de validation pour le seed FileStorageEngine."""

import json

from ager.adapters.file_engine import FileStorageEngine
from ager.models import BuildCmd
from tools.seed_file_storage import create_seed_state
from tools.seed_file_storage import main as seed_main


def test_create_seed_state_structure():
    """Le seed crée une structure JSON valide."""
    state = create_seed_state()
    assert "villages" in state
    assert "resources" in state
    assert "buildQueues" in state
    assert "1" in state["villages"]
    assert "2" in state["villages"]


def test_seed_main_creates_file(tmp_path):
    """La fonction main crée correctement le fichier."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    assert data_path.exists()
    state = json.loads(data_path.read_text(encoding="utf-8"))
    assert "villages" in state and "1" in state["villages"]


def test_seed_and_build(tmp_path):
    """Le seed permet de construire avec FileStorageEngine."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    engine = FileStorageEngine(str(data_path))
    cmd = BuildCmd(villageId=1, building="lumberCamp", levelTarget=2)
    res = engine.queue_build(cmd)
    assert res is True


def test_seed_snapshot_structure(tmp_path):
    """Le snapshot fonctionne avec un fichier seedé."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    engine = FileStorageEngine(str(data_path))
    villages = engine.snapshot()
    assert len(villages) >= 2
    assert all(hasattr(v, "id") for v in villages)
    assert all(hasattr(v, "name") for v in villages)
    assert all(hasattr(v, "resources") for v in villages)


def test_seed_loads_resources_correctly(tmp_path):
    """Les resources sont chargées depuis le format seed."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    engine = FileStorageEngine(str(data_path))
    village = engine.get_village(1)
    assert village is not None
    assert village.resources.wood == 100
    assert village.resources.clay == 80
    assert village.resources.iron == 90
    assert village.resources.crop == 75


def test_seed_loads_build_queues(tmp_path):
    """Les buildQueues sont chargées et converties."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    engine = FileStorageEngine(str(data_path))
    village = engine.get_village(1)
    assert village is not None
    assert len(village.queue) >= 1
    assert "farm" in village.queue[0].lower()


def test_seed_multiple_villages(tmp_path):
    """Le seed crée bien plusieurs villages."""
    data_path = tmp_path / "state.json"
    seed_main(data_path)

    engine = FileStorageEngine(str(data_path))
    v1 = engine.get_village(1)
    v2 = engine.get_village(2)

    assert v1 is not None
    assert v2 is not None
    assert v1.name == "Capitale"
    assert v2.name == "Avant-Poste"
    assert v1.resources.wood != v2.resources.wood  # Resources différentes


def test_seed_directory_creation(tmp_path):
    """Le seed crée le répertoire parent s'il n'existe pas."""
    nested_path = tmp_path / "deep" / "nested" / "state.json"
    assert not nested_path.parent.exists()

    seed_main(nested_path)

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_seed_overwrites_existing(tmp_path):
    """Le seed écrase un fichier existant."""
    data_path = tmp_path / "state.json"

    # Créer un fichier existant
    data_path.write_text('{"old": "data"}', encoding="utf-8")

    # Seed écrase
    seed_main(data_path)

    state = json.loads(data_path.read_text(encoding="utf-8"))
    assert "old" not in state
    assert "villages" in state
