from datetime import datetime, timezone
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
        self.engine_state: dict[int, dict[str, datetime]] = {
            1: {"last_tick": datetime.now(timezone.utc)}
        }

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
