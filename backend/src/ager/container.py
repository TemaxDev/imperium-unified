from .adapters.memory_engine import MemoryEngine

_engine = MemoryEngine()


def get_engine() -> MemoryEngine:
    return _engine
