import uuid
from app.auth.jwt import create_access_token, decode_token

def test_jwt_roundtrip():
    user_id = uuid.uuid4()

    token = create_access_token(user_id)
    data = decode_token(token)

    assert data["sub"] == str(user_id)
    assert data["type"] == "access"