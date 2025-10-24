from datetime import UTC, datetime

from ..models import BuildCmd, Resources, Village


class MemoryEngine:
    def __init__(self) -> None:
        self.world: dict[int, Village] = {
            1: Village(id=1, name="Capitale", resources=Resources(), queue=[])
        }
        # A7 gameplay persistence
        self.buildings: dict[int, dict[str, int]] = {
            1: {"lumber_mill": 1, "clay_pit": 1, "iron_mine": 1, "farm": 1}
        }
        self.engine_state: dict[int, dict[str, datetime]] = {1: {"last_tick": datetime.now(UTC)}}
        # A8 diplomacy persistence
        self.factions: dict[int, dict] = {
            1: {"id": 1, "name": "Player", "is_player": True},
            2: {"id": 2, "name": "Empire North", "is_player": False},
            3: {"id": 3, "name": "Guild East", "is_player": False},
        }
        self.relations: dict[str, dict] = {
            "1_2": {"a": 1, "b": 2, "stance": "NEUTRAL", "opinion": 0.0, "last_updated": datetime.now(UTC)},
            "1_3": {"a": 1, "b": 3, "stance": "NEUTRAL", "opinion": 0.0, "last_updated": datetime.now(UTC)},
            "2_3": {"a": 2, "b": 3, "stance": "NEUTRAL", "opinion": 0.0, "last_updated": datetime.now(UTC)},
        }
        self.treaties: dict[int, dict] = {}  # treaty_id -> treaty
        self.diplomacy_events: list[dict] = []  # event log
        self._next_treaty_id: int = 1

    def snapshot(self) -> list[Village]:
        return list(self.world.values())

    def get_village(self, vid: int) -> Village | None:
        return self.world.get(vid)

    def queue_build(self, cmd: BuildCmd) -> bool:
        v = self.world.get(cmd.villageId)
        if not v:
            return False
        if not cmd.building or cmd.levelTarget <= 0:
            return False
        v.queue.append(f"{cmd.building} -> L{cmd.levelTarget}")
        return True
