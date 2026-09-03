"""
Parches de esquema necesarios para que el login no falle
si el código se desplegó antes de aplicar la migración de Alembic.
"""
from sqlalchemy import inspect, text

from ..database import engine

COLUMNAS_OTP = (
    (
        "requiere_otp",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS requiere_otp "
        "BOOLEAN NOT NULL DEFAULT false",
    ),
    (
        "otp_codigo_hash",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS otp_codigo_hash VARCHAR(128)",
    ),
    (
        "otp_expira_en",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS otp_expira_en TIMESTAMPTZ",
    ),
    (
        "otp_intentos",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS otp_intentos "
        "INTEGER NOT NULL DEFAULT 0",
    ),
    (
        "otp_enviado_en",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS otp_enviado_en TIMESTAMPTZ",
    ),
)


def asegurar_esquema_login() -> list[str]:
    """Crea las columnas OTP de usuarios si aún no existen.

    Los usuarios actuales quedan con requiere_otp=false, así que el admin
    y las cuentas previas siguen entrando con usuario y contraseña.
    """
    inspector = inspect(engine)
    if "usuarios" not in inspector.get_table_names():
        return []

    columnas = {col["name"] for col in inspector.get_columns("usuarios")}
    faltantes = [nombre for nombre, _sql in COLUMNAS_OTP if nombre not in columnas]
    if not faltantes:
        return []

    sql_por_columna = dict(COLUMNAS_OTP)
    with engine.begin() as conexion:
        for nombre in faltantes:
            conexion.execute(text(sql_por_columna[nombre]))
    return faltantes
