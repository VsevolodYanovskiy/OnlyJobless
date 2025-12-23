from app.auth.security import hash_password, verify_password

def test_hash_and_verify_password():
    pwd = "Test12345"
    hashed = hash_password(pwd)

    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)