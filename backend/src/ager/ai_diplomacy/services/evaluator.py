"""Evaluator service for diplomacy opinion/stance updates (A8)."""

from datetime import datetime
from typing import Any

from ..rules import DiplomacyRules
from .store import DiploStore


class Evaluator:
    """Evaluates and updates diplomacy relations based on time passage.

    Handles:
    - Opinion cooldown (decay towards 0 over time)
    - Stance recomputation (ALLY/NEUTRAL/HOSTILE)
    - Treaty expiration
    - Honor bonuses for active alliances
    """

    def __init__(self, store: DiploStore, rules: DiplomacyRules):
        """Initialize evaluator with store and rules.

        Args:
            store: Diplomacy data store
            rules: Diplomacy rules with constants
        """
        self.store = store
        self.rules = rules

    def tick_update(self, now: datetime) -> dict[str, Any]:
        """Apply time-based updates to diplomacy state.

        Processes:
        1. Expire treaties past their expiration date
        2. Apply opinion cooldown (multiplicative decay towards 0)
        3. Add honor bonuses for active alliances
        4. Recompute stances based on opinion + treaty locks

        Args:
            now: Current time for tick processing

        Returns:
            Dictionary with:
            - updated_relations: list of (a,b,old_op,old_st,new_op,new_st) tuples
            - expired_treaties: list of expired treaty IDs
            - events: list of event summaries
        """
        out: dict[str, Any] = {
            "updated_relations": [],
            "expired_treaties": [],
            "events": [],
        }

        # 1) Expire treaties that have reached their expiration time
        for treaty in self.store.list_treaties():
            if (
                treaty.status == "ACTIVE"
                and treaty.expires_at
                and datetime.fromisoformat(treaty.expires_at) <= now
            ):
                self.store.update_treaty_status(treaty.id, "EXPIRED")  # type: ignore[arg-type]
                out["expired_treaties"].append(treaty.id)
                self.store.log_event(
                    "treaty_expire",
                    {"id": treaty.id, "a": treaty.a, "b": treaty.b, "type": treaty.type},
                    now,
                )

        # 2) Build index of active treaties for stance locking
        active_locks: dict[tuple[int, int], str] = {}
        for treaty in self.store.list_treaties():
            if treaty.status == "ACTIVE":
                pair = (min(treaty.a, treaty.b), max(treaty.a, treaty.b))
                # Priority: ALLIANCE > CEASEFIRE (if multiple active)
                current = active_locks.get(pair)
                if current is None or (current == "CEASEFIRE" and treaty.type == "ALLIANCE"):
                    active_locks[pair] = treaty.type

        # 3) Update all relations: cooldown + honor + stance recompute
        for rel in self.store.list_relations():
            old_op = rel.opinion
            old_st = rel.stance
            last_updated = datetime.fromisoformat(rel.last_updated)

            # Calculate time delta in hours
            dt_seconds = max(0.0, (now - last_updated).total_seconds())
            dt_hours = dt_seconds / 3600.0

            # Apply cooldown (multiplicative decay towards 0)
            if dt_hours > 0:
                factor = self.rules.cooldown_factor**dt_hours
                new_op = old_op * factor
            else:
                new_op = old_op

            # Add honor bonus for active alliances
            lock_type = active_locks.get((rel.a, rel.b))
            if lock_type == "ALLIANCE" and dt_hours > 0:
                new_op += self.rules.honor_bonus_per_hour * dt_hours

            # Recompute stance based on opinion + treaty locks
            if lock_type == "ALLIANCE":
                new_st = "ALLY"  # Locked by alliance treaty
            elif lock_type == "CEASEFIRE":
                # CEASEFIRE enforces minimum NEUTRAL
                new_st = "NEUTRAL" if new_op < self.rules.ally_threshold else "ALLY"
            else:
                # Standard thresholds
                if new_op >= self.rules.ally_threshold:
                    new_st = "ALLY"
                elif new_op <= self.rules.hostile_threshold:
                    new_st = "HOSTILE"
                else:
                    new_st = "NEUTRAL"

            # Persist changes if significant (opinion changed, stance changed, or time passed)
            if abs(new_op - old_op) > 1e-6 or new_st != old_st or dt_hours > 0:
                self.store.upsert_relation(rel.a, rel.b, new_st, new_op, now)
                out["updated_relations"].append((rel.a, rel.b, old_op, old_st, new_op, new_st))

        # 4) Log tick event for audit
        self.store.log_event(
            "tick_update",
            {
                "updated_relations": len(out["updated_relations"]),
                "expired_treaties": len(out["expired_treaties"]),
            },
            now,
        )
        out["events"].append({"kind": "tick_update", "ts": now.isoformat()})

        return out
