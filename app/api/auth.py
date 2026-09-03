"""
Endpoints de autenticación
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..database import get_db
from ..db.ensure_schema import marcar_otp_seguro, opciones_carga_usuario
from ..models.usuario import Rol, RolPermiso, Usuario, UsuarioRol
from ..schemas.auth import (
    LoginRequest,
    LoginResponse,
    PoliticaAccesoResponse,
    ReenviarOtpRequest,
    TokenResponse,
    VerificarOtpRequest,
)
from ..schemas.usuario import UsuarioWithArea
from ..services.email import MENSAJE_SMTP_BLOQUEADO, email_service, es_error_red_smtp
from ..utils.correo_institucional import (
    dominios_institucionales,
    es_correo_institucional,
    mensaje_correo_institucional,
)
from ..utils.otp import (
    enmascarar_correo,
    generar_codigo_otp,
    hash_otp,
    otp_esta_expirado,
    otp_expira_en,
    verificar_otp,
)
from ..utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_otp_token,
    decode_token_payload,
    verify_password,
)
from ..api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["autenticacion"])


def _query_usuario_auth(db: Session):
    return db.query(Usuario).options(
        *opciones_carga_usuario(
            joinedload(Usuario.roles)
            .joinedload(UsuarioRol.rol)
            .joinedload(Rol.permisos)
            .joinedload(RolPermiso.permiso)
        )
    )


def _requiere_otp(usuario: Usuario) -> bool:
    if usuario is None:
        return False
    if "requiere_otp" not in usuario.__dict__:
        marcar_otp_seguro(usuario)
    return bool(usuario.__dict__.get("requiere_otp"))


def _es_administrador(usuario: Usuario) -> bool:
    if not usuario:
        return False
    if "sistema.admin" in set(_permisos_de(usuario)):
        return True
    for ur in usuario.roles or []:
        rol = getattr(ur, "rol", None)
        if not rol:
            continue
        clave = str(getattr(rol, "clave", "") or "").strip().lower()
        nombre = str(getattr(rol, "nombre", "") or "").strip().lower()
        if clave in {"admin", "administrador"} or nombre in {"admin", "administrador"}:
            return True
    return False


def _debe_pedir_otp(usuario: Usuario, ingreso_por_correo: bool) -> bool:
    if ingreso_por_correo and es_correo_institucional(usuario.correo_electronico):
        return True
    return bool(_requiere_otp(usuario))


def _buscar_usuario_login(db: Session, identificador: str) -> Usuario | None:
    valor = (identificador or "").strip()
    if not valor:
        return None

    correo = valor.lower()
    consulta = db.query(Usuario).options(*opciones_carga_usuario())
    if "@" in valor:
        encontrado = consulta.filter(
            func.lower(func.trim(Usuario.correo_electronico)) == correo
        ).first()
    else:
        condiciones = [Usuario.nombre_usuario == valor]
        if valor.isdigit():
            condiciones.append(Usuario.documento == int(valor))
        encontrado = consulta.filter(or_(*condiciones)).first()

    if not encontrado:
        return None
    marcar_otp_seguro(encontrado)
    usuario = _usuario_por_id(db, encontrado.id)
    if usuario:
        marcar_otp_seguro(usuario)
    return usuario


def _usuario_por_id(db: Session, usuario_id: UUID) -> Usuario | None:
    return _query_usuario_auth(db).filter(Usuario.id == usuario_id).first()


def _permisos_de(usuario: Usuario) -> list[str]:
    permisos_set = set()
    for ur in usuario.roles or []:
        rol = getattr(ur, "rol", None)
        if not rol:
            continue
        for rp in rol.permisos or []:
            if rp.permiso:
                permisos_set.add(rp.permiso.codigo)
    return list(permisos_set)


def _datos_usuario(usuario: Usuario) -> dict:
    return {
        "id": str(usuario.id),
        "nombre_usuario": usuario.nombre_usuario,
        "email": usuario.correo_electronico,
        "nombre_completo": f"{usuario.nombre} {usuario.primer_apellido}",
        "activo": usuario.activo,
        "foto_url": usuario.foto_url,
        "permisos": _permisos_de(usuario),
    }


def _respuesta_sesion(usuario: Usuario) -> TokenResponse:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(usuario.id)},
        expires_delta=access_token_expires,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario=_datos_usuario(usuario),
        requiere_otp=False,
    )


def _limpiar_otp(usuario: Usuario) -> None:
    usuario.otp_codigo_hash = None
    usuario.otp_expira_en = None
    usuario.otp_intentos = 0
    usuario.otp_enviado_en = None


def _usuario_desde_otp_token(db: Session, otp_token: str) -> Usuario:
    payload = decode_token_payload(otp_token)
    if not payload or payload.get("purpose") != "otp" or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación expiró. Vuelva a iniciar sesión.",
        )
    try:
        usuario_id = UUID(str(payload["sub"]))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación expiró. Vuelva a iniciar sesión.",
        )
    usuario = _usuario_por_id(db, usuario_id)
    if not usuario or not usuario.activo or not _requiere_otp(usuario):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación expiró. Vuelva a iniciar sesión.",
        )
    return usuario


def _otp_reciente_vigente(usuario: Usuario) -> bool:
    if not getattr(usuario, "otp_codigo_hash", None):
        return False
    if otp_esta_expirado(getattr(usuario, "otp_expira_en", None)):
        return False
    enviado_en = getattr(usuario, "otp_enviado_en", None)
    if enviado_en is None:
        return False
    if enviado_en.tzinfo is None:
        enviado_en = enviado_en.replace(tzinfo=timezone.utc)
    espera = timedelta(seconds=settings.OTP_REENVIO_SEGUNDOS)
    return datetime.now(timezone.utc) < (enviado_en + espera)


def _respuesta_desafio_otp(usuario: Usuario, mensaje: str) -> LoginResponse:
    return LoginResponse(
        requiere_otp=True,
        token_type="bearer",
        otp_token=create_otp_token(str(usuario.id)),
        mensaje=mensaje,
        correo_enmascarado=enmascarar_correo(usuario.correo_electronico),
    )


def _emitir_y_enviar_otp(db: Session, usuario: Usuario) -> LoginResponse:
    if not es_correo_institucional(usuario.correo_electronico):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensaje_correo_institucional(),
        )

    if _otp_reciente_vigente(usuario):
        return _respuesta_desafio_otp(
            usuario,
            "Ya enviamos un código a su correo. Revise la bandeja de entrada o spam.",
        )

    codigo = generar_codigo_otp()
    usuario.otp_codigo_hash = hash_otp(codigo, str(usuario.id))
    usuario.otp_expira_en = otp_expira_en()
    usuario.otp_intentos = 0
    usuario.otp_enviado_en = datetime.now(timezone.utc)
    db.add(usuario)
    db.commit()

    enviado = email_service.enviar_codigo_otp(
        usuario.correo_electronico,
        usuario.nombre,
        codigo,
    )
    if not enviado:
        detalle = (email_service.ultimo_error or "").strip()
        if (
            not email_service.envio_configurado()
            or es_error_red_smtp(Exception(detalle))
            or "network is unreachable" in detalle.lower()
            or "resend.com" in detalle.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=MENSAJE_SMTP_BLOQUEADO,
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No se pudo enviar el código al correo. "
                f"{detalle or 'Revise spam o la configuración de correo.'}"
            ),
        )

    return _respuesta_desafio_otp(
        usuario,
        "Enviamos un código de verificación a su correo institucional.",
    )


@router.get("/politica-acceso", response_model=PoliticaAccesoResponse)
def politica_acceso():
    """Dominios institucionales y tiempos de OTP (público, para el formulario)."""
    return PoliticaAccesoResponse(
        dominios_institucionales=dominios_institucionales(),
        otp_expira_minutos=settings.OTP_EXPIRE_MINUTES,
        smtp_configurado=email_service.smtp_configurado(),
    )


def _es_error_columna_otp(error: Exception) -> bool:
    texto = str(error).lower()
    return "requiere_otp" in texto or "otp_codigo_hash" in texto or (
        "undefinedcolumn" in texto.replace(" ", "") and "usuarios" in texto
    )


def _reparar_columnas_otp(db: Session) -> None:
    from ..db.ensure_schema import asegurar_esquema_login

    db.rollback()
    asegurar_esquema_login()


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario.
    El administrador y cuentas previas pueden entrar con usuario o documento.
    Los usuarios nuevos deben entrar con su correo y un código OTP.
    """
    return _login(login_data, db, reintentar_esquema=True)


def _login(login_data: LoginRequest, db: Session, reintentar_esquema: bool):
    try:
        usuario = _buscar_usuario_login(db, login_data.nombre_usuario)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(login_data.password, usuario.contrasena_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )

        identificador = (login_data.nombre_usuario or "").strip()
        ingreso_por_correo = "@" in identificador
        if not _es_administrador(usuario) and not ingreso_por_correo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe ingresar con su correo electrónico. Solo el administrador puede usar el usuario.",
            )

        if _debe_pedir_otp(usuario, ingreso_por_correo):
            return _emitir_y_enviar_otp(db, usuario)

        sesion = _respuesta_sesion(usuario)
        return LoginResponse(
            requiere_otp=False,
            access_token=sesion.access_token,
            token_type=sesion.token_type,
            usuario=sesion.usuario,
        )
    except HTTPException:
        raise
    except Exception as e:
        if reintentar_esquema and _es_error_columna_otp(e):
            try:
                _reparar_columnas_otp(db)
                return _login(login_data, db, reintentar_esquema=False)
            except Exception:
                pass
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno en login: {str(e)}"
        )


@router.post("/login/verificar-otp", response_model=TokenResponse)
def verificar_otp_login(
    datos: VerificarOtpRequest,
    db: Session = Depends(get_db),
):
    usuario = _usuario_desde_otp_token(db, datos.otp_token)

    if otp_esta_expirado(getattr(usuario, "otp_expira_en", None)):
        _limpiar_otp(usuario)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código expiró. Vuelva a iniciar sesión.",
        )

    if verificar_otp(datos.codigo, str(usuario.id), getattr(usuario, "otp_codigo_hash", None)):
        _limpiar_otp(usuario)
        db.commit()
        return _respuesta_sesion(usuario)

    intentos = int(getattr(usuario, "otp_intentos", 0) or 0) + 1
    usuario.otp_intentos = intentos
    if intentos >= settings.OTP_MAX_INTENTOS:
        _limpiar_otp(usuario)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demasiados intentos. Vuelva a iniciar sesión.",
        )
    db.commit()
    restantes = settings.OTP_MAX_INTENTOS - intentos
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Código incorrecto. Le quedan {restantes} intento(s).",
    )


@router.post("/login/reenviar-otp", response_model=LoginResponse)
def reenviar_otp_login(
    datos: ReenviarOtpRequest,
    db: Session = Depends(get_db),
):
    usuario = _usuario_desde_otp_token(db, datos.otp_token)
    enviado_en = getattr(usuario, "otp_enviado_en", None)
    if enviado_en is not None:
        if enviado_en.tzinfo is None:
            enviado_en = enviado_en.replace(tzinfo=timezone.utc)
        espera = timedelta(seconds=settings.OTP_REENVIO_SEGUNDOS)
        restante = (enviado_en + espera) - datetime.now(timezone.utc)
        if restante.total_seconds() > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Espere {int(restante.total_seconds())} segundos para reenviar el código.",
            )
    return _emitir_y_enviar_otp(db, usuario)


@router.get("/me", response_model=UsuarioWithArea)
def get_me(current_user: Usuario = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado actual
    """
    user_data = UsuarioWithArea.model_validate(current_user)
    user_data.permisos = current_user.permisos_codes
    return user_data


@router.post("/logout")
def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Cerrar sesión (en JWT stateless esto es principalmente para el cliente)
    El cliente debe eliminar el token del localStorage
    """
    return {
        "message": "Sesión cerrada exitosamente",
        "usuario": current_user.nombre_usuario
    }
