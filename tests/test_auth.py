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
    assert data.get("requiere_otp") is False


def test_politica_acceso_es_publica(client):
    response = client.get("/api/v1/auth/politica-acceso")
    assert response.status_code == 200
    data = response.json()
    assert "gmail.com" in data["dominios_institucionales"]
    assert "outlook.com" in data["dominios_institucionales"]
    assert data["otp_expira_minutos"] >= 1


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


def test_login_usuario_nuevo_requiere_otp(client):
    from unittest.mock import patch

    hashed = get_password_hash("Password123")
    usuario = FakeUser(
        nombre_usuario="jperez",
        correo_electronico="jperez@iudc.edu.co",
        contrasena_hash=hashed,
        activo=True,
        requiere_otp=True,
        roles=[make_role("colaborador", ["documentos.ver"])],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        with patch("app.api.auth.generar_codigo_otp", return_value="123456"):
            response = client.post(
                "/api/v1/auth/login",
                json={"nombre_usuario": "jperez", "password": "Password123"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["requiere_otp"] is True
    assert data["otp_token"]
    assert not data.get("access_token")
    assert "iudc.edu.co" in (data.get("correo_enmascarado") or "")
    assert usuario.otp_codigo_hash


def test_verificar_otp_emite_jwt(client):
    from datetime import datetime, timedelta, timezone

    from app.utils.otp import hash_otp
    from app.utils.security import create_otp_token

    usuario_id = uuid4()
    usuario = FakeUser(
        id=usuario_id,
        nombre_usuario="jperez",
        correo_electronico="jperez@iudc.edu.co",
        contrasena_hash=get_password_hash("Password123"),
        activo=True,
        requiere_otp=True,
        otp_codigo_hash=hash_otp("123456", str(usuario_id)),
        otp_expira_en=datetime.now(timezone.utc) + timedelta(minutes=10),
        otp_intentos=0,
        roles=[make_role("colaborador", ["documentos.ver"])],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login/verificar-otp",
            json={
                "otp_token": create_otp_token(str(usuario_id)),
                "codigo": "123456",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["usuario"]["nombre_usuario"] == "jperez"
    assert usuario.otp_codigo_hash is None


def test_verificar_otp_incorrecto(client):
    from datetime import datetime, timedelta, timezone

    from app.utils.otp import hash_otp
    from app.utils.security import create_otp_token

    usuario_id = uuid4()
    usuario = FakeUser(
        id=usuario_id,
        nombre_usuario="jperez",
        correo_electronico="jperez@iudc.edu.co",
        contrasena_hash=get_password_hash("Password123"),
        activo=True,
        requiere_otp=True,
        otp_codigo_hash=hash_otp("123456", str(usuario_id)),
        otp_expira_en=datetime.now(timezone.utc) + timedelta(minutes=10),
        otp_intentos=0,
        roles=[],
    )
    db = _db_con_usuario(usuario)

    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        response = client.post(
            "/api/v1/auth/login/verificar-otp",
            json={
                "otp_token": create_otp_token(str(usuario_id)),
                "codigo": "000000",
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 400
    assert "incorrecto" in response.json()["detail"].lower()
    assert response.json().get("access_token") is None

