"""Tests for SQLiteEngine with ORM."""


from ager.adapters.sql_engine import SQLiteEngine
from ager.models import BuildCmd


def test_migrations_apply_and_seed(tmp_path):
    """Test que les migrations sont appliquées et le seed est créé."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    # Vérifier que le village 1 est présent (seed)
    v = eng.get_village(1)
    assert v is not None
    assert v.id == 1
    assert v.name == "Capitale"
    assert v.resources.wood == 800
    assert v.resources.clay == 800
    assert v.resources.iron == 800
    assert v.resources.crop == 800


def test_snapshot_orm(tmp_path):
    """Test snapshot retourne village + resources via ORM."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    snap = eng.snapshot()
    assert isinstance(snap, list)
    assert len(snap) >= 1

    village = snap[0]
    assert village.id == 1
    assert village.name == "Capitale"
    assert village.resources.wood == 800


def test_build_queue_orm(tmp_path):
    """Test build() ajoute une rangée dans build_queue via ORM."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    result = eng.queue_build(BuildCmd(villageId=1, building="farm", levelTarget=2))
    assert result is True

    # Vérifier que la queue contient l'élément
    v = eng.get_village(1)
    assert v is not None
    assert len(v.queue) == 1
    assert "farm -> L2" in v.queue


def test_get_village_none(tmp_path):
    """Test get_village retourne None si id inconnu."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    v = eng.get_village(999_999)
    assert v is None


def test_build_not_found(tmp_path):
    """Test build retourne False si village inexistant."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    result = eng.queue_build(
        BuildCmd(villageId=999_999, building="farm", levelTarget=2)
    )
    assert result is False


def test_build_invalid_command(tmp_path):
    """Test build retourne False pour commande invalide."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)

    # Niveau invalide
    result = eng.queue_build(BuildCmd(villageId=1, building="farm", levelTarget=0))
    assert result is False

    # Bâtiment vide
    result = eng.queue_build(BuildCmd(villageId=1, building="", levelTarget=2))
    assert result is False


def test_orm_persistence(tmp_path):
    """Test que les données ORM persistent entre les instances."""
    db = tmp_path / "test.db"

    # Première instance: ajouter un build
    eng1 = SQLiteEngine(db)
    eng1.queue_build(BuildCmd(villageId=1, building="barracks", levelTarget=3))

    # Deuxième instance: vérifier que le build est toujours là
    eng2 = SQLiteEngine(db)
    v = eng2.get_village(1)
    assert v is not None
    assert len(v.queue) == 1
    assert "barracks -> L3" in v.queue
