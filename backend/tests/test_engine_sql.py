import sqlite3

from ager.adapters.sql_engine import SQLiteEngine
from ager.models import BuildCmd


def test_sql_engine_init_and_seed(tmp_path):
    """Test que SQLiteEngine initialise la DB et seed le village 1."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    # seed minimal
    v = eng.get_village(1)
    assert v is not None
    assert v.id == 1
    assert v.name == "Capitale"


def test_snapshot_returns_list(tmp_path):
    """Test snapshot retourne une liste de villages."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    snap = eng.snapshot()
    assert isinstance(snap, list)
    assert len(snap) >= 1


def test_get_village_existing(tmp_path):
    """Test get_village retourne un Village pour un ID existant."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    v = eng.get_village(1)
    assert v is not None
    assert v.id == 1
    assert hasattr(v, "resources")


def test_get_village_not_found(tmp_path):
    """Test get_village retourne None si village inexistant."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    v = eng.get_village(999_999)
    assert v is None


def test_queue_build_happy_path(tmp_path):
    """Test queue_build ajoute une construction pour un village valide."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    result = eng.queue_build(BuildCmd(villageId=1, building="farm", levelTarget=2))
    assert result is True
    # Vérifier que la queue contient l'élément
    v = eng.get_village(1)
    assert v is not None
    assert len(v.queue) == 1
    assert "farm -> L2" in v.queue


def test_queue_build_invalid_village(tmp_path):
    """Test queue_build retourne False si village inexistant."""
    db = tmp_path / "test.db"
    eng = SQLiteEngine(db)
    result = eng.queue_build(BuildCmd(villageId=999_999, building="farm", levelTarget=2))
    assert result is False


def test_db_file_creation(tmp_path):
    """Test que le fichier DB est créé au bon emplacement."""
    db_path = tmp_path / "custom" / "ager.db"
    SQLiteEngine(db_path)
    assert db_path.exists()
    assert db_path.is_file()


def test_tables_exist(tmp_path):
    """Test que les tables villages, resources, build_queue sont créées."""
    db = tmp_path / "test.db"
    SQLiteEngine(db)
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Vérifier que les tables existent
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "village" in tables
    assert "resources" in tables
    assert "build_queue" in tables

    conn.close()
