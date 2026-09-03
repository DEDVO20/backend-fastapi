"""Pruebas de hashing de contraseñas y JWT."""
from datetime import timedelta

from jose import jwt

from app.config import settings
from app.utils.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_hash_y_verificacion_de_contrasena():
    hashed = get_password_hash("admin123")
    assert hashed != "admin123"
    assert verify_password("admin123", hashed) is True
    assert verify_password("otra-clave", hashed) is False


def test_create_access_token_incluye_sub_y_exp():
    token = create_access_token({"sub": "user-1"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user-1"
    assert "exp" in payload


def test_decode_access_token_valido():
    token = create_access_token({"sub": "42"})
    assert decode_access_token(token) == "42"


def test_decode_access_token_invalido_devuelve_none():
    assert decode_access_token("token-basura") is None


def test_decode_access_token_sin_sub_devuelve_none():
    token = jwt.encode({"foo": "bar"}, settings.SECRET_KEY, algorithm=ALGORITHM)
    assert decode_access_token(token) is None


def test_decode_access_token_expirado_devuelve_none():
    token = create_access_token({"sub": "42"}, expires_delta=timedelta(seconds=-10))
    assert decode_access_token(token) is None


def test_decode_access_token_rechaza_token_otp():
    from app.utils.security import create_otp_token

    token = create_otp_token("42")
    assert decode_access_token(token) is None
