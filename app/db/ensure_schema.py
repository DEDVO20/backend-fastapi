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
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    """
                    UPDATE usuarios
                    SET requiere_otp = true
                    WHERE requiere_otp = false
                      AND id NOT IN (
                        SELECT ur.usuario_id
                        FROM usuario_roles ur
                        JOIN roles r ON r.id = ur.rol_id
                        WHERE lower(coalesce(r.clave, '')) IN ('admin', 'administrador')
                           OR lower(coalesce(r.nombre, '')) IN ('admin', 'administrador')
                      )
                    """
                )
            )
    except Exception as exc:
        print(f"⚠️ No se pudo activar OTP en usuarios existentes: {exc}")
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
    if usuario is None or _otp_listo:
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


SQL_CALIDAD = (
    (
        "indicadores.tipo_indicador",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS tipo_indicador VARCHAR(50) NOT NULL DEFAULT 'eficacia'",
    ),
    (
        "indicadores.estado",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS estado VARCHAR(50) NOT NULL DEFAULT 'borrador'",
    ),
    (
        "indicadores.revisado_por",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS revisado_por UUID",
    ),
    (
        "indicadores.fecha_revision",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS fecha_revision TIMESTAMPTZ",
    ),
    (
        "indicadores.aprobado_por",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS aprobado_por UUID",
    ),
    (
        "indicadores.fecha_aprobacion",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS fecha_aprobacion TIMESTAMPTZ",
    ),
    (
        "indicadores.observacion_aprobacion",
        "ALTER TABLE indicadores ADD COLUMN IF NOT EXISTS observacion_aprobacion TEXT",
    ),
    (
        "mediciones_indicador",
        """
        CREATE TABLE IF NOT EXISTS mediciones_indicador (
            id UUID PRIMARY KEY,
            indicador_id UUID NOT NULL REFERENCES indicadores(id) ON UPDATE CASCADE ON DELETE CASCADE,
            periodo VARCHAR(20) NOT NULL,
            valor NUMERIC(10, 2) NOT NULL,
            meta NUMERIC(10, 2),
            cumple_meta BOOLEAN,
            observaciones TEXT,
            registrado_por UUID REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            creado_por UUID REFERENCES usuarios(id) ON UPDATE CASCADE ON DELETE SET NULL
        )
        """,
    ),
    (
        "mediciones_indicador.activo",
        "ALTER TABLE mediciones_indicador ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
    ),
    (
        "mediciones_indicador.creado_por",
        "ALTER TABLE mediciones_indicador ADD COLUMN IF NOT EXISTS creado_por UUID",
    ),
    (
        "mediciones_indicador.registrado_por",
        "ALTER TABLE mediciones_indicador ADD COLUMN IF NOT EXISTS registrado_por UUID",
    ),
    (
        "mediciones_indicador.creado_en",
        "ALTER TABLE mediciones_indicador ADD COLUMN IF NOT EXISTS creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ),
    (
        "mediciones_indicador.actualizado_en",
        "ALTER TABLE mediciones_indicador ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ),
)

_calidad_listo = False


def asegurar_esquema_calidad() -> list[str]:
    """Crea columnas/tablas de indicadores si el deploy llegó antes que Alembic."""
    global _calidad_listo
    if _calidad_listo:
        return []

    aplicadas: list[str] = []
    for nombre, sql in SQL_CALIDAD:
        try:
            with engine.begin() as conexion:
                conexion.execute(text(sql))
            aplicadas.append(nombre)
        except Exception as exc:
            print(f"⚠️ No se pudo asegurar {nombre}: {exc}")
            return aplicadas

    _calidad_listo = True
    return aplicadas
