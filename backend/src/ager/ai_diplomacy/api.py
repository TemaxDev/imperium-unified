"""FastAPI router for AI Diplomacy internal endpoints (A8)."""

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Query

from ..container import get_engine
from ..ports import SimulationEngine
from .rules import default_rules
from .services import Evaluator, Proposer, TreatyService
from .services.store_impl import get_diplo_store

router = APIRouter(prefix="/ai/diplomacy", tags=["ai-diplomacy"])


def get_diplo_services(
    engine: SimulationEngine = Depends(get_engine),
) -> tuple[Any, Evaluator, Proposer, TreatyService]:
    """Dependency injection for diplomacy services.

    Returns:
        Tuple of (store, evaluator, proposer, treaty_service)
    """
    store = get_diplo_store(engine)
    rules = default_rules()
    evaluator = Evaluator(store, rules)
    proposer = Proposer(store, rules)
    treaty_service = TreatyService(store, rules)
    return store, evaluator, proposer, treaty_service


@router.post("/tick")
def diplo_tick(
    now: str | None = None,
    services: tuple = Depends(get_diplo_services),
) -> dict[str, Any]:
    """Apply diplomacy tick: cooldown opinions, expire treaties, recompute stances.

    Args:
        now: ISO8601 timestamp (uses current UTC time if None)
        services: Injected diplomacy services

    Returns:
        Dictionary with:
        - updated_relations: list of [a,b,old_op,old_st,new_op,new_st]
        - expired_treaties: list of treaty IDs
        - events: list of event summaries
    """
    _, evaluator, _, _ = services
    dt = datetime.now(UTC) if not now else datetime.fromisoformat(now)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    result = evaluator.tick_update(dt)

    # Convert tuples to lists for JSON serialization
    result["updated_relations"] = [list(r) for r in result["updated_relations"]]

    return cast(dict[str, Any], result)


@router.get("/suggest")
def diplo_suggest(
    a: int = Query(..., description="First faction ID"),
    b: int = Query(..., description="Second faction ID"),
    k: int = Query(3, description="Number of suggestions to return"),
    services: tuple = Depends(get_diplo_services),
) -> dict[str, Any]:
    """Get top-k AI diplomatic suggestions for faction pair.

    Args:
        a: First faction ID
        b: Second faction ID
        k: Number of suggestions (default 3)
        services: Injected diplomacy services

    Returns:
        Dictionary with:
        - suggestions: list of {type, score, reason}
    """
    _, _, proposer, _ = services
    now = datetime.now(UTC)

    suggestions = proposer.top_suggestions(a, b, now, k)

    return {
        "suggestions": [{"type": s.type, "score": s.score, "reason": s.reason} for s in suggestions]
    }


@router.post("/propose")
def diplo_propose(
    body: dict[str, Any],
    services: tuple = Depends(get_diplo_services),
) -> dict[str, Any]:
    """Propose a diplomatic treaty between two factions.

    Args:
        body: Request body with:
            - from: First faction ID
            - to: Second faction ID
            - type: Treaty type (CEASEFIRE/TRADE/ALLIANCE)
            - duration_h: Optional duration in hours (uses default if omitted)
        services: Injected diplomacy services

    Returns:
        Dictionary with:
        - accepted: bool
        - treaty_id: int (if accepted)
        - expires_at: str ISO8601 (if accepted)
        - reason: str (if rejected)
    """
    _, _, _, treaty_service = services

    a = body["from"]
    b = body["to"]
    treaty_type = body["type"]
    duration_h = body.get("duration_h")

    now = datetime.now(UTC)

    return cast(dict[str, Any], treaty_service.propose(a, b, treaty_type, now, duration_h))


@router.get("/rules")
def diplo_rules(
    services: tuple = Depends(get_diplo_services),
) -> dict[str, Any]:
    """Get current diplomacy rules and constants.

    Returns:
        Dictionary with all DiplomacyRules fields
    """
    _, evaluator, _, _ = services
    rules = evaluator.rules

    # Convert dataclass to dict
    return {
        "version": rules.version,
        "cooldown_factor": rules.cooldown_factor,
        "attack_penalty": rules.attack_penalty,
        "trade_bonus": rules.trade_bonus,
        "honor_bonus_per_hour": rules.honor_bonus_per_hour,
        "ally_threshold": rules.ally_threshold,
        "hostile_threshold": rules.hostile_threshold,
        "recent_window_h": rules.recent_window_h,
        "ceasefire_hostile_bonus": rules.ceasefire_hostile_bonus,
        "ceasefire_attack_w": rules.ceasefire_attack_w,
        "ceasefire_opinion_w": rules.ceasefire_opinion_w,
        "trade_recent_w": rules.trade_recent_w,
        "trade_opinion_pos_w": rules.trade_opinion_pos_w,
        "trade_block_if_active_penalty": rules.trade_block_if_active_penalty,
        "alliance_min_opinion": rules.alliance_min_opinion,
        "alliance_opinion_w": rules.alliance_opinion_w,
        "alliance_shared_enemy_w": rules.alliance_shared_enemy_w,
        "ceasefire_duration_h": rules.ceasefire_duration_h,
        "trade_duration_h": rules.trade_duration_h,
        "alliance_duration_h": rules.alliance_duration_h,
    }
