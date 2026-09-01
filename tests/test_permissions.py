"""Pruebas de aliases y chequeo de permisos."""
from app.api.dependencies import (
    _expand_permission_codes,
    user_has_any_permission,
)
from tests.conftest import FakeUser


def test_expand_permission_incluye_aliases():
    expanded = _expand_permission_codes(["usuarios.gestion"])
    assert "usuarios.gestion" in expanded
    assert "usuarios.crear" in expanded
    assert "usuarios.editar" in expanded


def test_expand_permission_incluye_procesos_ver_para_admin_de_procesos():
    expanded = _expand_permission_codes(["procesos.ver"])
    assert "procesos.ver" in expanded
    assert "procesos.admin" in expanded


def test_expand_permission_sin_alias_queda_igual():
    expanded = _expand_permission_codes(["documentos.ver"])
    assert expanded == {"documentos.ver"}


def test_admin_tiene_cualquier_permiso():
    user = FakeUser(permisos_codes=["sistema.admin"])
    assert user_has_any_permission(user, ["riesgos.gestion"]) is True


def test_usuario_con_permiso_directo():
    user = FakeUser(permisos_codes=["riesgos.ver"])
    assert user_has_any_permission(user, ["riesgos.ver", "riesgos.gestion"]) is True


def test_usuario_con_alias_de_permiso():
    user = FakeUser(permisos_codes=["usuarios.crear"])
    assert user_has_any_permission(user, ["usuarios.gestion"]) is True


def test_usuario_sin_permiso():
    user = FakeUser(permisos_codes=["documentos.ver"])
    assert user_has_any_permission(user, ["sistema.config"]) is False


def test_usuario_sin_permisos_codes():
    user = FakeUser(permisos_codes=[])
    assert user_has_any_permission(user, ["usuarios.ver"]) is False
