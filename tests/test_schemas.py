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


def test_usuario_create_email_invalido():
    with pytest.raises(ValidationError):
        UsuarioCreate(
            documento=111,
            nombre="Ana",
            primer_apellido="Perez",
            correo_electronico="no-es-email",
            nombre_usuario="ana",
            contrasena="segura123",
        )
