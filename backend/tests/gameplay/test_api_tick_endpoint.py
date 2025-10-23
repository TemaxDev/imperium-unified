from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient
import pytest

from ager.app import app
from ager.container import get_engine, reset_engine


@pytest.fixture(autouse=True)
def reset():
    """Reset engine before each test."""
    reset_engine()
    yield
    reset_engine()


@pytest.mark.anyio
async def test_tick_endpoint_basic():
    """Test that /cmd/tick endpoint responds correctly."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First, ensure engine is initialized
        response = await client.get("/snapshot")
        assert response.status_code == 200

        # Call tick with explicit now
        now_str = "2025-10-22T13:00:00Z"
        response = await client.post(f"/cmd/tick?now={now_str}")
        assert response.status_code == 200

        data = response.json()
        assert "resources_changed" in data
        assert "builds_completed" in data


@pytest.mark.anyio
async def test_tick_endpoint_structure():
    """Test that /cmd/tick returns correct structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        now_str = "2025-10-22T14:00:00Z"
        response = await client.post(f"/cmd/tick?now={now_str}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["resources_changed"], dict)
        assert isinstance(data["builds_completed"], list)


@pytest.mark.anyio
async def test_tick_endpoint_idempotence():
    """Test that calling tick twice with same 'now' is idempotent."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Initialize with snapshot
        await client.get("/snapshot")

        now_str = "2025-10-22T15:00:00Z"

        # First call
        response1 = await client.post(f"/cmd/tick?now={now_str}")
        assert response1.status_code == 200
        data1 = response1.json()

        # Second call with same now
        response2 = await client.post(f"/cmd/tick?now={now_str}")
        assert response2.status_code == 200
        data2 = response2.json()

        # Second call should have empty changes
        assert len(data2["resources_changed"]) == 0 or all(
            sum(vars(v).values()) == 0 for v in data2["resources_changed"].values()
        )


@pytest.mark.anyio
async def test_rules_endpoint():
    """Test that /rules endpoint returns gameplay rules."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/rules")
        assert response.status_code == 200

        data = response.json()
        assert data["version"] == "v1"
        assert "base_rates" in data
        assert "base_costs" in data
        assert "base_durations_s" in data

        # Check some expected values
        assert data["base_rates"]["lumber_mill"] == 60.0
        assert data["base_rates"]["farm"] == 30.0
