"""Diplomacy rules and constants (A8).

This module defines versioned diplomacy rules for opinion dynamics,
stance thresholds, and AI proposal scoring weights.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DiplomacyRules:
    """Versioned diplomacy rules (diplo_v1).

    All constants are calibrated for 30-60 min gameplay sessions.
    """

    version: str = "diplo_v1"

    # Opinion dynamics
    cooldown_factor: float = 0.98  # opinion *= 0.98 per game-hour at tick
    attack_penalty: float = 20.0  # Δopinion -= 20 per aggression
    trade_bonus: float = 8.0  # Δopinion += 8 per trade transaction
    honor_bonus_per_hour: float = 1.5  # +1.5 per hour of active treaty

    # Stances
    ally_threshold: float = 40.0  # ≥ 40 => ALLY
    hostile_threshold: float = -40.0  # ≤ -40 => HOSTILE

    # Proposer (recent events window & weights)
    recent_window_h: int = 24  # hours to consider recent events
    ceasefire_hostile_bonus: int = 1200  # points if stance==HOSTILE
    ceasefire_attack_w: int = 35  # +35 pts per recent attack (cap 5)
    ceasefire_opinion_w: int = 15  # +15 pts per point below -40

    trade_recent_w: int = 25  # +25 pts per recent trade (cap 5)
    trade_opinion_pos_w: int = 5  # +5 pts per opinion point above 0
    trade_block_if_active_penalty: int = 10_000  # block if TRADE already active

    alliance_min_opinion: float = 20.0  # only suggest ALLIANCE if opinion ≥ 20
    alliance_opinion_w: int = 20  # +20 pts per point above 20
    alliance_shared_enemy_w: int = 40  # +40 pts per shared enemy (cap 5)

    # Default durations (hours)
    ceasefire_duration_h: int = 12
    trade_duration_h: int = 24
    alliance_duration_h: int = 72


def default_rules() -> DiplomacyRules:
    """Return default diplomacy rules (diplo_v1)."""
    return DiplomacyRules()
