import pytest

@pytest.mark.asyncio
async def test_app_starts(client):
    r = await client.get("/")
    assert r.status_code in (200, 404)