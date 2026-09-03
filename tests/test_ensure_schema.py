"""Pruebas del parche de columnas OTP al arrancar."""
from unittest.mock import MagicMock, patch

from app.db.ensure_schema import COLUMNAS_OTP, asegurar_esquema_login


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


@patch("app.db.ensure_schema.inspect")
@patch("app.db.ensure_schema.engine")
def test_asegurar_esquema_login_no_hace_nada_si_ya_existen(mock_engine, mock_inspect):
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["usuarios"]
    inspector.get_columns.return_value = [
        {"name": nombre} for nombre, _sql in COLUMNAS_OTP
    ] + [{"name": "id"}]
    mock_inspect.return_value = inspector

    assert asegurar_esquema_login() == []
    mock_engine.begin.assert_not_called()


@patch("app.db.ensure_schema.inspect")
@patch("app.db.ensure_schema.engine")
def test_asegurar_esquema_login_agrega_columnas_faltantes(mock_engine, mock_inspect):
    inspector = MagicMock()
    inspector.get_table_names.return_value = ["usuarios"]
    inspector.get_columns.return_value = [{"name": "id"}, {"name": "nombre_usuario"}]
    mock_inspect.return_value = inspector

    conexion = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = conexion

    creadas = asegurar_esquema_login()
    assert creadas == [nombre for nombre, _sql in COLUMNAS_OTP]
    assert conexion.execute.call_count == len(COLUMNAS_OTP)
