import pytest
from httpx import AsyncClient, ASGITransport
from ager.app import app


@pytest.mark.asyncio
async def test_snapshot_and_village():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/snapshot")
        assert r.status_code == 200
        villages = r.json()["villages"]
        assert len(villages) >= 1
        vid = villages[0]["id"]

        r2 = await ac.get(f"/village/{vid}")
        assert r2.status_code == 200
        assert r2.json()["id"] == vid


@pytest.mark.asyncio
async def test_cmd_build():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/cmd/build", json={"villageId": 1, "building": "LumberCamp", "levelTarget": 2}
        )
        assert r.status_code == 200
        assert r.json()["accepted"] is True
