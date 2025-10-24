"""Test diplomacy API endpoints (A8-5)."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from ager.app import app
from ager.container import reset_engine


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    """Set up memory engine for tests."""
    # Set environment to use memory engine
    monkeypatch.setenv("AGER_ENGINE", "memory")
    # Reset engine before and after each test
    reset_engine()
    yield
    reset_engine()


async def test_get_rules_returns_diplo_v1(client):
    """Test GET /ai/diplomacy/rules returns version and all constants."""
    response = await client.get("/ai/diplomacy/rules")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["version"] == "diplo_v1", "Should return diplo_v1"

    # Verify key constants present
    assert "cooldown_factor" in data
    assert "ally_threshold" in data
    assert "hostile_threshold" in data
    assert "ceasefire_duration_h" in data
    assert "trade_duration_h" in data
    assert "alliance_duration_h" in data

    # Verify values match defaults
    assert data["cooldown_factor"] == 0.98
    assert data["ally_threshold"] == 40.0
    assert data["hostile_threshold"] == -40.0


async def test_post_tick_returns_200_with_updates(client):
    """Test POST /ai/diplomacy/tick returns expected structure."""
    # Use current time to avoid negative dt with engine initialization
    start_time = datetime.now(UTC)

    # First tick to synchronize state
    await client.post("/ai/diplomacy/tick", params={"now": start_time.isoformat()})

    # Second tick 1 hour later to see updates
    later_time = start_time + timedelta(hours=1)
    response = await client.post("/ai/diplomacy/tick", params={"now": later_time.isoformat()})

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()

    # Verify structure
    assert "updated_relations" in data, "Should have updated_relations"
    assert "expired_treaties" in data, "Should have expired_treaties"
    assert "events" in data, "Should have events"

    # Should have 3 default relations updated (cooldown applied)
    assert len(data["updated_relations"]) == 3, "Should update 3 default relations"

    # Each update should be a list of 6 elements [a, b, old_op, old_st, new_op, new_st]
    for update in data["updated_relations"]:
        assert len(update) == 6, f"Update should have 6 elements, got {len(update)}"


async def test_get_suggest_returns_suggestions_with_scores(client):
    """Test GET /ai/diplomacy/suggest returns suggestions with integer scores."""
    response = await client.get("/ai/diplomacy/suggest", params={"a": 1, "b": 2, "k": 3})

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "suggestions" in data, "Should have suggestions key"

    suggestions = data["suggestions"]
    assert len(suggestions) <= 3, "Should return at most k=3 suggestions"

    # Verify structure of each suggestion
    for sugg in suggestions:
        assert "type" in sugg, "Suggestion should have type"
        assert "score" in sugg, "Suggestion should have score"
        assert "reason" in sugg, "Suggestion should have reason"

        # Verify score is integer
        assert isinstance(sugg["score"], int), f"Score should be int, got {type(sugg['score'])}"

        # Verify type is valid
        assert sugg["type"] in ("CEASEFIRE", "TRADE", "ALLIANCE"), f"Invalid type: {sugg['type']}"


async def test_suggest_deterministic_ordering(client):
    """Test that suggestions are deterministic (same state = same order)."""
    # Call twice with same parameters
    response1 = await client.get("/ai/diplomacy/suggest", params={"a": 1, "b": 2, "k": 3})
    response2 = await client.get("/ai/diplomacy/suggest", params={"a": 1, "b": 2, "k": 3})

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    suggestions1 = data1["suggestions"]
    suggestions2 = data2["suggestions"]

    # Verify identical ordering
    assert len(suggestions1) == len(suggestions2), "Should return same number of suggestions"

    for i, (s1, s2) in enumerate(zip(suggestions1, suggestions2, strict=True)):
        assert s1["type"] == s2["type"], f"Suggestion {i}: type differs"
        assert s1["score"] == s2["score"], f"Suggestion {i}: score differs"


async def test_post_propose_ceasefire_accepted(client):
    """Test POST /ai/diplomacy/propose accepts CEASEFIRE proposal."""
    start_time = datetime.now(UTC)

    # First tick to initialize state
    await client.post("/ai/diplomacy/tick", params={"now": start_time.isoformat()})

    # Propose ceasefire
    response = await client.post(
        "/ai/diplomacy/propose",
        json={"from": 1, "to": 2, "type": "CEASEFIRE", "duration_h": 12},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["accepted"] is True, "CEASEFIRE should be accepted"
    assert "treaty_id" in data, "Should return treaty_id"
    assert "expires_at" in data, "Should return expires_at"

    # Verify expires_at is in the future (within reasonable range)
    expires_at = datetime.fromisoformat(data["expires_at"])
    now = datetime.now(UTC)
    # Should be between 11 and 13 hours from now (allowing for processing time)
    time_until_expiry = (expires_at - now).total_seconds() / 3600
    assert 11 < time_until_expiry < 13, f"Expires should be ~12h from now, got {time_until_expiry}h"


async def test_post_propose_duplicate_rejected(client):
    """Test proposing duplicate treaty is rejected."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    await client.post("/ai/diplomacy/tick", params={"now": now.isoformat()})

    # Propose first alliance
    response1 = await client.post(
        "/ai/diplomacy/propose",
        json={"from": 1, "to": 2, "type": "ALLIANCE", "duration_h": 24},
    )
    assert response1.status_code == 200
    assert response1.json()["accepted"] is True

    # Propose duplicate alliance
    response2 = await client.post(
        "/ai/diplomacy/propose",
        json={"from": 1, "to": 2, "type": "ALLIANCE", "duration_h": 24},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["accepted"] is False, "Duplicate should be rejected"
    assert "reason" in data2, "Should provide rejection reason"


async def test_tick_with_treaty_expiration(client):
    """Test tick correctly expires treaties and updates relations."""
    start_time = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Initial tick
    await client.post("/ai/diplomacy/tick", params={"now": start_time.isoformat()})

    # Propose short ceasefire
    propose_response = await client.post(
        "/ai/diplomacy/propose",
        json={"from": 1, "to": 2, "type": "CEASEFIRE", "duration_h": 1},
    )
    assert propose_response.json()["accepted"] is True
    treaty_id = propose_response.json()["treaty_id"]

    # Advance 2 hours (past expiration)
    # The treaty was created at "now" in propose (which uses datetime.now(UTC))
    # So we need to advance from the actual treaty start time
    expires_at_str = propose_response.json()["expires_at"]
    expires_at = datetime.fromisoformat(expires_at_str)

    # Tick after expiration
    later_time = expires_at + timedelta(hours=1)
    tick_response = await client.post("/ai/diplomacy/tick", params={"now": later_time.isoformat()})

    assert tick_response.status_code == 200
    data = tick_response.json()

    # Verify treaty expired
    assert treaty_id in data["expired_treaties"], f"Treaty {treaty_id} should be expired"


async def test_suggest_respects_k_parameter(client):
    """Test that suggest endpoint respects k parameter."""
    # Request only 1 suggestion
    response = await client.get("/ai/diplomacy/suggest", params={"a": 1, "b": 2, "k": 1})

    assert response.status_code == 200
    data = response.json()

    suggestions = data["suggestions"]
    assert len(suggestions) <= 1, f"Should return at most k=1 suggestions, got {len(suggestions)}"


async def test_tick_idempotent_same_timestamp(client):
    """Test that calling tick with same timestamp is idempotent."""
    now = datetime(2025, 10, 23, 12, 0, 0, tzinfo=UTC)

    # First tick
    response1 = await client.post("/ai/diplomacy/tick", params={"now": now.isoformat()})
    assert response1.status_code == 200
    data1 = response1.json()

    # Second tick with same timestamp
    response2 = await client.post("/ai/diplomacy/tick", params={"now": now.isoformat()})
    assert response2.status_code == 200
    data2 = response2.json()

    # Second tick should have no significant updates (dt=0)
    # Relations may still be listed but opinion shouldn't change
    if len(data2["updated_relations"]) > 0:
        for update in data2["updated_relations"]:
            old_op, new_op = update[2], update[4]
            # Opinion should be virtually unchanged (within float tolerance)
            assert abs(new_op - old_op) < 1e-6, "Opinion should not change with dt=0"
