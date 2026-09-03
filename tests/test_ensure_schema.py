"""Pruebas del parche de columnas OTP al arrancar."""
from unittest.mock import MagicMock, patch

from app.db import ensure_schema
from app.db.ensure_schema import COLUMNAS_OTP, asegurar_esquema_login


def setup_function():
    ensure_schema._otp_listo = False


def test_columnas_otp_cubren_el_modelo_de_usuario():
    nombres = [nombre for nombre, _sql in COLUMNAS_OTP]
    assert nombres == [
        "requiere_otp",
        "otp_codigo_hash",
        "otp_expira_en",
        "otp_intentos",
        "otp_enviado_en",
    ]
    for _nombre, sql in COLUMNAS_OTP:
        assert "ADD COLUMN IF NOT EXISTS" in sql


@patch("app.db.ensure_schema.engine")
def test_asegurar_esquema_login_ejecuta_alter_si_faltan(mock_engine):
    conexion = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = conexion

    creadas = asegurar_esquema_login()
    assert creadas == [nombre for nombre, _sql in COLUMNAS_OTP]
    assert conexion.execute.call_count == len(COLUMNAS_OTP) + 1
    assert ensure_schema.otp_disponible() is True

    conexion.execute.reset_mock()
    assert asegurar_esquema_login() == []
    conexion.execute.assert_not_called()


@patch("app.db.ensure_schema.engine")
def test_asegurar_esquema_login_no_marca_listo_si_falla(mock_engine):
    mock_engine.begin.side_effect = Exception("no permission")
    creadas = asegurar_esquema_login()
    assert creadas == []
    assert ensure_schema.otp_disponible() is False
