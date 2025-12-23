import pytest
from app.auth.passwords import validate_password

def test_validate_password_ok():
    validate_password("Test12345")  # не падает

def test_validate_password_too_short():
    with pytest.raises(ValueError):
        validate_password("abc")

def test_validate_password_common():
    with pytest.raises(ValueError):
        validate_password("password")

def test_validate_password_no_digits():
    with pytest.raises(ValueError):
        validate_password("Password")

def test_validate_password_no_letters():
    with pytest.raises(ValueError):
        validate_password("12345678")