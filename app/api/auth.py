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
from ..services.email import email_service
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
        joinedload(Usuario.roles)
        .joinedload(UsuarioRol.rol)
        .joinedload(Rol.permisos)
        .joinedload(RolPermiso.permiso)
    )


def _buscar_usuario_login(db: Session, identificador: str) -> Usuario | None:
    valor = (identificador or "").strip()
    if not valor:
        return None
    condiciones = [
        Usuario.nombre_usuario == valor,
        func.lower(Usuario.correo_electronico) == valor.lower(),
    ]
    if valor.isdigit():
        condiciones.append(Usuario.documento == int(valor))
    return _query_usuario_auth(db).filter(or_(*condiciones)).first()


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
    if not usuario or not usuario.activo or not getattr(usuario, "requiere_otp", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La verificación expiró. Vuelva a iniciar sesión.",
        )
    return usuario


def _emitir_y_enviar_otp(db: Session, usuario: Usuario) -> LoginResponse:
    if not es_correo_institucional(usuario.correo_electronico):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensaje_correo_institucional(),
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el código al correo institucional. Contacte al administrador.",
        )

    return LoginResponse(
        requiere_otp=True,
        token_type="bearer",
        otp_token=create_otp_token(str(usuario.id)),
        mensaje="Enviamos un código de verificación a su correo institucional.",
        correo_enmascarado=enmascarar_correo(usuario.correo_electronico),
    )


@router.get("/politica-acceso", response_model=PoliticaAccesoResponse)
def politica_acceso():
    """Dominios institucionales y tiempos de OTP (público, para el formulario)."""
    return PoliticaAccesoResponse(
        dominios_institucionales=dominios_institucionales(),
        otp_expira_minutos=settings.OTP_EXPIRE_MINUTES,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario.
    Cuentas actuales (admin y usuarios previos): JWT directo.
    Usuarios nuevos: contraseña + código OTP enviado al correo institucional.
    """
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

        if getattr(usuario, "requiere_otp", False):
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
