"""Treaty service for managing diplomatic agreements (A8)."""

from datetime import datetime, timedelta
from typing import Any

from ..rules import DiplomacyRules
from .store import DiploStore


class TreatyService:
    """Manages diplomatic treaty proposals and lifecycle.

    Handles:
    - Treaty proposal validation
    - Opening new treaties with appropriate durations
    - Immediate stance/opinion adjustments
    - Idempotent duplicate detection
    """

    def __init__(self, store: DiploStore, rules: DiplomacyRules):
        """Initialize treaty service with store and rules.

        Args:
            store: Diplomacy data store
            rules: Diplomacy rules with default durations
        """
        self.store = store
        self.rules = rules

    def propose(
        self,
        a: int,
        b: int,
        treaty_type: str,
        now: datetime,
        duration_h: int | None = None,
    ) -> dict[str, Any]:
        """Propose a treaty between two factions.

        Validates the proposal, opens the treaty if accepted,
        and applies immediate effects to the relation.

        Args:
            a: First faction ID
            b: Second faction ID
            treaty_type: "CEASEFIRE", "TRADE", or "ALLIANCE"
            now: Current time
            duration_h: Treaty duration in hours (uses default if None)

        Returns:
            Dictionary with:
            - accepted: bool (True if treaty created)
            - treaty_id: int (if accepted)
            - expires_at: str ISO8601 (if accepted)
            - reason: str (if rejected)
        """
        # Validate treaty type
        if treaty_type not in {"CEASEFIRE", "TRADE", "ALLIANCE"}:
            return {"accepted": False, "reason": f"invalid_type: {treaty_type}"}

        # Normalize pair (always a < b)
        a, b = (a, b) if a < b else (b, a)

        # Check for duplicate active treaty of same type (soft idempotence)
        for treaty in self.store.list_treaties():
            if (
                treaty.status == "ACTIVE"
                and {treaty.a, treaty.b} == {a, b}
                and treaty.type == treaty_type
            ):
                self.store.log_event(
                    "treaty_propose_duplicate", {"a": a, "b": b, "type": treaty_type}, now
                )
                return {"accepted": False, "reason": "already_active"}

        # Determine duration (use default if not specified)
        if duration_h is None:
            duration_map = {
                "CEASEFIRE": self.rules.ceasefire_duration_h,
                "TRADE": self.rules.trade_duration_h,
                "ALLIANCE": self.rules.alliance_duration_h,
            }
            duration_h = duration_map[treaty_type]

        expires_at = now + timedelta(hours=duration_h)

        # Open the treaty
        treaty_id = self.store.open_treaty(a, b, treaty_type, now, expires_at)  # type: ignore[arg-type]

        # Apply immediate effects to relation
        rel = self.store.get_relation(a, b)
        if not rel:
            # Shouldn't happen if data is consistent, but handle gracefully
            return {"accepted": False, "reason": "relation_not_found"}

        new_st = rel.stance
        new_op = rel.opinion

        if treaty_type == "CEASEFIRE":
            # Lock to minimum NEUTRAL, give small opinion boost to materialize peace
            if new_st == "HOSTILE":
                new_st = "NEUTRAL"
                new_op = max(new_op, self.rules.hostile_threshold + 2.0)

        elif treaty_type == "TRADE":
            # No stance lock; benefits materialize via trade events (opinion bonus)
            pass

        elif treaty_type == "ALLIANCE":
            # Lock to ALLY and ensure opinion meets threshold
            new_st = "ALLY"
            if new_op < self.rules.ally_threshold:
                new_op = self.rules.ally_threshold

        # Persist updated relation
        self.store.upsert_relation(a, b, new_st, new_op, now)

        # Log treaty opening
        self.store.log_event(
            "treaty_open",
            {
                "id": treaty_id,
                "a": a,
                "b": b,
                "type": treaty_type,
                "expires_at": expires_at.isoformat(),
            },
            now,
        )

        return {
            "accepted": True,
            "treaty_id": treaty_id,
            "expires_at": expires_at.isoformat(),
        }
