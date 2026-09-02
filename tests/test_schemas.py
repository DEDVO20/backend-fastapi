"""Pruebas de validación de schemas Pydantic."""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.schemas.riesgo import RiesgoCreate
from app.schemas.usuario import UsuarioCreate


def test_login_request_valido():
    data = LoginRequest(nombre_usuario="admin", password="admin123")
    assert data.nombre_usuario == "admin"


def test_login_request_password_corta():
    with pytest.raises(ValidationError):
        LoginRequest(nombre_usuario="admin", password="123")


def test_riesgo_create_valido():
    riesgo = RiesgoCreate(
        proceso_id=uuid4(),
        codigo="RSK-001",
        descripcion="Falla de proceso",
        tipo_riesgo="operativo",
        probabilidad=3,
        impacto=4,
    )
    assert riesgo.estado == "activo"
    assert riesgo.probabilidad == 3


def test_riesgo_probabilidad_fuera_de_rango():
    with pytest.raises(ValidationError):
        RiesgoCreate(
            proceso_id=uuid4(),
            codigo="RSK-002",
            descripcion="Inválido",
            tipo_riesgo="operativo",
            probabilidad=9,
            impacto=2,
        )


def test_usuario_create_requiere_contrasena_minima():
    with pytest.raises(ValidationError):
        UsuarioCreate(
            documento=111,
            nombre="Ana",
            primer_apellido="Perez",
            correo_electronico="ana@example.com",
            nombre_usuario="ana",
            contrasena="123",
        )


def test_usuario_update_acepta_roles_parciales():
    from uuid import uuid4
    from app.schemas.usuario import UsuarioUpdate

    data = UsuarioUpdate(activo=False, rol_ids=[uuid4()])
    assert data.activo is False
    assert data.rol_ids is not None
    assert len(data.rol_ids) == 1


def test_usuario_rol_response_usa_rol_id():
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.schemas.usuario import UsuarioRolResponse

    usuario_id = uuid4()
    rol_id = uuid4()
    asignacion_id = uuid4()
    parsed = UsuarioRolResponse(
        id=asignacion_id,
        usuario_id=usuario_id,
        rol_id=rol_id,
        creado_en=datetime.now(timezone.utc),
        rol={"id": rol_id, "nombre": "Admin", "clave": "admin"},
    )
    assert parsed.rol_id == rol_id
    assert parsed.id == asignacion_id
    assert parsed.rol is not None
    assert parsed.rol.clave == "admin"
