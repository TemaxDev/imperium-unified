import pytest
from httpx import ASGITransport, AsyncClient

from ager.app import app


@pytest.mark.asyncio
async def test_health_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data and "python" in data
