"""Fixtures compartidas para las pruebas del backend."""
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-pytest-calidad")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")

from app.database import get_db
from app.main import app
from app.api.dependencies import get_current_user


class FakeUser:
    """Usuario en memoria para pruebas de auth y RBAC."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid4())
        self.nombre_usuario = kwargs.get("nombre_usuario", "tester")
        self.nombre = kwargs.get("nombre", "Test")
        self.segundo_nombre = kwargs.get("segundo_nombre")
        self.primer_apellido = kwargs.get("primer_apellido", "User")
        self.segundo_apellido = kwargs.get("segundo_apellido")
        self.correo_electronico = kwargs.get("correo_electronico", "test@example.com")
        self.activo = kwargs.get("activo", True)
        self.foto_url = kwargs.get("foto_url")
        self.documento = kwargs.get("documento", 123456)
        self.area_id = kwargs.get("area_id")
        self.area = kwargs.get("area")
        self.roles = kwargs.get("roles", [])
        self.contrasena_hash = kwargs.get("contrasena_hash", "hash")
        self._permisos = kwargs.get("permisos_codes", [])

    @property
    def permisos_codes(self):
        return self._permisos

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.primer_apellido}"


def make_role(clave: str, permisos: list[str] | None = None):
    """Construye un rol mínimo con permisos anidados como en SQLAlchemy."""
    permiso_objs = []
    for codigo in permisos or []:
        permiso_objs.append(
            SimpleNamespace(permiso=SimpleNamespace(codigo=codigo))
        )
    rol = SimpleNamespace(clave=clave, permisos=permiso_objs)
    return SimpleNamespace(rol=rol)


def _fake_db():
    db = SimpleNamespace()
    db.execute = lambda *args, **kwargs: None
    yield db


@pytest.fixture
def admin_user():
    return FakeUser(
        nombre_usuario="admin",
        permisos_codes=["sistema.admin"],
        roles=[make_role("admin", ["sistema.admin"])],
    )


@pytest.fixture
def usuario_sin_permisos():
    return FakeUser(
        nombre_usuario="consulta",
        permisos_codes=["documentos.ver"],
        roles=[make_role("consulta", ["documentos.ver"])],
    )


@pytest.fixture
def client():
    """Cliente HTTP contra la app, sin tocar la base real."""
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = _fake_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_admin(admin_user):
    """Cliente autenticado como administrador."""
    app.dependency_overrides.clear()

    async def _current_user():
        return admin_user

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_sin_permisos(usuario_sin_permisos):
    """Cliente autenticado sin permisos de administración."""
    app.dependency_overrides.clear()

    async def _current_user():
        return usuario_sin_permisos

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
