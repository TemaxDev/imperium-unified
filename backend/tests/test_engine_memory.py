from ager.adapters.memory_engine import MemoryEngine
from ager.app import BuildCmd


def test_snapshot_not_empty():
    eng = MemoryEngine()
    snap = eng.snapshot()
    assert len(snap) >= 1
    assert snap[0].id == 1


def test_get_village_ok_and_nok():
    eng = MemoryEngine()
    assert eng.get_village(1) is not None
    assert eng.get_village(9999) is None


def test_queue_build_ok():
    eng = MemoryEngine()
    ok = eng.queue_build(BuildCmd(villageId=1, building="LumberCamp", levelTarget=2))
    assert ok is True
    v = eng.get_village(1)
    assert "LumberCamp" in v.queue[0]
