import pytest
from bson import ObjectId




@pytest.mark.asyncio
async def test_chat_new_ok(client, override_auth, override_mongo):
    r = await client.post("/chat/new")
    assert r.status_code == 200
    assert "chat_id" in r.json()


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200