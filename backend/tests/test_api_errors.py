import pytest
from httpx import ASGITransport, AsyncClient

from ager.app import app


@pytest.mark.asyncio
async def test_get_village_404():
    t = ASGITransport(app=app)
    async with AsyncClient(transport=t, base_url="http://test") as ac:
        r = await ac.get("/village/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cmd_build_422():
    t = ASGITransport(app=app)
    async with AsyncClient(transport=t, base_url="http://test") as ac:
        # village inconnu
        r = await ac.post("/cmd/build", json={"villageId": 9999, "building": "X", "levelTarget": 1})
        assert r.status_code == 422
        # payload invalide
        r2 = await ac.post("/cmd/build", json={"villageId": 1, "building": "", "levelTarget": 0})
        assert r2.status_code == 422
