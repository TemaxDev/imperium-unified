"""Proposer service for AI diplomatic suggestions (A8)."""

from datetime import datetime, timedelta

from ..dtos import Suggestion
from ..rules import DiplomacyRules
from .store import DiploStore

# Deterministic tie-breaker for suggestions with equal scores
TYPE_RANK = {"CEASEFIRE": 0, "TRADE": 1, "ALLIANCE": 2}


class Proposer:
    """Generates AI diplomatic proposals with deterministic scoring.

    All scores are computed as integers (fixed-point) to ensure
    deterministic ordering across platforms and test environments.
    """

    def __init__(self, store: DiploStore, rules: DiplomacyRules):
        """Initialize proposer with store and rules.

        Args:
            store: Diplomacy data store
            rules: Diplomacy rules with scoring weights
        """
        self.store = store
        self.rules = rules

    def top_suggestions(self, a: int, b: int, now: datetime, k: int = 3) -> list[Suggestion]:
        """Generate top-k diplomatic suggestions for faction pair.

        Args:
            a: First faction ID
            b: Second faction ID
            now: Current time for recent event window
            k: Number of suggestions to return (default 3)

        Returns:
            List of Suggestion objects sorted by score (descending),
            with deterministic tie-breaking by TYPE_RANK.
        """
        # Normalize pair (always a < b)
        a, b = (a, b) if a < b else (b, a)

        # Get current relation
        rel = self.store.get_relation(a, b)
        if not rel:
            # No relation exists, return empty
            return []

        op = rel.opinion
        stance = rel.stance

        # Analyze recent events in rolling window
        window_h = self.rules.recent_window_h
        since = now - timedelta(hours=window_h)
        attacks_recent = 0
        trades_recent = 0

        for event in self.store.list_events(since=since):
            kind = event.kind
            payload = event.payload
            # Count events involving this pair (direction-agnostic)
            if {payload.get("a"), payload.get("b")} == {a, b}:
                if kind == "attack":
                    attacks_recent += 1
                elif kind == "trade":
                    trades_recent += 1

        # Count shared enemies (both have HOSTILE stance with same third faction)
        shared_enemies = 0
        all_factions = [f.id for f in self.store.list_factions() if f.id not in (a, b)]
        for c in all_factions:
            rel_ac = self.store.get_relation(a, c)
            rel_bc = self.store.get_relation(b, c)
            if rel_ac and rel_bc and rel_ac.stance == "HOSTILE" and rel_bc.stance == "HOSTILE":
                shared_enemies += 1

        # Check active treaties for this pair
        active_types: set[str] = set()
        for treaty in self.store.list_treaties():
            if treaty.status == "ACTIVE" and {treaty.a, treaty.b} == {a, b}:
                active_types.add(treaty.type)

        has_trade = "TRADE" in active_types
        has_alliance = "ALLIANCE" in active_types

        # === SCORING (all integers for determinism) ===

        # 1) CEASEFIRE score
        score_cf = -(10**9)  # Default: blocked
        reason_cf = ""
        if not has_alliance:  # Can't propose ceasefire if alliance active
            score_cf = 0
            if stance == "HOSTILE":
                score_cf += self.rules.ceasefire_hostile_bonus
            score_cf += self.rules.ceasefire_attack_w * min(attacks_recent, 5)
            # Points below hostile threshold (more negative = more bonus)
            below = max(0, int(round(-op - (-self.rules.hostile_threshold))))
            score_cf += self.rules.ceasefire_opinion_w * below
            reason_cf = f"hostile={stance=='HOSTILE'} attacks={attacks_recent} op={op:.1f}"

        # 2) TRADE score
        score_tr = 0
        reason_tr = ""
        if has_trade:
            score_tr -= self.rules.trade_block_if_active_penalty
            reason_tr = "trade_already_active"
        else:
            score_tr += self.rules.trade_recent_w * min(trades_recent, 5)
            score_tr += self.rules.trade_opinion_pos_w * max(0, int(round(op)))
            reason_tr = f"trades={trades_recent} op={op:.1f}"

        # 3) ALLIANCE score
        score_al = -(10**9)  # Default: blocked
        reason_al = ""
        if op >= self.rules.alliance_min_opinion and not has_alliance:
            score_al = self.rules.alliance_opinion_w * int(
                round(op - self.rules.alliance_min_opinion)
            )
            score_al += self.rules.alliance_shared_enemy_w * min(shared_enemies, 5)
            reason_al = f"op={op:.1f} shared_enemies={shared_enemies}"

        # Assemble candidates
        candidates = [
            Suggestion("CEASEFIRE", score_cf, reason_cf),
            Suggestion("TRADE", score_tr, reason_tr),
        ]
        # Only include ALLIANCE if it's viable
        if score_al > -(10**8):
            candidates.append(Suggestion("ALLIANCE", score_al, reason_al))

        # Sort: primary by score (desc), secondary by TYPE_RANK (asc)
        candidates.sort(key=lambda s: (-s.score, TYPE_RANK[s.type]))

        return candidates[:k]
