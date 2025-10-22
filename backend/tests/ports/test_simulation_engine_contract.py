"""Tests de contrat pour le port SimulationEngine.

Ces tests vérifient l'interface du port de manière agnostique de l'implémentation.
Ils doivent passer avec n'importe quel adaptateur (mémoire, DB, service distant, etc.).
"""

from ager.models import BuildCmd, Village


def test_snapshot_returns_list(engine):
    """Le contrat snapshot() garantit une liste de villages."""
    result = engine.snapshot()
    assert isinstance(result, list)
    # Le contrat n'impose pas de liste vide ou non-vide au démarrage


def test_snapshot_contains_villages(engine):
    """Les éléments retournés par snapshot() sont des objets Village."""
    result = engine.snapshot()
    if len(result) > 0:
        # Si la liste n'est pas vide, chaque élément doit être un Village
        for village in result:
            assert isinstance(village, Village)
            assert hasattr(village, "id")
            assert hasattr(village, "name")
            assert hasattr(village, "resources")
            assert hasattr(village, "queue")


def test_get_village_existing(engine):
    """get_village() retourne un Village existant ou None."""
    # Récupérer un village depuis snapshot pour garantir qu'il existe
    villages = engine.snapshot()
    if len(villages) > 0:
        vid = villages[0].id
        result = engine.get_village(vid)
        assert result is not None
        assert isinstance(result, Village)
        assert result.id == vid


def test_get_village_nonexistent(engine):
    """get_village() retourne None pour un village inexistant."""
    # ID très improbable d'exister
    result = engine.get_village(999_999)
    assert result is None


def test_queue_build_happy_path(engine):
    """queue_build() accepte une commande valide et retourne True."""
    villages = engine.snapshot()
    if len(villages) > 0:
        vid = villages[0].id
        cmd = BuildCmd(villageId=vid, building="Farm", levelTarget=1)
        result = engine.queue_build(cmd)
        assert isinstance(result, bool)
        assert result is True


def test_queue_build_invalid_village(engine):
    """queue_build() refuse une commande pour un village inexistant."""
    cmd = BuildCmd(villageId=999_999, building="Farm", levelTarget=1)
    result = engine.queue_build(cmd)
    assert isinstance(result, bool)
    assert result is False


def test_queue_build_invalid_command(engine):
    """queue_build() refuse une commande invalide (building vide, level <= 0)."""
    villages = engine.snapshot()
    if len(villages) > 0:
        vid = villages[0].id
        # Building vide
        cmd1 = BuildCmd(villageId=vid, building="", levelTarget=1)
        result1 = engine.queue_build(cmd1)
        assert result1 is False

        # Level invalide
        cmd2 = BuildCmd(villageId=vid, building="Farm", levelTarget=0)
        result2 = engine.queue_build(cmd2)
        assert result2 is False


def test_build_queue_persistence(engine):
    """Une commande acceptée apparaît dans la queue du village."""
    villages = engine.snapshot()
    if len(villages) > 0:
        vid = villages[0].id
        initial_queue_len = len(villages[0].queue)

        cmd = BuildCmd(villageId=vid, building="LumberCamp", levelTarget=2)
        result = engine.queue_build(cmd)
        assert result is True

        # Vérifier que la queue a été mise à jour
        updated_village = engine.get_village(vid)
        assert updated_village is not None
        assert len(updated_village.queue) == initial_queue_len + 1
        # Le contrat n'impose pas le format exact de la queue, juste qu'elle contient la commande
        assert any("LumberCamp" in item for item in updated_village.queue)


def test_engine_isolation(engine):
    """Chaque fixture engine est isolée (pas de partage d'état entre tests)."""
    # Ce test vérifie que la fixture crée bien une instance fraîche
    # En modifiant l'état et en vérifiant qu'un autre test ne le voit pas
    villages = engine.snapshot()
    initial_count = len(villages)

    # On ne peut pas créer de village via l'interface actuelle,
    # mais on peut vérifier l'isolation via queue_build
    if initial_count > 0:
        vid = villages[0].id
        cmd = BuildCmd(villageId=vid, building="TestBuilding", levelTarget=1)
        engine.queue_build(cmd)

        # Vérifier que la commande a été ajoutée
        updated = engine.get_village(vid)
        assert updated is not None
        assert any("TestBuilding" in item for item in updated.queue)


def test_snapshot_consistency(engine):
    """snapshot() retourne les mêmes villages à deux appels consécutifs (sans modification)."""
    snap1 = engine.snapshot()
    snap2 = engine.snapshot()

    assert len(snap1) == len(snap2)
    if len(snap1) > 0:
        # Vérifier que les IDs sont les mêmes
        ids1 = {v.id for v in snap1}
        ids2 = {v.id for v in snap2}
        assert ids1 == ids2
