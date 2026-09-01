"""Pruebas de autorización por roles."""
import asyncio

import pytest
from fastapi import HTTPException

from app.utils.rbac import ensure_roles, require_role
from tests.conftest import FakeUser, make_role


def test_ensure_roles_permite_rol_autorizado():
    user = FakeUser(roles=[make_role("admin")])
    ensure_roles(user, ["admin", "auditor"])


def test_ensure_roles_rechaza_rol_no_autorizado():
    user = FakeUser(roles=[make_role("consulta")])
    with pytest.raises(HTTPException) as exc:
        ensure_roles(user, ["admin"])
    assert exc.value.status_code == 403


def test_ensure_roles_usuario_sin_roles():
    user = FakeUser(roles=[])
    with pytest.raises(HTTPException) as exc:
        ensure_roles(user, ["admin"])
    assert exc.value.status_code == 403


def test_ensure_roles_usuario_none():
    with pytest.raises(HTTPException):
        ensure_roles(None, ["admin"])


def test_require_role_decorador_async_ok():
    @require_role(["admin"])
    async def vista(current_user=None):
        return "ok"

    user = FakeUser(roles=[make_role("admin")])
    assert asyncio.run(vista(current_user=user)) == "ok"


def test_require_role_decorador_sync_rechaza():
    @require_role(["admin"])
    def vista(current_user=None):
        return "ok"

    user = FakeUser(roles=[make_role("consulta")])
    with pytest.raises(HTTPException) as exc:
        vista(current_user=user)
    assert exc.value.status_code == 403
