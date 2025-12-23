import pytest

@pytest.mark.asyncio
async def test_register(client):
    r = await client.post(
        "/auth/register",
        json={
            "username": "test_user",
            "password": "Test12345",
            "preferred_language": "ru"
        }
    )

    assert r.status_code in (200, 409)

@pytest.fixture
def auth_headers():
    return {
        "Authorization": "Bearer fake-token"
    }