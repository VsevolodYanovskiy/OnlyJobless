import pytest
from httpx import AsyncClient
from uuid import uuid4
import pytest
from app.auth.deps import get_current_user
from app.main import app
from app.users.models import User
import uuid

from app.main import app
from app.auth.deps import get_current_user


class FakeUser:
    def __init__(self):
        self.id = uuid4()
        self.username = "test"
        self.preferred_language = "ru"


@pytest.fixture(autouse=True)
def override_auth():
    async def fake_user():
        return User(
            id=uuid.uuid4(),
            username="test",
            password_hash="x",
            preferred_language="ru",
        )

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


from app.db.deps import get_mongo


class FakeMongo:
    class chats:
        @staticmethod
        async def count_documents(*args, **kwargs):
            return 0

        @staticmethod
        async def insert_one(doc):
            class R:
                inserted_id = "fake_id"
            return R()

        @staticmethod
        async def find_one(*args, **kwargs):
            return None


@pytest.fixture
def override_mongo():
    app.dependency_overrides[get_mongo] = lambda: FakeMongo()
    yield
    app.dependency_overrides.pop(get_mongo, None)