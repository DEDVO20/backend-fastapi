"""Pruebas de autenticación: login, me y logout."""
from unittest.mock import MagicMock
from uuid import uuid4

from app.database import get_db
from app.main import app
from app.utils.security import get_password_hash
from tests.conftest import FakeUser, make_role


def _db_con_usuario(usuario):
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = usuario
    return db


def test_login_exitoso(client):
    hashed = get_password_hash("admin123")
    usuario = FakeUser(
        id=uuid4(),
        nombre_usuario="admin",
        contrasena_hash=hashed,
        activo=True,
        roles=[make_role("admin", ["sistema.admin"])],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"nombre_usuario": "admin", "password": "admin123"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["usuario"]["nombre_usuario"] == "admin"
    assert "sistema.admin" in data["usuario"]["permisos"]


def test_login_usuario_inexistente(client):
    db = _db_con_usuario(None)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"nombre_usuario": "noexiste", "password": "admin123"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]


def test_login_password_incorrecta(client):
    usuario = FakeUser(
        nombre_usuario="admin",
        contrasena_hash=get_password_hash("admin123"),
        activo=True,
        roles=[],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"nombre_usuario": "admin", "password": "wrongpass"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401


def test_login_usuario_inactivo(client):
    usuario = FakeUser(
        nombre_usuario="admin",
        contrasena_hash=get_password_hash("admin123"),
        activo=False,
        roles=[],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"nombre_usuario": "admin", "password": "admin123"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 403
    assert "inactivo" in response.json()["detail"].lower()


def test_me_sin_token(client):
    response = client.get("api/v1/auth/me")
    assert response.status_code in (401, 403)


def test_me_con_token_invalido(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code in (401, 403, 500)


def test_logout_requiere_autenticacion(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code in (401, 403)
