from ..models import BuildCmd, Resources, Village


class MemoryEngine:
    def __init__(self) -> None:
        self.world: dict[int, Village] = {
            1: Village(id=1, name="Capitale", resources=Resources(), queue=[])
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
