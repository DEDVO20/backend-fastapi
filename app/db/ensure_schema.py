"""
Parches de esquema necesarios para que el login no falle
si el código se desplegó antes de aplicar la migración de Alembic.
"""
from sqlalchemy import text
from sqlalchemy.orm import load_only

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

_otp_listo = False


def otp_disponible() -> bool:
    return _otp_listo


def asegurar_esquema_login() -> list[str]:
    """Crea las columnas OTP de usuarios si aún no existen.

    Siempre ejecuta ADD COLUMN IF NOT EXISTS (idempotente). Los usuarios
    actuales quedan con requiere_otp=false.
    """
    global _otp_listo
    if _otp_listo:
        return []

    aplicadas: list[str] = []
    for nombre, sql in COLUMNAS_OTP:
        try:
            with engine.begin() as conexion:
                conexion.execute(text(sql))
            aplicadas.append(nombre)
        except Exception as exc:
            print(f"⚠️ No se pudo asegurar columna usuarios.{nombre}: {exc}")
            return aplicadas

    _otp_listo = True
    return aplicadas


def opciones_carga_usuario(*extra):
    """Evita SELECT de columnas OTP si todavía no existen en PostgreSQL."""
    if _otp_listo:
        return extra

    from ..models.usuario import Usuario

    return (
        load_only(
            Usuario.id,
            Usuario.documento,
            Usuario.nombre,
            Usuario.segundo_nombre,
            Usuario.primer_apellido,
            Usuario.segundo_apellido,
            Usuario.correo_electronico,
            Usuario.nombre_usuario,
            Usuario.contrasena_hash,
            Usuario.area_id,
            Usuario.activo,
            Usuario.foto_url,
            Usuario.creado_por,
            Usuario.creado_en,
            Usuario.actualizado_en,
        ),
        *extra,
    )


def marcar_otp_seguro(usuario) -> None:
    """Rellena atributos OTP en memoria para no disparar un SELECT extra."""
    if usuario is None:
        return
    from sqlalchemy.orm.attributes import set_committed_value

    estado = usuario.__dict__
    if "requiere_otp" not in estado:
        set_committed_value(usuario, "requiere_otp", False)
    if "otp_codigo_hash" not in estado:
        set_committed_value(usuario, "otp_codigo_hash", None)
    if "otp_expira_en" not in estado:
        set_committed_value(usuario, "otp_expira_en", None)
    if "otp_intentos" not in estado:
        set_committed_value(usuario, "otp_intentos", 0)
    if "otp_enviado_en" not in estado:
        set_committed_value(usuario, "otp_enviado_en", None)
