import pytest
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password_round_trip():
    hashed = hash_password("strongpass")

    assert verify_password("strongpass", hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token("user@example.com")
    payload = decode_token(token)

    assert payload["sub"] == "user@example.com"
    assert "exp" in payload


def test_decode_token_with_wrong_secret_raises():
    token = create_access_token("user@example.com")

    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret-key", algorithms=[get_settings().algorithm])
